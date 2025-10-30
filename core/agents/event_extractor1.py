import json
import yaml
import re
from core.agents.base_agent import BaseAgent
from typing import Dict, List, Any
from loguru import logger

class EventExtractionAgent(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个专业的金融信息分析师。你的任务是从新闻中提取对投资决策有影响的事件，并进行分级。

        请专注于识别：
        1. 可能影响资产价格的事件
        2. 政策变化和经济数据发布
        3. 行业重大发展和公司事件
        4. 市场情绪和资金流向变化

        输出必须是严格的JSON格式。"""

        super().__init__("EventExtractionAgent", system_prompt)
        self.required_output_fields = ["core_events", "impact_level", "time_horizon", "affected_assets"]

        # 加载配置
        try:
            with open('config/impact_criteria.yaml', 'r') as f:
                self.impact_criteria = yaml.safe_load(f)
        except:
            self.impact_criteria = self._get_default_criteria()

    def _get_default_criteria(self):
        """获取默认的影响标准"""
        return {
            "impact_levels": {
                "high": {"keywords": ["利率决策", "财政刺激", "贸易战", "金融危机", "重大政策", "经济衰退"],
                         "priority": 1},
                "medium": {"keywords": ["经济数据", "行业监管", "公司财报", "并购", "央行讲话"], "priority": 2},
                "low": {"keywords": ["常规数据", "分析师观点", "日常新闻"], "priority": 3}
            }
        }

    def process(self, news_items: List[Dict]) -> Dict[str, Any]:
        """处理新闻列表，提取重要事件"""
        extracted_events = []

        logger.info(f"开始处理 {len(news_items)} 条新闻")

        for i, news in enumerate(news_items):
            logger.debug(f"处理第 {i + 1} 条新闻: {news.get('title', '')[:50]}...")
            event = self.extract_single_event(news)
            if event and event["impact_level"] != "low":
                extracted_events.append(event)

        # 按影响程度排序
        extracted_events.sort(key=lambda x: self._get_impact_priority(x["impact_level"]), reverse=True)

        return {
            "extracted_events": extracted_events,
            "summary": f"共提取 {len(extracted_events)} 个重要事件",
            "total_processed": len(news_items),
            "high_impact_count": len([e for e in extracted_events if e["impact_level"] == "high"])
        }

    def _get_impact_priority(self, impact_level: str) -> int:
        """获取影响程度的优先级数值"""
        priority_map = {"high": 3, "medium": 2, "low": 1}
        return priority_map.get(impact_level, 1)

    def extract_single_event(self, news: Dict) -> Dict[str, Any]:
        """提取单个新闻事件"""
        # 构建详细的提示词
        prompt = f"""
请分析以下财经新闻，提取对投资决策有影响的事件：

新闻标题：{news.get('title', '')}
新闻内容：{news.get('content', '')}
新闻来源：{news.get('source', '未知')}
发布时间：{news.get('timestamp', '未知')}

请严格按照以下JSON格式输出分析结果：
{{
    "core_event": "用一句话总结核心事件",
    "impact_level": "high/medium/low",
    "time_horizon": "short/mid/long",
    "affected_assets": ["相关的股票、债券、商品或货币"],
    "investment_implication": "简要说明对投资的影响",
    "confidence": 0.0-1.0之间的数值,
    "reasoning": "简要说明分类理由"
}}

要求：
1. 只返回JSON格式，不要其他任何文字
2. 基于事件对金融市场的影响程度进行分级
3. 明确时间框架：短期(1-30天)、中期(1-6个月)、长期(6个月以上)
4. 尽可能具体地列出受影响的资产
"""

        response = self.llm_call(prompt, use_cache=True)

        # 清理响应并尝试解析JSON
        cleaned_response = self._clean_llm_response(response)

        try:
            event_data = json.loads(cleaned_response)
            # 验证必需字段
            if not all(field in event_data for field in self.required_output_fields):
                logger.warning(f"事件数据缺少必需字段: {event_data}")
                return self._create_fallback_event(news)

            return event_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始响应: {response}")
            logger.debug(f"清理后: {cleaned_response}")
            return self._create_fallback_event(news)

    def _clean_llm_response(self, response: str) -> str:
        """清理LLM响应，提取JSON部分"""
        # 移除可能的代码块标记
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()

        # 尝试找到第一个{和最后一个}
        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end != 0:
            return response[start:end]

        return response

    def _create_fallback_event(self, news: Dict) -> Dict[str, Any]:
        """创建备用事件结构"""
        title = news.get('title', '')
        content = news.get('content', '')

        # 简单的基于关键词的影响判断
        impact_level = "medium"
        high_impact_words = ["利率", "降息", "加息", "通胀", "衰退", "危机", "刺激"]
        low_impact_words = ["观点", "评论", "分析", "预计"]

        if any(word in title + content for word in high_impact_words):
            impact_level = "high"
        elif any(word in title + content for word in low_impact_words):
            impact_level = "low"

        return {
            "core_event": title,
            "impact_level": impact_level,
            "time_horizon": "short",
            "affected_assets": [],
            "investment_implication": "需要进一步分析",
            "confidence": 0.3,
            "reasoning": "自动回退分析"
        }