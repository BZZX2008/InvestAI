#质量保证体系

import json
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime
from loguru import logger


class QualityAssurance:
    def __init__(self):
        self.quality_metrics = {}
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Dict]:
        """加载验证规则"""
        return {
            "event_extraction": {
                "required_fields": ["core_event", "impact_level", "time_horizon"],
                "field_validators": {
                    "impact_level": lambda x: x in ["low", "medium", "high"],
                    "time_horizon": lambda x: x in ["short", "mid", "long"],
                    "confidence": lambda x: 0 <= x <= 1
                },
                "content_validators": [
                    lambda event: len(event.get('core_event', '')) > 5,
                    lambda event: len(event.get('core_event', '')) < 500
                ]
            },
            "analysis_output": {
                "required_fields": ["investment_thesis", "confidence", "time_horizon"],
                "field_validators": {
                    "confidence": lambda x: 0 <= x <= 1,
                    "investment_thesis": lambda x: len(x) > 10 and len(x) < 1000
                },
                "consistency_checks": [
                    lambda analysis: self._check_analysis_consistency(analysis)
                ]
            },
            "portfolio_optimization": {
                "required_fields": ["target_allocation", "optimization_type"],
                "field_validators": {
                    "optimization_type": lambda x: x in ["strategic", "tactical", "rebalancing"]
                },
                "allocation_checks": [
                    lambda optimization: self._check_allocation_sum(optimization)
                ]
            }
        }

    def validate_event_extraction(self, events: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """验证事件提取质量"""
        errors = []
        valid_count = 0

        for i, event in enumerate(events):
            event_errors = self._validate_single_event(event, "event_extraction")
            if not event_errors:
                valid_count += 1
            else:
                errors.append(f"事件{i + 1}: {', '.join(event_errors)}")

        validity_ratio = valid_count / len(events) if events else 0
        self._record_metric("event_extraction_quality", validity_ratio)

        is_valid = validity_ratio >= 0.8  # 80%以上有效
        return is_valid, errors

    def validate_analysis_output(self, analysis_results: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证分析输出质量"""
        errors = []
        valid_count = 0
        total_analyses = len(analysis_results)

        for analyst_type, result in analysis_results.items():
            analysis_errors = self._validate_single_analysis(result, analyst_type)
            if not analysis_errors:
                valid_count += 1
            else:
                errors.append(f"{analyst_type}分析: {', '.join(analysis_errors)}")

        validity_ratio = valid_count / total_analyses if total_analyses else 0
        self._record_metric("analysis_quality", validity_ratio)

        is_valid = validity_ratio >= 0.7  # 70%以上有效
        return is_valid, errors

    def validate_portfolio_optimization(self, optimization: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证组合优化质量"""
        errors = []

        # 检查必需字段
        required_fields = self.validation_rules["portfolio_optimization"]["required_fields"]
        for field in required_fields:
            if field not in optimization:
                errors.append(f"缺少必需字段: {field}")

        # 检查字段有效性
        field_validators = self.validation_rules["portfolio_optimization"]["field_validators"]
        for field, validator in field_validators.items():
            if field in optimization and not validator(optimization[field]):
                errors.append(f"字段验证失败: {field}")

        # 检查分配总和
        allocation_checks = self.validation_rules["portfolio_optimization"]["allocation_checks"]
        for check in allocation_checks:
            if not check(optimization):
                errors.append("资产配置总和检查失败")

        is_valid = len(errors) == 0
        self._record_metric("portfolio_optimization_quality", 1.0 if is_valid else 0.0)

        return is_valid, errors

    def _validate_single_event(self, event: Dict[str, Any], rule_type: str) -> List[str]:
        """验证单个事件"""
        errors = []
        rules = self.validation_rules[rule_type]

        # 检查必需字段
        for field in rules["required_fields"]:
            if field not in event:
                errors.append(f"缺少字段: {field}")

        # 检查字段有效性
        for field, validator in rules.get("field_validators", {}).items():
            if field in event and not validator(event[field]):
                errors.append(f"无效的{field}: {event[field]}")

        # 检查内容有效性
        for validator in rules.get("content_validators", []):
            if not validator(event):
                errors.append("内容验证失败")

        return errors

    def _validate_single_analysis(self, analysis: Dict[str, Any], analyst_type: str) -> List[str]:
        """验证单个分析结果"""
        errors = []
        rules = self.validation_rules["analysis_output"]

        # 检查必需字段
        for field in rules["required_fields"]:
            if field not in analysis:
                errors.append(f"缺少字段: {field}")

        # 检查字段有效性
        for field, validator in rules.get("field_validators", {}).items():
            if field in analysis and not validator(analysis[field]):
                errors.append(f"无效的{field}: {analysis[field]}")

        # 检查一致性
        for check in rules.get("consistency_checks", []):
            if not check(analysis):
                errors.append("一致性检查失败")

        return errors

    def _check_analysis_consistency(self, analysis: Dict[str, Any]) -> bool:
        """检查分析一致性"""
        thesis = analysis.get('investment_thesis', '').lower()
        confidence = analysis.get('confidence', 0)

        # 高置信度应该有具体的论点
        if confidence > 0.7 and len(thesis) < 50:
            return False

        # 检查时间框架一致性
        time_horizon = analysis.get('time_horizon', '')
        if time_horizon == 'short' and '长期' in thesis:
            return False

        return True

    def _check_allocation_sum(self, optimization: Dict[str, Any]) -> bool:
        """检查资产配置总和"""
        allocation = optimization.get('target_allocation', {})
        total_weight = 0

        for asset_class, alloc_info in allocation.items():
            if isinstance(alloc_info, dict) and 'target_weight' in alloc_info:
                weight_str = alloc_info['target_weight']
                try:
                    # 尝试解析百分比
                    if '%' in weight_str:
                        weight = float(weight_str.replace('%', ''))
                    else:
                        weight = float(weight_str)
                    total_weight += weight
                except (ValueError, TypeError):
                    # 如果无法解析，跳过
                    continue

        # 允许一定的误差范围
        return 95 <= total_weight <= 105

    def _record_metric(self, metric_name: str, value: float):
        """记录质量指标"""
        timestamp = datetime.now().isoformat()
        if metric_name not in self.quality_metrics:
            self.quality_metrics[metric_name] = []

        self.quality_metrics[metric_name].append({
            "timestamp": timestamp,
            "value": value
        })

        # 只保留最近100个记录
        if len(self.quality_metrics[metric_name]) > 100:
            self.quality_metrics[metric_name] = self.quality_metrics[metric_name][-100:]

    def get_quality_report(self) -> Dict[str, Any]:
        """生成质量报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_quality": self._calculate_overall_quality(),
            "metric_trends": {},
            "recommendations": []
        }

        # 计算各指标趋势
        for metric_name, records in self.quality_metrics.items():
            if records:
                recent_values = [r["value"] for r in records[-10:]]  # 最近10次
                avg_value = sum(recent_values) / len(recent_values)
                report["metric_trends"][metric_name] = {
                    "current": records[-1]["value"],
                    "average": avg_value,
                    "trend": "improving" if len(recent_values) > 1 and recent_values[-1] > recent_values[
                        0] else "stable"
                }

        # 生成改进建议
        report["recommendations"] = self._generate_improvement_recommendations()

        return report

    def _calculate_overall_quality(self) -> float:
        """计算总体质量分数"""
        if not self.quality_metrics:
            return 0.0

        total_score = 0
        count = 0

        for metric_name, records in self.quality_metrics.items():
            if records:
                total_score += records[-1]["value"]
                count += 1

        return total_score / count if count > 0 else 0.0

    def _generate_improvement_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 检查事件提取质量
        event_quality = self.quality_metrics.get("event_extraction_quality", [])
        if event_quality and event_quality[-1]["value"] < 0.8:
            recommendations.append("事件提取质量较低，建议优化提取提示词")

        # 检查分析质量
        analysis_quality = self.quality_metrics.get("analysis_quality", [])
        if analysis_quality and analysis_quality[-1]["value"] < 0.7:
            recommendations.append("分析输出质量需要提升，检查分析器配置")

        # 检查组合优化质量
        portfolio_quality = self.quality_metrics.get("portfolio_optimization_quality", [])
        if portfolio_quality and portfolio_quality[-1]["value"] < 0.9:
            recommendations.append("组合优化建议需要更严格的验证")

        if not recommendations:
            recommendations.append("系统质量良好，继续保持")

        return recommendations


# 全局质量保证实例
quality_assurance = QualityAssurance()