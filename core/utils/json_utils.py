import json
import re
import logging
from typing import Any, Dict
from loguru import logger


class JSONUtils:
    @staticmethod
    def safe_json_parse(json_str: str, default: Any = None) -> Any:
        """安全解析JSON，处理各种格式问题"""
        if not json_str or not isinstance(json_str, str):
            return default

        try:
            # 第一步：基础清理
            cleaned = JSONUtils._basic_clean(json_str)

            # 第二步：修复常见的JSON格式问题
            cleaned = JSONUtils._fix_common_json_issues(cleaned)

            # 第三步：尝试解析
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"清理前: {json_str[:500]}...")
            logger.debug(f"清理后: {cleaned[:500]}...")

            # 第四步：尝试更激进的修复
            try:
                repaired = JSONUtils._aggressive_json_repair(cleaned)
                return json.loads(repaired)
            except:
                logger.error("激进修复也失败，返回默认值")
                return default

    @staticmethod
    def _basic_clean(text: str) -> str:
        """基础清理"""
        # 移除代码块标记
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        # 移除控制字符（除了制表符、换行符、回车符）
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # 修复常见的转义问题
        text = text.replace('\\"', '"')
        text = text.replace("\\'", "'")

        return text

    @staticmethod
    def _fix_common_json_issues(text: str) -> str:
        """修复常见的JSON格式问题"""
        # 修复未转义的双引号
        text = re.sub(r'([^\\])"([^"\\]*)"', r'\1"\2"', text)

        # 修复单引号（转换为双引号）
        text = re.sub(r"'([^']*)'", r'"\1"', text)

        # 修复缺失的逗号
        text = re.sub(r'("\s*")\s*"', r'\1, "', text)
        text = re.sub(r'(\d)\s*"', r'\1, "', text)
        text = re.sub(r'}\s*"', r'}, "', text)
        text = re.sub(r']\s*"', r'], "', text)

        # 修复缺失的引号
        text = re.sub(r'(\w+):\s*([^",{}\[\]]+)(?=\s*[,}\]])', r'"\1": "\2"', text)

        # 修复尾随逗号
        text = re.sub(r',\s*([}\]])', r'\1', text)

        return text

    @staticmethod
    def _aggressive_json_repair(text: str) -> str:
        """激进的JSON修复"""
        # 尝试提取第一个{到最后一个}
        start = text.find('{')
        end = text.rfind('}') + 1

        if start != -1 and end != 0:
            text = text[start:end]

        # 如果仍然无效，尝试手动构建
        if not JSONUtils._is_valid_json(text):
            text = JSONUtils._build_fallback_json()

        return text

    @staticmethod
    def _is_valid_json(text: str) -> bool:
        """检查是否为有效JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False

    @staticmethod
    def _build_fallback_json() -> str:
        """构建回退JSON"""
        return '{"error": "JSON解析失败", "analysis_type": "fallback"}'

    @staticmethod
    def validate_json_structure(data: Dict, required_fields: list) -> bool:
        """验证JSON结构"""
        if not isinstance(data, dict):
            return False

        for field in required_fields:
            if field not in data:
                logger.warning(f"缺少必需字段: {field}")
                return False

        return True

    @staticmethod
    def sanitize_string(value: str) -> str:
        """清理字符串中的问题字符"""
        if not isinstance(value, str):
            return str(value) if value is not None else ""

        # 移除控制字符
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

        # 修复常见的转义问题
        value = value.replace('\\"', '"').replace("\\'", "'")

        # 限制长度（避免过长的字符串）
        if len(value) > 1000:
            value = value[:1000] + "..."

        return value