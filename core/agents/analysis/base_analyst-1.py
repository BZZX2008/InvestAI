from abc import ABC, abstractmethod
from typing import Dict, List, Any
import json
from loguru import logger
from core.agents.base_agent import BaseAgent


class BaseAnalyst(BaseAgent, ABC):
    def __init__(self, name: str, system_prompt: str):
        super().__init__(name, system_prompt)
        self.analysis_type = name.lower()

    def process(self, input_data: Any) -> Dict[str, Any]:
        """实现BaseAgent的抽象方法 - 现在委托给analyze_events"""
        if isinstance(input_data, list):
            return self.analyze_events(input_data)
        else:
            logger.warning(f"{self.name} 收到非列表输入，尝试转换")
            return self.analyze_events([input_data] if input_data else [])

    @abstractmethod
    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """分析事件并生成投资逻辑 - 子类必须实现"""
        pass

    def extract_investment_logic(self, events: List[Dict]) -> Dict[str, Any]:
        """提取投资逻辑的核心方法"""
        prompt = self._build_analysis_prompt(events)
        response = self.llm_call(prompt, use_cache=True)
        return self._parse_analysis_response(response)

    @abstractmethod
    def _build_analysis_prompt(self, events: List[Dict]) -> str:
        """构建分析提示词 - 子类必须实现"""
        pass

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析分析响应 - 增强错误处理"""
        max_attempts = 3
        cleaned_response = self._clean_json_response(response)

        for attempt in range(max_attempts):
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.warning(f"{self.name} JSON解析尝试 {attempt + 1} 失败: {e}")

                if attempt < max_attempts - 1:
                    # 尝试修复常见的JSON格式问题
                    cleaned_response = self._fix_common_json_issues(cleaned_response)
                else:
                    logger.error(f"{self.name} 所有JSON解析尝试均失败")
                    logger.debug(f"最终清理后的响应: {cleaned_response}")
                    return self._create_fallback_analysis()

        return self._create_fallback_analysis()

    def _fix_common_json_issues(self, json_str: str) -> str:
        """修复常见的JSON格式问题"""
        import re

        # 修复1: 转义字符串中的双引号
        json_str = re.sub(r'(?<!\\)"(?=[^"]*"(?:[^"]*"[^"]*")*[^"]*$)', r'\\"', json_str)

        # 修复2: 添加缺失的逗号
        json_str = re.sub(r'(\s*)(\})(\s*)"', r'\1\2,\3"', json_str)
        json_str = re.sub(r'(\s*)(\])(\s*)"', r'\1\2,\3"', json_str)

        # 修复3: 移除尾随逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

    def _clean_json_response(self, response: str) -> str:
        """清理JSON响应"""
        import re
        # 移除代码块标记
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()

        # 提取第一个{到最后一个}
        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end != 0:
            response = response[start:end]

        # 修复：转义字符串中的双引号
        response = self._escape_quotes_in_strings(response)

        return response

    def _escape_quotes_in_strings(self, json_str: str) -> str:
        """转义JSON字符串值中的双引号"""
        import re

        # 匹配JSON字符串值的正则表达式
        string_pattern = r'"(?:[^"\\]|\\.)*"'

        def escape_quotes(match):
            string_value = match.group(0)
            # 只处理字符串值，不处理键名
            if ':' in json_str[:match.start()]:
                # 转义字符串中的双引号，但保留转义的双引号
                escaped = string_value[1:-1].replace('"', '\\"')
                return f'"{escaped}"'
            return string_value

        return re.sub(string_pattern, escape_quotes, json_str)

    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """创建备用分析结果"""
        return {
            "analysis_type": self.analysis_type,
            "investment_thesis": "分析暂时不可用",
            "time_horizon": "short",
            "confidence": 0.3,
            "key_factors": [],
            "recommendations": []
        }