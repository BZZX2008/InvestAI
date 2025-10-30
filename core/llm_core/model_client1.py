import requests
import re
from loguru import logger
from diskcache import Cache
from typing import Optional


class QwenModelClient:
    def __init__(self, model: str = "qwen3:1.7b", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        self.url = "http://localhost:11434/api/generate"
        self.cache = Cache('./data/llm_cache')

    def get_completion(self,
                       prompt: str,
                       system_message: str = "You are a helpful assistant",
                       use_cache: bool = True) -> str:

        cache_key = f"{system_message[:50]}_{prompt[:100]}"

        if use_cache and cache_key in self.cache:
            logger.debug("Cache hit for LLM request")
            return self.cache[cache_key]

        full_prompt = f"{system_message}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": self.temperature,
            "stream": False,
            "seed": 42
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=3000)

            if response.status_code == 200:
                result = response.json()
                cleaned = re.sub(r'<think>.*?</think>', '', result['response'], flags=re.DOTALL)
                response_text = cleaned.strip()

                if use_cache:
                    self.cache[cache_key] = response_text

                return response_text
            else:
                logger.error(f"LLM request failed: {response.status_code} - {response.text}")
                return f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"LLM request exception: {e}")
            return f"Error: {str(e)}"