from abc import ABC, abstractmethod
from typing import Dict, Any, List
from loguru import logger
from core.llm_core.model_client import QwenModelClient, VLLMModelClient


class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm_client = QwenModelClient()
        self.llm_client_1 = VLLMModelClient()
        logger.info(f"Initialized agent: {name}")

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """处理输入并返回结果"""
        pass

    def llm_call(self, prompt: str, **kwargs) -> str:
        """统一的LLM调用方法"""
        return self.llm_client.get_completion(
            prompt=prompt,
            system_message=self.system_prompt,
            **kwargs
        )

    def validate_output(self, output: Dict[str, Any]) -> bool:
        """验证输出格式"""
        required_fields = getattr(self, 'required_output_fields', [])
        return all(field in output for field in required_fields)