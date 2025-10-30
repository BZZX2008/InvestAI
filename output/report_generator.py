from datetime import datetime
from typing import Dict, Any, List
from loguru import logger


class MarkdownReportGenerator:
    def __init__(self):
        self.template = self._load_template()

    def _load_template(self) -> str:
        """加载完整报告模板"""
        return """# 智能投资决策报告
**生成时间**: {timestamp}  
**分析周期**: {period}  
**处理新闻**: {processed_count}条 | **重要事件**: {event_count}个

## 🎯 核心事件摘要
{events_summary}

## 📊 专业分析团队观点
{analysis_views}

## 🎯 综合投资策略
{investment_strategy}

## 💼 组合优化建议
{portfolio_optimization}

## 🛡️ 全面风险管理
{risk_management}

## 📈 具体操作计划
{action_plan}

## 🔍 监控与调整
{monitoring_plan}



**为100万资金设计配置方案**（大宗商品+A股）：
   | 资产类别 | 具体标的逻辑                  | 仓位% | 持有周期 | 确定性评级（高/中/低） |  建仓方向（多/空） |
   |----------|-------------------------------|-------|----------|----------------------|--------|
   | 商品     | 供需缺口+金融属性强化+基差分析            |       |          |                      |          |
   | A股      | 政策受益强度+资金流多维验证+产业链传导确定性+景气度-估值性价比      |       |          |                      |           |




**以下是当前的持仓情况，给出合理的建议**
  | 资产类别 | 具体标的 | 资金 | 盈亏 |      合理建议 |        依据（新闻+原理） |
  |----------|----------|------|------|---------|-----------------------|
  | A股      | 分众传媒 | 50万 | 盈利12万 |         |                      |
  | A股      | 胜利股份 | 7万 | 亏损0.5万 |           |                      |
  | A股      | 第一创业 | 40万 | 亏损2万 |        |                      |
  | 期货      | 铁矿石 | 10万 | 无盈亏 |        |                      |
  | 期货      | 菜粕   | 10万 | 无盈亏 |        |                      |



---
*本报告基于AI分析生成，仅供参考，投资有风险，决策需谨慎。*
"""

    def generate_report(self, data: Dict[str, Any]) -> str:
        """生成完整Markdown报告"""
        try:
            events = data.get("extracted_events", [])
            analysis_results = data.get("analysis_results", {})
            investment_strategy = data.get("investment_strategy", {})
            portfolio_optimization = data.get("portfolio_optimization", {})
            risk_assessment = data.get("risk_assessment", {})

            report_content = self.template.format(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                period="当日",
                processed_count=data.get("total_processed", 0),
                event_count=len(events),
                events_summary=self._format_events_summary(events),
                analysis_views=self._format_analysis_views(analysis_results),
                investment_strategy=self._format_investment_strategy(investment_strategy),
                portfolio_optimization=self._format_portfolio_optimization(portfolio_optimization),
                risk_management=self._format_risk_management(risk_assessment),
                action_plan=self._format_action_plan(portfolio_optimization, risk_assessment),
                monitoring_plan=self._format_monitoring_plan(portfolio_optimization, risk_assessment)
            )

            return report_content

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return f"# 报告生成错误\n\n错误信息: {str(e)}\n\n数据键值: {list(data.keys())}"

    def _format_events_summary(self, events: List[Dict]) -> str:
        """格式化事件摘要"""
        if not events:
            return "⚠️ 今日无重要事件"

        summary = []
        high_impact = [e for e in events if e.get("impact_level") == "high"]
        medium_impact = [e for e in events if e.get("impact_level") == "medium"]

        if high_impact:
            summary.append("### 🔴 高影响事件")
            for event in high_impact[:3]:
                summary.append(f"- **{event.get('core_event', '')}**")
                assets = event.get('affected_assets', [])
                if assets:
                    summary.append(f"  - 影响资产: {', '.join(assets[:3])}")

        if medium_impact:
            summary.append("### 🟡 中等影响事件")
            for event in medium_impact[:5]:
                summary.append(f"- {event.get('core_event', '')}")

        return "\n".join(summary)

    def _format_analysis_views(self, analysis_results: Dict[str, Dict]) -> str:
        """格式化分析团队观点"""
        if not analysis_results:
            return "### 专业分析\n暂无分析结果"

        views = []
        for analyst_type, result in analysis_results.items():
            thesis = result.get('investment_thesis', '暂无观点')
            confidence = result.get('confidence', 0)
            time_horizon = result.get('time_horizon', '未知')

            views.append(f"### {analyst_type.upper()}分析")
            views.append(f"- **核心观点**: {thesis}")
            views.append(f"- **时间框架**: {time_horizon}")
            views.append(f"- **置信度**: {confidence:.2f}")

            # 添加具体建议
            recommendations = result.get('recommendations', [])
            if recommendations:
                views.append("- **具体建议**:")
                for rec in recommendations[:2]:
                    asset = rec.get('asset') or rec.get('asset_class') or rec.get('sector', '')
                    direction = rec.get('direction') or rec.get('allocation_change', '')
                    if asset and direction:
                        views.append(f"  - {asset}: {direction}")

        return "\n".join(views)

    def _format_investment_strategy(self, strategy: Dict[str, Any]) -> str:
        """格式化投资策略"""
        if not strategy:
            return "### 投资策略\n策略合成失败"

        content = []
        unified_thesis = strategy.get('unified_thesis', '暂无统一策略')
        confidence = strategy.get('confidence_score', 0)

        content.append(f"**核心理念**: {unified_thesis}")
        content.append(f"**策略置信度**: {confidence:.2f}")

        # 时间分配
        time_allocation = strategy.get('time_allocation', {})
        if time_allocation:
            content.append("\n**时间框架**:")
            for timeframe, desc in time_allocation.items():
                content.append(f"- {timeframe}: {desc}")

        # 资产配置
        asset_allocation = strategy.get('asset_allocation', {})
        if asset_allocation:
            content.append("\n**资产配置**:")
            for asset_class, allocation in asset_allocation.items():
                alloc_desc = allocation.get('allocation', '')
                if alloc_desc:
                    content.append(f"- {asset_class}: {alloc_desc}")
                    specific_assets = allocation.get('specific_assets', [])
                    if specific_assets:
                        content.append(f"  - 重点关注: {', '.join(specific_assets[:3])}")

        return "\n".join(content)

    def _format_portfolio_optimization(self, optimization: Dict[str, Any]) -> str:
        """格式化组合优化建议"""
        if not optimization:
            return "### 组合优化\n优化建议暂不可用"

        content = ["### 目标资产配置"]

        target_allocation = optimization.get('target_allocation', {})
        if not target_allocation:
            return "### 组合优化\n无具体优化建议"

        # 总体配置
        for asset_class, allocation in target_allocation.items():
            if isinstance(allocation, dict) and 'target_weight' in allocation:
                content.append(f"- **{asset_class}**: {allocation['target_weight']}")

                # 详细配置
                if asset_class == 'equities' and 'sector_breakdown' in allocation:
                    content.append("  - 行业配置:")
                    sectors = allocation['sector_breakdown']
                    for sector, weight in sectors.items():
                        content.append(f"    * {sector}: {weight}")

                # 具体标的建议
                specific_recs = allocation.get('specific_recommendations', [])
                if specific_recs:
                    content.append("  - 具体操作:")
                    for rec in specific_recs[:3]:
                        asset = rec.get('asset', '')
                        action = rec.get('action', '')
                        amount = rec.get('amount', '')
                        if asset and action:
                            content.append(f"    * {asset}: {action} {amount}")

        # 风险指标
        risk_metrics = optimization.get('risk_metrics', {})
        if risk_metrics:
            content.append("\n**预期风险指标**:")
            for metric, value in risk_metrics.items():
                content.append(f"- {metric}: {value}")

        return "\n".join(content)

    def _format_risk_management(self, risk_assessment: Dict[str, Any]) -> str:
        """格式化风险管理"""
        if not risk_assessment:
            return "### 风险管理\n风险评估暂不可用"

        content = []

        # 总体风险评估
        risk_assessment_data = risk_assessment.get('risk_assessment', {})
        if risk_assessment_data:
            content.append("### 风险评估")
            overall_risk = risk_assessment_data.get('overall_risk_level', '未知')
            content.append(f"- **总体风险等级**: {overall_risk}")

            var_estimate = risk_assessment_data.get('var_estimate', '')
            if var_estimate:
                content.append(f"- **风险价值(VaR)**: {var_estimate}")

        # 风险因子
        risk_factors = risk_assessment.get('risk_factors', [])
        if risk_factors:
            content.append("\n**主要风险因子**:")
            for factor in risk_factors[:3]:
                factor_name = factor.get('factor', '')
                exposure = factor.get('exposure', '')
                if factor_name and exposure:
                    content.append(f"- {factor_name}: {exposure}暴露")

        # 风险控制措施
        risk_controls = risk_assessment.get('risk_controls', {})
        if risk_controls:
            content.append("\n**风险控制措施**:")

            stop_loss = risk_controls.get('stop_loss_strategy', {})
            if stop_loss:
                content.append("- **止损策略**:")
                for level, strategy in stop_loss.items():
                    content.append(f"  - {level}: {strategy}")

            position_limits = risk_controls.get('position_limits', {})
            if position_limits:
                content.append("- **仓位限制**:")
                for limit_type, limit_value in position_limits.items():
                    content.append(f"  - {limit_type}: {limit_value}")

        return "\n".join(content) if content else "采用标准风险管理措施"

    def _format_action_plan(self, optimization: Dict[str, Any], risk_assessment: Dict[str, Any]) -> str:
        """格式化具体操作计划"""
        content = ["### 执行计划"]

        # 组合优化的操作建议
        rebalancing_plan = optimization.get('rebalancing_plan', {})
        if rebalancing_plan:
            urgency = rebalancing_plan.get('urgency', '')
            priority_actions = rebalancing_plan.get('priority_actions', [])

            if urgency:
                content.append(f"**执行 urgency**: {urgency}")

            if priority_actions:
                content.append("**优先操作**:")
                for action in priority_actions[:3]:
                    content.append(f"- {action}")

        # 具体的资产操作
        equities_allocation = optimization.get('target_allocation', {}).get('equities', {})
        specific_actions = equities_allocation.get('specific_recommendations', [])

        if specific_actions:
            content.append("\n**具体资产操作**:")
            for action in specific_actions[:5]:
                asset = action.get('asset', '')
                action_type = action.get('action', '')
                amount = action.get('amount', '')
                rationale = action.get('rationale', '')

                if asset and action_type:
                    line = f"- {asset}: {action_type}"
                    if amount:
                        line += f" {amount}"
                    if rationale:
                        line += f" (理由: {rationale})"
                    content.append(line)

        return "\n".join(content) if len(content) > 1 else "建议保持现有配置"

    def _format_monitoring_plan(self, optimization: Dict[str, Any], risk_assessment: Dict[str, Any]) -> str:
        """格式化监控计划"""
        content = ["### 监控与调整"]

        # 组合优化的监控计划
        monitoring_plan = optimization.get('monitoring_plan', {})
        if monitoring_plan:
            triggers = monitoring_plan.get('rebalancing_triggers', [])
            review_schedule = monitoring_plan.get('review_schedule', '')

            if triggers:
                content.append("**再平衡触发条件**:")
                for trigger in triggers[:3]:
                    content.append(f"- {trigger}")

            if review_schedule:
                content.append(f"**回顾频率**: {review_schedule}")

        # 风险预警指标
        warning_indicators = risk_assessment.get('early_warning_indicators', [])
        if warning_indicators:
            content.append("\n**风险预警指标**:")
            for indicator in warning_indicators[:3]:
                indicator_name = indicator.get('indicator', '')
                threshold = indicator.get('threshold', '')
                action = indicator.get('action', '')

                if indicator_name and threshold:
                    content.append(f"- {indicator_name}: 阈值{threshold} → {action}")

        return "\n".join(content) if len(content) > 1 else "按标准流程监控"







