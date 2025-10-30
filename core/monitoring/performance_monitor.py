import time
import psutil
import threading
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger


class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "processing_times": {},
            "memory_usage": [],
            "cpu_usage": [],
            "llm_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        self.start_time = time.time()
        self._monitoring_thread = None
        self._stop_monitoring = False

    def start_monitoring(self, interval: int = 30):
        """开始性能监控"""
        self._stop_monitoring = False
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info(f"性能监控已启动，间隔: {interval}秒")

    def stop_monitoring(self):
        """停止性能监控"""
        self._stop_monitoring = True
        if self._monitoring_thread:
            self._monitoring_thread.join()
        logger.info("性能监控已停止")

    def _monitoring_loop(self, interval: int):
        """监控循环"""
        while not self._stop_monitoring:
            try:
                self._record_system_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"性能监控错误: {e}")

    def _record_system_metrics(self):
        """记录系统指标"""
        # 内存使用
        memory_info = psutil.virtual_memory()
        self.metrics["memory_usage"].append({
            "timestamp": datetime.now().isoformat(),
            "percent": memory_info.percent,
            "used_gb": memory_info.used / (1024 ** 3),
            "available_gb": memory_info.available / (1024 ** 3)
        })

        # CPU使用
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics["cpu_usage"].append({
            "timestamp": datetime.now().isoformat(),
            "percent": cpu_percent
        })

        # 限制记录数量
        for key in ["memory_usage", "cpu_usage"]:
            if len(self.metrics[key]) > 100:
                self.metrics[key] = self.metrics[key][-100:]

    def record_processing_time(self, stage: str, duration: float):
        """记录处理时间"""
        if stage not in self.metrics["processing_times"]:
            self.metrics["processing_times"][stage] = []

        self.metrics["processing_times"][stage].append({
            "timestamp": datetime.now().isoformat(),
            "duration": duration
        })

        # 限制记录数量
        if len(self.metrics["processing_times"][stage]) > 50:
            self.metrics["processing_times"][stage] = self.metrics["processing_times"][stage][-50:]

    def record_llm_call(self):
        """记录LLM调用"""
        self.metrics["llm_calls"] += 1

    def record_cache_hit(self):
        """记录缓存命中"""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.metrics["cache_misses"] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        uptime = time.time() - self.start_time

        # 计算平均处理时间
        avg_processing_times = {}
        for stage, times in self.metrics["processing_times"].items():
            if times:
                avg_duration = sum(t["duration"] for t in times) / len(times)
                avg_processing_times[stage] = avg_duration

        # 计算缓存命中率
        total_cache_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total_cache_requests * 100) if total_cache_requests > 0 else 0

        # 当前系统状态
        current_memory = self.metrics["memory_usage"][-1] if self.metrics["memory_usage"] else {}
        current_cpu = self.metrics["cpu_usage"][-1] if self.metrics["cpu_usage"] else {}

        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "llm_calls_total": self.metrics["llm_calls"],
            "cache_performance": {
                "hits": self.metrics["cache_hits"],
                "misses": self.metrics["cache_misses"],
                "hit_rate": round(cache_hit_rate, 2)
            },
            "average_processing_times": avg_processing_times,
            "current_system_status": {
                "memory_usage_percent": current_memory.get("percent", 0),
                "cpu_usage_percent": current_cpu.get("percent", 0)
            },
            "performance_recommendations": self._generate_performance_recommendations()
        }

        return report

    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

    def _generate_performance_recommendations(self) -> List[str]:
        """生成性能改进建议"""
        recommendations = []

        # 检查缓存性能
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = (self.metrics["cache_hits"] / total * 100) if total > 0 else 0.0
        #cache_hit_rate = (self.metrics["cache_hits"] / (self.metrics["cache_hits"] + self.metrics["cache_misses"])) * 100
        if cache_hit_rate < 50:
            recommendations.append("缓存命中率较低，建议优化缓存策略")

        # 检查内存使用
        if self.metrics["memory_usage"]:
            avg_memory = sum(m["percent"] for m in self.metrics["memory_usage"][-10:]) / 10
            if avg_memory > 80:
                recommendations.append("内存使用率较高，建议优化内存使用")

        # 检查处理时间
        processing_times = self.metrics["processing_times"]
        for stage, times in processing_times.items():
            if times:
                avg_time = sum(t["duration"] for t in times) / len(times)
                if avg_time > 30:  # 超过30秒
                    recommendations.append(f"{stage}阶段处理时间较长，建议优化")

        if not recommendations:
            recommendations.append("系统性能良好")

        return recommendations


# 全局性能监控实例
performance_monitor = PerformanceMonitor()