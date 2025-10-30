import requests
import re
from loguru import logger
from diskcache import Cache
from typing import Optional

import json
import os
from typing import Optional
from openai import OpenAI






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
            logger.debug(f"Cache hit for LLM request (model: {self.model})")
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







#"/root/Qwen3-30B-A3B-Thinking-2507-FP8"

class VLLMModelClient:
    def __init__(self, model: str = "/root/Qwen3-8B", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature
        # 初始化缓存
        self.cache = Cache('./data/llm_cache')

        # 设置代理环境变量（适配本地代理配置）
        os.environ['HTTP_PROXY'] = 'http://127.0.0.1:33333'
        os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:33333'
        os.environ['NO_PROXY'] = 'localhost,127.0.0.1'  # 排除本地地址不走代理
        # 设置CUDA可见设备 (新增部分)
        os.environ['CUDA_VISIBLE_DEVICES'] = '0, 1'  # 指定使用第0、1号GPU

        # 配置vLLM API服务器连接
        self.api_key = "sssssss"
        self.api_base = "http://localhost:6008/v1"
        self.client = OpenAI(api_key=self.api_key,
                             base_url=self.api_base
                        )



    def get_completion(self,
                       prompt: str,
                       system_message: str = "You are a helpful assistant",
                       use_cache: bool = True) -> str:
        """
        获取模型补全结果

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            use_cache: 是否使用缓存

        Returns:
            str: 模型响应文本
        """
        # 生成缓存键
        cache_key = f"{system_message[:50]}_{prompt[:100]}_{self.model}"

        if use_cache and cache_key in self.cache:
            logger.debug(f"Cache hit for VLLM request (model: {self.model})")
            return self.cache[cache_key]

        try:
            # 构建消息列表
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})



            # 发送请求到vLLM服务器
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                #stream=False
            )




            # 解析响应
            if completion.choices:
                result = completion.choices[0].message.content
                print(result)
                cleaned = re.sub(r'.*?</think>', '', result, flags=re.DOTALL)
                response_text = cleaned.strip()


                # 缓存结果
                if use_cache:
                    self.cache[cache_key] = response_text.strip()

                logger.debug(f"VLLM request successful (model: {self.model})")
                return response_text
            else:
                logger.error("VLLM request returned no choices")
                return "Error: No response choices"

        except requests.exceptions.RequestException as e:
            logger.error(f"VLLM API request failed: {e}")
            return f"Error: API request failed - {str(e)}"
        except Exception as e:
            logger.error(f"VLLM request exception: {e}")
            return f"Error: {str(e)}"



    def get_completion_with_retry(self,
                                  prompt: str,
                                  system_message: str = "You are a helpful assistant",
                                  max_retries: int = 3,
                                  use_cache: bool = True) -> str:
        """
        带重试机制的获取模型补全结果

        Args:
            prompt: 用户提示词
            system_message: 系统消息
            max_retries: 最大重试次数
            use_cache: 是否使用缓存

        Returns:
            str: 模型响应文本
        """
        for attempt in range(max_retries):
            try:
                result = self.get_completion(prompt, system_message, use_cache)
                if not result.startswith("Error:"):
                    return result
                logger.warning(f"VLLM request failed on attempt {attempt + 1}: {result}")
            except Exception as e:
                logger.warning(f"VLLM request exception on attempt {attempt + 1}: {e}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying VLLM request... ({attempt + 2}/{max_retries})")

        return "Error: All retry attempts failed"


# 创建默认客户端实例
# 可以根据需要选择使用哪个客户端
#default_client = VLLMModelClient()  # 默认使用vLLM客户端
# default_client = QwenModelClient()  # 或者使用Ollama客户端