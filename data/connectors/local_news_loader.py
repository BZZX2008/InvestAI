import os
import json
import re
from datetime import datetime
from typing import List, Dict, Generator, Optional, Tuple
from loguru import logger
import glob


class LocalNewsLoader:
    def __init__(self, data_directory: str = "data/news"):
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)

    ##将所有行的数据加入列表中
    def load_news_from_file(self, filename: str) -> List[Dict]:
        """从单个txt文件加载新闻数据"""
        filepath = os.path.join(self.data_directory, filename)

        if not os.path.exists(filepath):
            logger.warning(f"新闻文件不存在: {filepath}")
            return []

        news_items = [] #用于存放当前整个文件的内容
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 按行分割，但保留空行用于分隔不同新闻
            lines = content.split('\n')

            current_news = {} #用于存放一行的内容
            current_line_num = 0

            for line in lines:
                current_line_num += 1
                line = line.strip()

                if not line:
                    # 空行表示当前新闻结束
                    if current_news:
                        news_items.append(current_news)
                        current_news = {}
                    continue

                # 解析每一行，新格式: ID: 4422906 | 时间: 2025-10-08 22:46 | 标签: 公司/市场 | 内容: 美光科技公司股价上涨5.1%。
                if "|" in line:
                    #解析单行数据，每行数据字典化
                    news_data = self._parse_news_line(line, filename, current_line_num)
                    if news_data:
                        # 如果已经有当前新闻，先保存
                        if current_news:
                            news_items.append(current_news)
                        current_news = news_data
                    else:
                        logger.warning(f"解析失败 {filename}:{current_line_num}")

                # 保留对JSON格式的支持
                elif line.startswith("{"):
                    try:
                        json_data = json.loads(line)
                        if isinstance(json_data, dict):
                            json_data['source_file'] = filename
                            json_data['source_line'] = current_line_num
                            # 如果已经有当前新闻，先保存
                            if current_news:
                                news_items.append(current_news)
                            current_news = json_data
                            news_items.append(current_news)
                            current_news = {}
                    except json.JSONDecodeError:
                        logger.warning(f"JSON解析失败 {filename}:{current_line_num}")
                        continue

            # 添加最后一条新闻
            if current_news:
                news_items.append(current_news)

            logger.info(f"从 {filename} 加载了 {len(news_items)} 条新闻")

        except Exception as e:
            logger.error(f"加载新闻文件失败 {filename}: {e}")

        return news_items

    ##将每行数据字典化
    def _parse_news_line(self, line: str, filename: str = "", line_num: int = 0) -> Optional[Dict]:
        """解析单行新闻数据"""
        try:
            # 使用更灵活的正则表达式解析字段
            # 匹配格式: 字段名: 字段值 | 字段名: 字段值
            pattern = r'([^:|]+):\s*(.*?)(?=\s*[^:|]+:\s*|\s*$)'
            matches = re.findall(pattern, line)


            if not matches:
                logger.debug(f"未找到有效字段: {filename}:{line_num}")
                return None

            news_item = {
                'source_file': filename,
                'source_line': line_num,
                'raw_line': line  # 保存原始行用于调试
            }

            field_mapping = {
                'ID': 'id',
                '时间': 'timestamp',
                '标签': 'category',
                '内容': 'content',
                '来源': 'source',
                '标题': 'title'
            }

            for key, value in matches:
                key = key.strip()
                value = value.strip()

                # 使用字段映射
                if key in field_mapping:
                    mapped_key = field_mapping[key]
                    news_item[mapped_key] = value
                else:
                    # 未知字段也保存
                    news_item[key] = value

            # 从内容自动生成标题（如果没有标题字段）
            if 'content' in news_item and 'title' not in news_item:
                content = news_item['content']
                # 取前30个字符作为标题，如果包含句号，取第一句
                if '。' in content:
                    title = content.split('。')[0] + '。'
                else:
                    title = content[:30] + '...' if len(content) > 30 else content
                news_item['title'] = title

            # 验证必要字段
            if 'content' not in news_item:
                print('``````````````````````````````````````````````````````````````````````````````````````````````````')
                logger.warning(f"缺少内容字段: {filename}:{line_num}")
                return None

            # 确保ID存在
            if 'id' not in news_item:
                # 如果没有ID，从内容生成一个简单的ID
                content_hash = hash(news_item['content']) % 1000000
                news_item['id'] = f"auto_{abs(content_hash):06d}"

            #将每行数据字典化
            return news_item

        except Exception as e:
            logger.error(f"解析新闻行失败 {filename}:{line_num}: {e}")
            return None


    def load_news_from_files(self, file_pattern: str = "*.txt") -> List[Dict]:
        """批量从多个文件加载新闻数据"""
        pattern = os.path.join(self.data_directory, file_pattern)
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"未找到匹配的文件: {pattern}")
            return []

        all_news = []
        for filepath in files:
            filename = os.path.basename(filepath)
            news_items = self.load_news_from_file(filename)
            all_news.extend(news_items)

        logger.info(f"从 {len(files)} 个文件加载了 {len(all_news)} 条新闻")
        return all_news


    ##整个文档数据，用生成器方式逐个产出，节省内存
    def load_news_generator(self, file_pattern: str = "*.txt") -> Generator[Dict, None, None]:
        """生成器方式批量加载新闻数据，节省内存"""
        pattern = os.path.join(self.data_directory, file_pattern)
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"未找到匹配的文件: {pattern}")
            return

        for filepath in files:
            filename = os.path.basename(filepath)
            news_items = self.load_news_from_file(filename)#将所有行的数据加入列表中
            for news in news_items:
                #使用 yield 可以按需生成，一次只处理一条新闻，延迟加载 / 节省内存，内存占用恒定。如果 news_items 是一个非常大的列表（比如百万条新闻），直接返回会占用大量内存。
                # 将 news_items 中的每个元素逐个产出，形成一个生成器。
                #作为管道（pipeline）的一部分，在数据处理链中，生成器可以串联起来，实现高效流式处理：

                yield news


    def load_all_news(self, use_generator: bool = False) -> List[Dict]:
        """加载所有新闻文件的数据"""
        if use_generator:
            return list(self.load_news_generator())
        else:
            return self.load_news_from_files()


    def get_news_statistics(self, news_items: List[Dict]) -> Dict:
        """获取新闻数据统计信息"""
        # 初始化统计字典，确保所有键都存在
        stats = {
            'total_count': len(news_items),
            'sources': {},
            'categories': {},
            'date_range': {'min': None, 'max': None},
            'parsing_quality': {
                'valid_news': 0,
                'missing_timestamp': 0,
                'missing_category': 0,
                'short_content': 0
            }
        }

        if not news_items:
            logger.warning("没有新闻数据可统计")
            return stats

        for news in news_items:
            # 统计来源
            source = news.get('source_file', 'unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1

            # 统计分类
            category = news.get('category', '未分类')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1

            # 统计时间范围
            timestamp = news.get('timestamp')
            if timestamp:
                try:
                    # 清理时间戳格式
                    date_str = self._normalize_timestamp(timestamp)
                    if stats['date_range']['min'] is None or date_str < stats['date_range']['min']:
                        stats['date_range']['min'] = date_str
                    if stats['date_range']['max'] is None or date_str > stats['date_range']['max']:
                        stats['date_range']['max'] = date_str
                except Exception as e:
                    logger.debug(f"时间戳解析失败: {timestamp}, 错误: {e}")
                    stats['parsing_quality']['missing_timestamp'] += 1
            else:
                stats['parsing_quality']['missing_timestamp'] += 1

            # 检查内容质量
            content = news.get('content', '')
            if len(content) < 5:
                stats['parsing_quality']['short_content'] += 1
            else:
                stats['parsing_quality']['valid_news'] += 1

            if not news.get('category'):
                stats['parsing_quality']['missing_category'] += 1

        # 计算解析质量百分比
        total = len(news_items)
        if total > 0:
            stats['parsing_quality']['valid_percentage'] = round(
                stats['parsing_quality']['valid_news'] / total * 100, 2
            )

        logger.info(
            f"新闻统计完成: {len(news_items)} 条新闻，{len(stats['sources'])} 个来源，{len(stats['categories'])} 个分类")

        return stats


    def _normalize_timestamp(self, timestamp: str) -> str:
        """规范化时间戳格式"""
        # 移除可能的多余空格和字符
        timestamp = timestamp.strip()

        # 处理常见的时间格式
        if ' ' in timestamp:
            date_part, time_part = timestamp.split(' ', 1)
        else:
            date_part = timestamp
            time_part = "00:00"

        # 确保日期格式正确
        date_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(date_pattern, date_part)
        if match:
            year, month, day = match.groups()
            # 标准化日期格式
            normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            return normalized_date
        else:
            raise ValueError(f"无法解析日期格式: {timestamp}")


    def filter_news(self, news_items: List[Dict], **filters) -> List[Dict]:
        """过滤新闻数据"""
        filtered_news = news_items

        for key, value in filters.items():
            if value is not None:
                if key == 'category':
                    filtered_news = [news for news in filtered_news
                                     if news.get('category') == value]
                elif key == 'source_file':
                    filtered_news = [news for news in filtered_news
                                     if news.get('source_file') == value]
                elif key == 'date_range':
                    start_date, end_date = value
                    filtered_news = [news for news in filtered_news
                                     if self._is_date_in_range(news.get('timestamp'), start_date, end_date)]
                elif key == 'keyword':
                    filtered_news = [news for news in filtered_news
                                     if value.lower() in news.get('content', '').lower()]
                elif key == 'min_content_length':
                    filtered_news = [news for news in filtered_news
                                     if len(news.get('content', '')) >= value]

        return filtered_news


    def _is_date_in_range(self, timestamp: str, start_date: str, end_date: str) -> bool:
        """检查日期是否在范围内"""
        if not timestamp:
            return False

        try:
            date_str = self._normalize_timestamp(timestamp)
            return start_date <= date_str <= end_date
        except:
            return False


    def add_timestamp_if_missing(self, news_items: List[Dict]) -> List[Dict]:
        """为没有时间戳的新闻添加时间戳"""
        for news in news_items:
            if 'timestamp' not in news:
                news['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        return news_items


    def validate_news_data(self, news_items: List[Dict]) -> Tuple[int, List[Dict]]:
        """验证新闻数据质量，返回有效新闻数量和无效新闻列表"""
        valid_news = []
        invalid_news = []

        for news in news_items:
            # 检查必要字段
            if not news.get('content'):
                invalid_news.append({**news, 'error': '缺少内容'})
                continue

            # 检查内容长度
            if len(news.get('content', '')) < 3:
                invalid_news.append({**news, 'error': '内容过短'})
                continue

            # 检查ID
            if not news.get('id'):
                news['id'] = f"auto_{hash(news['content']) % 1000000:06d}"

            valid_news.append(news)

        logger.info(f"数据验证完成: {len(valid_news)} 条有效，{len(invalid_news)} 条无效")
        return len(valid_news), invalid_news


    def export_news_sample(self, news_items: List[Dict], count: int = 10,  output_file: str = "news_sample.txt") -> str:
        """导出新闻样本到文件"""
        sample = news_items[:count]
        output_path = os.path.join(self.data_directory, output_file)

        with open(output_path, 'w', encoding='utf-8') as f:
            for news in sample:
                # 重新格式化为标准格式
                line_parts = []
                if 'id' in news:
                    line_parts.append(f"ID: {news['id']}")
                if 'timestamp' in news:
                    line_parts.append(f"时间: {news['timestamp']}")
                if 'category' in news:
                    line_parts.append(f"标签: {news['category']}")
                if 'content' in news:
                    line_parts.append(f"内容: {news['content']}")

                f.write(" | ".join(line_parts) + "\n\n")

        logger.info(f"新闻样本已导出到: {output_path}")
        return output_path


# 使用示例
if __name__ == "__main__":
    loader = LocalNewsLoader("data/news")

    # 批量加载所有新闻
    all_news = loader.load_all_news()

    # 获取统计信息
    stats = loader.get_news_statistics(all_news)
    print(f"总新闻数: {stats['total_count']}")
    print(f"来源分布: {stats['sources']}")
    print(f"分类分布: {stats['categories']}")
    print(f"时间范围: {stats['date_range']}")
    print(f"解析质量: {stats['parsing_quality']}")

    # 验证数据质量
    valid_count, invalid_news = loader.validate_news_data(all_news)
    print(f"有效新闻: {valid_count}")

    # 过滤新闻
    filtered_news = loader.filter_news(all_news, category="公司/市场", keyword="股价")
    print(f"过滤后新闻数: {len(filtered_news)}")

    # 导出样本
    if all_news:
        sample_file = loader.export_news_sample(all_news, 5)
        print(f"样本文件: {sample_file}")




    # 使用生成器处理大量数据（节省内存）
    print("\n使用生成器处理:")
    news_count = 0
    for news in loader.load_news_generator():
        news_count += 1
        if news_count <= 3:  # 只显示前3条
            print(f"处理新闻: {news.get('title', '无标题')}")
        if news_count % 1000 == 0:
            print(f"已处理 {news_count} 条新闻...")

    print(f"总共处理了 {news_count} 条新闻")