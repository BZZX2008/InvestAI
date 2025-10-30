#智能缓存
import time
import hashlib
import json
from typing import Any, Optional
from diskcache import Cache
from loguru import logger


class SmartCache:
    def __init__(self, cache_dir: str = "./data/cache", default_ttl: int = 3600):
        self.cache = Cache(cache_dir)
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }

    def get_key(self, data: Any, prefix: str = "") -> str:
        """生成缓存键"""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)

        key = hashlib.md5(f"{prefix}{data_str}".encode()).hexdigest()
        return f"{prefix}_{key}" if prefix else key

    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        result = self.cache.get(key)
        if result is not None:
            self.stats['hits'] += 1
            logger.debug(f"缓存命中: {key}")
        else:
            self.stats['misses'] += 1
        return result

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存数据"""
        ttl = ttl or self.default_ttl
        self.cache.set(key, value, expire=ttl)
        self.stats['sets'] += 1
        logger.debug(f"缓存设置: {key}, TTL: {ttl}")

    def get_or_compute(self, key: str, compute_func: callable, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """获取或计算缓存数据"""
        cached = self.get(key)
        if cached is not None:
            return cached

        result = compute_func(*args, **kwargs)
        self.set(key, result, ttl)
        return result

    def clear_expired(self):
        """清理过期缓存"""
        self.cache.expire()
        logger.info("已清理过期缓存")

    def get_stats(self) -> dict:
        """获取缓存统计"""
        hit_ratio = self.stats['hits'] / max(1, self.stats['hits'] + self.stats['misses'])
        return {
            **self.stats,
            'hit_ratio': round(hit_ratio, 4),
            'size': len(self.cache),
            'cache_dir': self.cache.directory
        }

    def clear_all(self):
        """清空所有缓存"""
        self.cache.clear()
        logger.info("已清空所有缓存")


# 全局缓存实例
llm_cache = SmartCache("./data/cache/llm", default_ttl=86400)  # 24小时
data_cache = SmartCache("./data/cache/data", default_ttl=3600)  # 1小时