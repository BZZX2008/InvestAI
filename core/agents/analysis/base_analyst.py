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
        """解析分析响应"""
        try:
            # 清理响应并提取JSON
            cleaned = self._clean_json_response(response)
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"{self.name} JSON解析失败: {e}")
            logger.debug(f"原始响应: {response}")
            return self._create_fallback_analysis()

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
            return response[start:end]

        return response

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