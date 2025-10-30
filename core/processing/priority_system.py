from typing import Dict, List, Any
from datetime import datetime
import time
from loguru import logger


class PrioritySystem:
    def __init__(self):
        self.priority_rules = self._load_priority_rules()

    def _load_priority_rules(self) -> Dict[str, Dict]:
        """加载优先级规则"""
        return {
            "high_impact_short_term": {
                "score": 100,
                "conditions": [
                    {"field": "impact_level", "value": "high", "operator": "equals"},
                    {"field": "time_horizon", "value": "short", "operator": "equals"}
                ],
                "description": "高影响短期事件"
            },
            "high_impact_mid_term": {
                "score": 80,
                "conditions": [
                    {"field": "impact_level", "value": "high", "operator": "equals"},
                    {"field": "time_horizon", "value": "mid", "operator": "equals"}
                ],
                "description": "高影响中期事件"
            },
            "portfolio_risk_event": {
                "score": 90,
                "conditions": [
                    {"field": "affected_assets", "value": ["持仓标的"], "operator": "contains_any"},
                    {"field": "impact_level", "value": "medium", "operator": "gte"}
                ],
                "description": "组合风险事件"
            },
            "market_crisis": {
                "score": 95,
                "conditions": [
                    {"field": "core_event", "value": ["危机", "崩盘", "暴跌", "恐慌"], "operator": "contains_any"}
                ],
                "description": "市场危机事件"
            },
            "policy_change": {
                "score": 85,
                "conditions": [
                    {"field": "core_event", "value": ["政策", "监管", "利率", "央行"], "operator": "contains_any"}
                ],
                "description": "政策变化事件"
            },
            "earnings_surprise": {
                "score": 70,
                "conditions": [
                    {"field": "core_event", "value": ["财报", "盈利", "营收"], "operator": "contains_any"},
                    {"field": "impact_level", "value": "medium", "operator": "gte"}
                ],
                "description": "财报惊喜事件"
            }
        }

    def calculate_priority_score(self, event: Dict[str, Any], current_holdings: List[str] = None) -> float:
        """计算事件优先级分数"""
        base_score = 0

        # 基础影响分数
        impact_scores = {"low": 10, "medium": 50, "high": 100}
        base_score += impact_scores.get(event.get('impact_level', 'low'), 10)

        # 时间框架分数（短期事件分数更高）
        time_scores = {"short": 30, "mid": 20, "long": 10}
        base_score += time_scores.get(event.get('time_horizon', 'mid'), 15)

        # 置信度分数
        confidence = event.get('confidence', 0.5)
        base_score *= confidence

        # 应用优先级规则
        rule_bonus = self._apply_priority_rules(event, current_holdings)
        base_score += rule_bonus

        # 时间衰减（如果是旧事件，分数降低）
        time_penalty = self._calculate_time_penalty(event)
        base_score *= time_penalty

        return max(0, min(100, base_score))

    def _apply_priority_rules(self, event: Dict[str, Any], current_holdings: List[str]) -> float:
        """应用优先级规则"""
        total_bonus = 0

        for rule_name, rule in self.priority_rules.items():
            if self._matches_rule(event, rule, current_holdings):
                total_bonus += rule['score']
                logger.debug(f"事件匹配规则 '{rule_name}': +{rule['score']}分")

        return total_bonus

    def _matches_rule(self, event: Dict[str, Any], rule: Dict, current_holdings: List[str]) -> bool:
        """检查事件是否匹配规则"""
        for condition in rule.get('conditions', []):
            field = condition['field']
            value = condition['value']
            operator = condition['operator']

            event_value = event.get(field)

            if operator == "equals":
                if event_value != value:
                    return False
            elif operator == "gte":  # greater than or equal
                impact_levels = ["low", "medium", "high"]
                if impact_levels.index(event_value) < impact_levels.index(value):
                    return False
            elif operator == "contains_any":
                if isinstance(event_value, str):
                    event_text = event_value.lower()
                    if isinstance(value, list):
                        if not any(keyword in event_text for keyword in value):
                            return False
                    else:
                        if value not in event_text:
                            return False
                elif isinstance(event_value, list):
                    if current_holdings and field == "affected_assets":
                        # 检查事件影响的资产是否与持仓有重叠
                        if not any(asset in current_holdings for asset in event_value):
                            return False
                    else:
                        if not any(item in value for item in event_value):
                            return False

        return True

    def _calculate_time_penalty(self, event: Dict[str, Any]) -> float:
        """计算时间衰减惩罚"""
        event_time = event.get('timestamp')
        if not event_time:
            return 1.0

        try:
            # 解析时间戳
            if isinstance(event_time, (int, float)):
                event_dt = datetime.fromtimestamp(event_time)
            else:
                event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))

            # 计算时间差（小时）
            time_diff = (datetime.now() - event_dt).total_seconds() / 3600

            # 指数衰减：1小时内100%，24小时内80%，72小时内50%
            if time_diff <= 1:
                return 1.0
            elif time_diff <= 24:
                return 0.8
            elif time_diff <= 72:
                return 0.5
            else:
                return 0.3

        except Exception as e:
            logger.warning(f"时间衰减计算失败: {e}")
            return 0.7

    def prioritize_events(self, events: List[Dict[str, Any]], current_holdings: List[str] = None) -> List[
        Dict[str, Any]]:
        """对事件进行优先级排序"""
        logger.info(f"开始对 {len(events)} 个事件进行优先级排序")

        scored_events = []
        for event in events:
            score = self.calculate_priority_score(event, current_holdings)
            scored_events.append({
                **event,
                'priority_score': score,
                'priority_level': self._score_to_level(score)
            })

        # 按优先级分数降序排序
        scored_events.sort(key=lambda x: x['priority_score'], reverse=True)

        # 记录优先级分布
        levels = {}
        for event in scored_events:
            level = event['priority_level']
            levels[level] = levels.get(level, 0) + 1

        logger.info(f"优先级分布: {levels}")

        return scored_events

    def _score_to_level(self, score: float) -> str:
        """将分数转换为优先级等级"""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "minimal"

    def get_processing_recommendation(self, prioritized_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取处理建议"""
        critical_events = [e for e in prioritized_events if e['priority_level'] == 'critical']
        high_events = [e for e in prioritized_events if e['priority_level'] == 'high']

        recommendation = {
            "immediate_attention": len(critical_events),
            "high_priority": len(high_events),
            "suggested_batch_size": self._calculate_batch_size(prioritized_events),
            "estimated_processing_time": self._estimate_processing_time(prioritized_events),
            "focus_areas": self._identify_focus_areas(prioritized_events)
        }

        return recommendation

    def _calculate_batch_size(self, events: List[Dict[str, Any]]) -> int:
        """计算建议的批处理大小"""
        critical_count = len([e for e in events if e['priority_level'] == 'critical'])

        if critical_count > 5:
            return 3  # 关键事件多，小批次处理
        elif len(events) > 20:
            return 8  # 事件数量多，中等批次
        else:
            return 5  # 默认批次大小

    def _estimate_processing_time(self, events: List[Dict[str, Any]]) -> str:
        """估算处理时间"""
        critical_count = len([e for e in events if e['priority_level'] in ['critical', 'high']])
        total_events = len(events)

        base_time = total_events * 2  # 每个事件约2秒
        critical_bonus = critical_count * 5  # 关键事件需要更多时间

        total_seconds = base_time + critical_bonus

        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            return f"{total_seconds // 60}分钟"
        else:
            return f"{total_seconds // 3600}小时{total_seconds % 3600 // 60}分钟"

    def _identify_focus_areas(self, events: List[Dict[str, Any]]) -> List[str]:
        """识别重点关注领域"""
        areas = {}

        for event in events[:10]:  # 只关注前10个高优先级事件
            event_text = event.get('core_event', '').lower()

            if any(word in event_text for word in ['利率', '央行', '货币政策']):
                areas['monetary_policy'] = areas.get('monetary_policy', 0) + 1
            if any(word in event_text for word in ['财报', '盈利', '营收']):
                areas['earnings'] = areas.get('earnings', 0) + 1
            if any(word in event_text for word in ['地缘', '战争', '冲突']):
                areas['geopolitical'] = areas.get('geopolitical', 0) + 1
            if any(word in event_text for word in ['通胀', 'cpi', '物价']):
                areas['inflation'] = areas.get('inflation', 0) + 1

        # 返回出现次数最多的3个领域
        sorted_areas = sorted(areas.items(), key=lambda x: x[1], reverse=True)
        return [area[0] for area in sorted_areas[:3]]


# 全局优先级系统实例
priority_system = PrioritySystem()