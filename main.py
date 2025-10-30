#!/usr/bin/env python3

import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from loguru import logger
from data.connectors.local_news_loader import LocalNewsLoader
from core.agents.event_extractor import EventExtractionAgent
from core.agents.coordinator import CoordinatorAgent
from output.report_generator import MarkdownReportGenerator

# 导入性能优化组件
from core.cache.smart_cache import llm_cache, data_cache
from core.processing.async_engine import async_engine
from core.processing.priority_system import priority_system
from core.quality.quality_assurance import quality_assurance
from core.monitoring.performance_monitor import performance_monitor

# 配置日志
logger.add("logs/app.log", rotation="50 MB", level="INFO")


class OptimizedInvestmentSystem:
    def __init__(self):
        self.news_loader = LocalNewsLoader()
        self.event_extractor = EventExtractionAgent()
        self.coordinator = CoordinatorAgent()
        self.report_generator = MarkdownReportGenerator()

        # 创建必要目录
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data/cache", exist_ok=True)
        os.makedirs("data/chroma_db", exist_ok=True)
        os.makedirs("data/news", exist_ok=True)
        os.makedirs("output/reports", exist_ok=True)

        # 启动性能监控
        performance_monitor.start_monitoring(interval=30)

        logger.info("优化版投资分析系统初始化完成")

    def run(self, size: int = 200, use_cache: bool = True):
        """运行优化版投资分析系统"""
        logger.info("开始执行优化版投资分析流程")
        start_time = time.time()

        try:
            # 1. 批量加载新闻数据（支持上万条数据）
            logger.info("批量加载新闻数据...")

            #注意不是获取整个文档，而是按照size在整个文档中获取内容， 然后内容和id双重哈希去重， 确保唯一。
            news_items = self._load_news_batch(size, use_cache)

            if not news_items:
                logger.warning("没有获取到新闻数据，创建示例数据")
                self._create_sample_news()
                news_items = self._load_news_batch(size, use_cache)

            performance_monitor.record_processing_time("news_loading", time.time() - start_time)
            data_loading_time = time.time()


            # 2. 批量事件提取与分级
            logger.info(f"批量提取重要事件，批次大小: {size}...")
            events_data = self._batch_extract_events(news_items, batch_size=50)

            # 优先级排序
            prioritized_events = priority_system.prioritize_events(
                events_data.get("extracted_events", [])
            )
            events_data["extracted_events"] = prioritized_events

            # 质量验证
            is_valid, errors = quality_assurance.validate_event_extraction(
                events_data.get("extracted_events", [])
            )
            if not is_valid:
                logger.warning(f"事件提取质量验证失败: {errors}")

            performance_monitor.record_processing_time("event_extraction", time.time() - data_loading_time)
            extraction_time = time.time()

            # 3. 协调分析（使用异步处理）
            logger.info("协调分析任务...")
            coordination_result = self.coordinator.process(events_data)

            # 质量验证
            is_valid, errors = quality_assurance.validate_analysis_output(
                coordination_result.get("analysis_results", {})
            )
            if not is_valid:
                logger.warning(f"分析输出质量验证失败: {errors}")

            performance_monitor.record_processing_time("coordination_analysis", time.time() - extraction_time)
            coordination_time = time.time()

            # 4. 生成报告
            logger.info("生成投资报告...")
            report_data = {**events_data, **coordination_result}
            report = self.report_generator.generate_report(report_data)

            performance_monitor.record_processing_time("report_generation", time.time() - coordination_time)

            # 5. 保存报告和性能数据
            self._save_report(report)
            self._save_performance_data()

            total_time = time.time() - start_time
            performance_monitor.record_processing_time("total_processing", total_time)

            logger.info(f"投资分析流程完成，总耗时: {total_time:.2f}秒")

        except Exception as e:
            logger.error(f"系统执行失败: {e}")
            performance_monitor.record_processing_time("error_handling", time.time() - start_time)
            raise



    ##注意不是获取整个文档，而是按照size数量在整个文档中获取内容， 然后内容和id双重哈希去重， 确保唯一。
    def _load_news_batch(self, size: int, use_cache: bool = True) -> list:
        """批量加载新闻数据，支持缓存和去重"""
        cache_key = f"news_batch_{size}_{self._get_news_cache_key()}"

        if use_cache:
            cached_news = data_cache.get(cache_key)
            if cached_news:
                logger.info(f"使用缓存新闻数据，数量: {len(cached_news)}")
                return cached_news

        # 使用生成器加载大量数据
        all_news = []
        news_count = 0
        duplicate_count = 0

        # 记录已处理的新闻ID和内容哈希，用于去重
        processed_ids = set()
        processed_hashes = set()

        logger.info("开始加载新闻数据...")

        """生成器方式批量加载新闻数据，节省内存"""

        #for news in self.news_loader.load_news_generator(): # 用最新文档
        for news in self.news_loader.load_news_generator('news.txt'): #用指定文档
            news_count += 1

            # 去重逻辑
            news_id = news.get('id')
            #生成内容哈希
            content_hash = self._get_content_hash(news.get('content', ''))

            if news_id and news_id in processed_ids:
                duplicate_count += 1
                continue

            if content_hash in processed_hashes:
                duplicate_count += 1
                continue

            # 添加到处理列表
            all_news.append(news)
            if news_id:
                processed_ids.add(news_id)
            processed_hashes.add(content_hash)

            # 如果达到批次大小，停止加载， 不是获取整个文档
            if len(all_news) >= size:
                break

            # 进度显示
            if news_count % 1000 == 0:
                logger.info(f"已扫描 {news_count} 条新闻，去重后 {len(all_news)} 条")

        logger.info(f"新闻加载完成: 扫描{news_count}条，去重后{len(all_news)}条，重复{duplicate_count}条")

        # 缓存结果
        if use_cache and all_news:
            data_cache.set(cache_key, all_news, ttl=1800)  # 30分钟缓存

        return all_news


    def _get_news_cache_key(self) -> str:
        """生成新闻缓存键，基于文件修改时间"""
        try:
            news_dir = "data/news"
            if not os.path.exists(news_dir):
                return "default"

            # 获取最新文件修改时间
            latest_mtime = 0

            for filename in os.listdir(news_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(news_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    latest_mtime = max(latest_mtime, mtime)

            return str(int(latest_mtime))
        except:
            return "default"


    #根据内容生成哈希
    def _get_content_hash(self, content: str) -> str:
        """生成内容哈希"""
        return hashlib.md5(content.encode()).hexdigest()


    #将总size，分批次交个大模型处理，解决上下文长度问题，最后合并各批次的处理内容
    def _batch_extract_events(self, news_items: list, batch_size: int = 50) -> dict:
        """批量提取事件"""
        if not news_items:
            return {"extracted_events": [], "total_processed": 0}

        logger.info(f"开始批量事件提取，总新闻数: {len(news_items)}")

        # 分批处理
        all_events = []#总的处理内容
        total_batches = (len(news_items) + batch_size - 1) // batch_size


        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(news_items))
            batch_news = news_items[start_idx:end_idx]

            logger.info(f"处理批次 {batch_num + 1}/{total_batches}, 新闻数: {len(batch_news)}")

            # 批量处理单个批次, 调用大模型处理单个批次，解决大模型上下文长度问题
            batch_events = self._process_news_batch(batch_news)

            #单批次处理后内容添加到总列表中
            all_events.extend(batch_events)

            # 进度显示
            if (batch_num + 1) % 5 == 0 or (batch_num + 1) == total_batches:
                logger.info(f"进度: {batch_num + 1}/{total_batches}批次，已提取 {len(all_events)} 个事件")

        return {
            "extracted_events": all_events,
            "total_processed": len(news_items),
            "batch_info": {
                "batch_size": batch_size,
                "total_batches": total_batches,
                "events_per_news": len(all_events) / len(news_items) if news_items else 0
            }
        }



    def _process_news_batch(self, news_batch: list) -> list:
        """处理单个新闻批次"""
        if not news_batch:
            return []

        # 构建批量提示词
        batch_prompt = self._build_batch_prompt(news_batch)

        try:
            # 使用LLM批量处理
            response = self.event_extractor.llm_call(batch_prompt, use_cache=True)
         #   print(response)

            # 解析批量响应
            batch_events = self._parse_batch_response(response, news_batch)

            # 记录LLM调用
            performance_monitor.record_llm_call()

            return batch_events

        except Exception as e:
            logger.error(f"批量事件提取失败: {e}")
            # 回退到单条处理
            return self._fallback_single_processing(news_batch)

    def _build_batch_prompt(self, news_batch: list) -> str:
        """构建批量处理提示词"""
        news_list_text = ""
        for i, news in enumerate(news_batch):
            content = news.get('content', '')[:800]  # 限制内容长度
            news_list_text += f"{i + 1}. 内容: {content}\n"
#"investment_implication": "投资含义说明",
        prompt = f"""
        请批量分析以下多条新闻，提取对投资决策有影响的事件：

        {news_list_text}

        请为每条新闻提取投资相关事件，并按以下JSON格式输出：

        {{
          "batch_events": [
            {{
              "news_index": 1,
              "core_event": "事件描述",
              "impact_level": "high/medium/low",
              "time_horizon": "short/mid/long",
              "affected_assets": ["标的1", "标的2"],
              "Label"："标注涉及：宏观经济指标/政策变动/行业颠覆事件/国际关联事件/企业或公司动态/市场异动与交易事件/社会与民生事件/科技与创新进展/法律与诉讼/监管行动与合规事件/地理与区域事件/人事变动（非公司层面）/舆情事件等等"
              "importance ranking": "事件影响与重要性评分(1-5)",
              "basis":"评分依据与原理"
              
            }},
            ...
          ]
        }}

        要求：
        1. 只返回JSON格式，不要其他内容
        2. 为每条新闻至少提取一个事件
        3. 重点关注金融、经济、政策相关事件
        4. 如果新闻无关投资，impact_level设为"low"
        """
        return prompt

    def _parse_batch_response(self, response: str, original_news: list) -> list:
        """解析批量响应"""
        import json
        import re

        try:
            # 清理响应
            cleaned = re.sub(r'```json\s*', '', response)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()

            # 提取JSON
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("未找到JSON内容")

            json_str = cleaned[start:end]
            result = json.loads(json_str)

            batch_events = result.get('batch_events', [])

            # 验证事件数量
            if len(batch_events) != len(original_news):
                logger.warning(f"批量事件数量不匹配: 期望{len(original_news)}，实际{len(batch_events)}")

            # 添加原始新闻信息
            for event in batch_events:
                news_index = event.get('news_index', 1) - 1
                if 0 <= news_index < len(original_news):
                    original_news_item = original_news[news_index]
                    event['source_file'] = original_news_item.get('source_file')
                    event['source_line'] = original_news_item.get('source_line')
                    event['original_timestamp'] = original_news_item.get('timestamp')
                    event['original_category'] = original_news_item.get('category')

            return batch_events

        except Exception as e:
            logger.error(f"批量响应解析失败: {e}")
            logger.debug(f"原始响应: {response}")
            raise

    def _fallback_single_processing(self, news_batch: list) -> list:
        """回退到单条处理"""
        logger.info("使用单条处理回退方案")
        all_events = []

        for news in news_batch:
            try:
                # 使用现有的事件提取器单条处理
                events_data = self.event_extractor.process([news])
                events = events_data.get('extracted_events', [])
                all_events.extend(events)

                # 记录LLM调用
                performance_monitor.record_llm_call()

            except Exception as e:
                logger.error(f"单条事件提取失败: {e}")
                # 创建默认事件
                default_event = self._create_default_event(news)
                all_events.append(default_event)

        return all_events

    def _create_default_event(self, news: dict) -> dict:
        """创建默认事件"""
        return {
            "core_event": news.get('content', '')[:100],
            "impact_level": "low",
            "time_horizon": "short",
            "affected_assets": [],
            "investment_implication": "需要进一步分析",
            "confidence": 0.3,
            "source_file": news.get('source_file'),
            "source_line": news.get('source_line')
        }

    def _create_sample_news(self):
        """创建示例新闻文件"""
        sample_content = """ID: 4422906 | 时间: 2025-10-08 22:46 | 标签: 公司/市场 | 内容: 美光科技公司股价上涨5.1%，受AI芯片需求推动。
ID: 4422907 | 时间: 2025-10-08 22:45 | 标签: 政策/宏观 | 内容: 美联储主席表示通胀压力缓解，可能考虑降息。
ID: 4422908 | 时间: 2025-10-08 22:44 | 标签: 行业/科技 | 内容: 人工智能芯片需求激增，英伟达业绩超预期。
ID: 4422909 | 时间: 2025-10-08 22:43 | 标签: 市场/商品 | 内容: 国际油价突破85美元，地缘政治紧张局势升级。
ID: 4422910 | 时间: 2025-10-08 22:42 | 标签: 经济/数据 | 内容: 美国非农就业数据超预期，失业率降至3.5%。"""

        sample_file = "data/news/sample_batch_news.txt"
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)

        logger.info(f"已创建示例新闻文件: {sample_file}")

    def _save_report(self, report: str):
        """保存报告到文件"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/reports/investment_report_{timestamp}.md"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"报告已保存: {filename}")

        # 同时在控制台输出摘要
        print("\n" + "=" * 50)
        print("投资分析报告摘要")
        print("=" * 50)
        lines = report.split('\n')
        for line in lines[:25]:  # 只输出前25行
            if line.strip():
                print(line)
        print("=" * 50)
        print(f"完整报告已保存至: {filename}")

    def _save_performance_data(self):
        """保存性能数据"""
        from datetime import datetime
        import json

        # 生成性能报告
        perf_report = performance_monitor.get_performance_report()
        quality_report = quality_assurance.get_quality_report()
        cache_stats = llm_cache.get_stats()

        # 保存性能数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        perf_filename = f"output/reports/performance_{timestamp}.json"

        performance_data = {
            "timestamp": timestamp,
            "performance": perf_report,
            "quality": quality_report,
            "cache": cache_stats
        }

        with open(perf_filename, 'w', encoding='utf-8') as f:
            json.dump(performance_data, f, indent=2, ensure_ascii=False)

        logger.info(f"性能数据已保存: {perf_filename}")

        # 输出关键性能指标
        print(f"\n📊 性能指标:")
        print(f"   总运行时间: {perf_report['uptime_human']}")
        print(f"   LLM调用次数: {perf_report['llm_calls_total']}")
        print(f"   缓存命中率: {perf_report['cache_performance']['hit_rate']}%")
        print(f"   总体质量分数: {quality_report['overall_quality']:.2f}")

    def __del__(self):
        """析构函数，停止性能监控"""
        performance_monitor.stop_monitoring()


def main():
    """主函数，支持命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description='AI投资分析系统')
    parser.add_argument('--batch-size', type=int, default=500, help='批次大小，默认100条新闻')
    #parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    #parser.add_argument('--test-mode', action='store_true', help='测试模式，使用小批量数据')

    args = parser.parse_args()

    # 测试模式使用小批次
    #if args.test_mode:
     #   args.batch_size = 10
      #  logger.info("测试模式启用，使用小批次处理")

    system = OptimizedInvestmentSystem()

    try:
        system.run(
            batch_size=500,
            #use_cache=not args.no_cache
        )

    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"系统执行失败: {e}")
        raise


if __name__ == "__main__":
    main()