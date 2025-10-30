#异步处理引擎
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Callable
from loguru import logger
from core.cache.smart_cache import llm_cache, data_cache


class AsyncProcessingEngine:
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_batch_async(self, items: List[Any], process_func: Callable, batch_size: int = 10) -> List[Any]:
        """异步批量处理"""
        logger.info(f"开始异步批量处理 {len(items)} 个项目，批次大小: {batch_size}")

        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await self._process_batch(batch, process_func)
            results.extend(batch_results)

            # 进度日志
            progress = min(i + batch_size, len(items))
            logger.info(f"处理进度: {progress}/{len(items)} ({progress / len(items) * 100:.1f}%)")

        return results

    async def _process_batch(self, batch: List[Any], process_func: Callable) -> List[Any]:
        """处理单个批次"""
        tasks = []
        for item in batch:
            task = self._process_single(item, process_func)
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_single(self, item: Any, process_func: Callable) -> Any:
        """处理单个项目"""
        async with self.semaphore:
            try:
                # 尝试从缓存获取
                cache_key = llm_cache.get_key(item, prefix=process_func.__name__)
                cached_result = llm_cache.get(cache_key)

                if cached_result is not None:
                    logger.debug(f"使用缓存结果: {cache_key}")
                    return cached_result

                # 执行处理函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.executor, process_func, item)

                # 缓存结果
                llm_cache.set(cache_key, result)
                return result

            except Exception as e:
                logger.error(f"处理失败: {e}")
                return {"error": str(e)}

    def parallel_process_analysts(self, analysis_tasks: Dict[str, List]) -> Dict[str, Any]:
        """并行处理分析任务"""
        import concurrent.futures

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(analysis_tasks)) as executor:
            future_to_analyst = {}

            for analyst_type, events in analysis_tasks.items():
                if events:  # 只有有事件的才处理
                    from core.agents.coordinator import CoordinatorAgent
                    # 这里需要获取对应的分析器实例
                    future = executor.submit(self._process_analyst_sync, analyst_type, events)
                    future_to_analyst[future] = analyst_type

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_analyst):
                analyst_type = future_to_analyst[future]
                try:
                    results[analyst_type] = future.result()
                except Exception as e:
                    logger.error(f"{analyst_type} 分析失败: {e}")
                    results[analyst_type] = {"error": str(e)}

        return results

    def _process_analyst_sync(self, analyst_type: str, events: List[Dict]) -> Dict[str, Any]:
        """同步处理分析任务（用于线程池）"""
        from core.agents.coordinator import CoordinatorAgent
        coordinator = CoordinatorAgent()

        if analyst_type in coordinator.analysts:
            analyst = coordinator.analysts[analyst_type]
            return analyst.analyze_events(events)
        else:
            return {"error": f"未知的分析器类型: {analyst_type}"}


# 全局异步引擎实例
async_engine = AsyncProcessingEngine(max_workers=6)