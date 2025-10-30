# 📁 config.py
import os
from typing import Dict, Any


class Config:
    """系统配置"""
    # 模型配置
    MODEL_NAME = "qwen3:1.7b"
    MODEL_TEMPERATURE = 0.1  # 降低随机性，提高稳定性
    MODEL_URL = "http://localhost:11434/api/generate"

    # 数据配置
    DATA_PATHS = {
        "raw": "data/raw",
        "processed": "data/processed",
        "vector_store": "data/vector_store",
        "output": "output"
    }

    # 智能体配置
    AGENT_CONFIGS = {
        "information_extractor": {
            "system_message": "你是一个专业的投资信息分析专家，专门从海量新闻中识别重要投资事件。",
            "focus_areas": ["货币政策", "财政政策", "行业监管", "公司事件", "经济数据", "地缘政治"]
        }
    }


config = Config()