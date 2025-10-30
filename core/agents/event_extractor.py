import json
import yaml
import re
from typing import Dict, List, Any
from loguru import logger
from core.agents.base_agent import BaseAgent


class EventExtractionAgent(BaseAgent):
    def __init__(self):
        system_prompt = """你是国家发改委级智库级的新闻信息分析师。核心使命：穿透新闻表象识别真实意图，正确对新闻事件标注与分级，为投资决策提供信息支撑。"""
        # """你是一个国家级的经济与金融类新闻信息分析师。你的任务是从新闻中取对投资决策提有影响的事件，并进行分级。
        # 标注涉及：宏观经济指标/政策变动/行业颠覆事件/国际关联事件/企业或公司动态/市场异动与交易事件/社会与民生事件/科技与创新进展/法律与诉讼/监管行动与合规事件/地理与区域事件/人事变动（非公司层面）/舆情事件等等。
        #                             按照形象有影响的事件，并进行分级。"""

        super().__init__("EventExtractionAgent", system_prompt)
        self.required_output_fields = ["core_events", "impact_level", "time_horizon", "affected_assets"]

        # 加载配置
        try:
            with open('config/impact_criteria.yaml', 'r') as f:
                self.impact_criteria = yaml.safe_load(f)
        except:
            self.impact_criteria = self._get_default_criteria()

    def process(self, input_data: Any) -> Dict[str, Any]:
        """处理输入数据 - 支持单条和批量处理"""
        if isinstance(input_data, list):
            # 批量处理
            if len(input_data) > 1:
                return self._process_batch(input_data)
            else:
                return self._process_single(input_data[0] if input_data else {})
        else:
            return self._process_single(input_data)

    def _process_batch(self, news_items: List[Dict]) -> Dict[str, Any]:
        """批量处理新闻"""
        extracted_events = []

        logger.info(f"批量处理 {len(news_items)} 条新闻")

        # 这里主系统会处理批量逻辑，这里保持单条处理兼容性
        for news in news_items:
            event = self.extract_single_event(news)
            if event and event["impact_level"] != "low":
                extracted_events.append(event)

        return {
            "extracted_events": extracted_events,
            "summary": f"共提取 {len(extracted_events)} 个重要事件",
            "total_processed": len(news_items)
        }

    def _process_single(self, news: Dict) -> Dict[str, Any]:
        """处理单条新闻"""
        event = self.extract_single_event(news)
        events_list = [event] if event else []

        return {
            "extracted_events": events_list,
            "summary": f"提取 {len(events_list)} 个事件",
            "total_processed": 1
        }

    def extract_single_event(self, news: Dict) -> Dict[str, Any]:
        """提取单个新闻事件 - 保持原有逻辑"""
        prompt = f"""
请分析以下新闻内容，提取投资相关事件：

标题：{news.get('title', '')}
内容：{news.get('content', '')[:1000]}
来源：{news.get('source', '未知')}
时间：{news.get('timestamp', '未知')}

请按以下JSON格式输出：
{{
    "core_event": "用一句话总结核心事件",
    "impact_level": "high/medium/low",
    "time_horizon": "short/mid/long",
    "affected_assets": ["相关的股票、债券、商品或货币"],
    "investment_implication": "简要说明对投资的影响",
    "confidence": 0.0-1.0
}}

注意：只返回JSON格式，不要其他内容。
"""

        response = self.llm_call(prompt, use_cache=True)

        try:
            event_data = self._parse_single_response(response)
            return event_data
        except Exception as e:
            logger.error(f"事件提取失败: {e}")
            return self._create_default_event(news)

    def _parse_single_response(self, response: str) -> Dict[str, Any]:
        """解析单条响应"""
        cleaned_response = self._clean_llm_response(response)
        event_data = json.loads(cleaned_response)

        # 验证必需字段
        if not all(field in event_data for field in self.required_output_fields):
            raise ValueError("事件数据缺少必需字段")

        return event_data

    def _clean_llm_response(self, response: str) -> str:
        """清理LLM响应"""
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()

        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end != 0:
            return response[start:end]

        return response

    def _create_default_event(self, news: Dict) -> Dict[str, Any]:
        """创建默认事件结构"""
        title = news.get('title', '')
        content = news.get('content', '')

        # 简单的基于关键词的影响判断
        impact_level = "medium"
        high_impact_words = ["利率", "降息", "加息", "通胀", "衰退", "危机", "刺激", "财报", "盈利"]
        low_impact_words = ["观点", "评论", "分析", "预计", "可能"]

        combined_text = (title + content).lower()

        if any(word in combined_text for word in high_impact_words):
            impact_level = "high"
        elif any(word in combined_text for word in low_impact_words):
            impact_level = "low"

        return {
            "core_event": title if title else content[:100],
            "impact_level": impact_level,
            "time_horizon": "short",
            "affected_assets": [],
            "investment_implication": "自动分析结果",
            "confidence": 0.5
        }

    def _get_default_criteria(self):
        """获取默认的影响标准"""
        return {
            "impact_levels": {
                "high": {"keywords": ["利率决策", "财政刺激", "贸易战", "金融危机", "重大政策", "经济衰退"],
                         "priority": 1},

                "medium": {"keywords": ["经济数据", "行业监管", "公司财报", "并购", "央行讲话"],
                           "priority": 2},

                "low": {"keywords": ["常规数据", "分析师观点", "日常新闻"],
                        "priority": 3}
            }
        }