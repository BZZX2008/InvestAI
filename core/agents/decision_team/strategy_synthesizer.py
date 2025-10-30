from core.agents.base_agent import BaseAgent
from typing import Dict, List, Any
import json
from loguru import logger


class StrategySynthesizer(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个顶级的投资策略师，具有跨资产、跨市场的全球投资视野。

你的专长包括：
1. 多资产类别策略配置
2. 风险平价和风险预算模型
3. 因子投资和smart beta策略
4. 动态资产配置和战术调整

请基于全面的专业分析，合成统一的投资策略框架。"""
        super().__init__("StrategySynthesizer", system_prompt)

    def process(self, input_data: Any) -> Dict[str, Any]:
        """处理输入数据并生成专业投资策略"""
        if isinstance(input_data, dict) and 'analysis_results' in input_data:
            return self.synthesize_strategy(input_data['analysis_results'])
        elif isinstance(input_data, dict):
            return self.synthesize_strategy(input_data)
        else:
            logger.warning(f"StrategySynthesizer 收到不支持的输入类型: {type(input_data)}")
            return self._create_default_strategy()

    def synthesize_strategy(self, analysis_results: Dict[str, Dict]) -> Dict[str, Any]:
        """合成专业投资策略"""
        if not analysis_results:
            return self._create_default_strategy()

        prompt = self._build_synthesis_prompt(analysis_results)
        response = self.llm_call(prompt, use_cache=True)

        try:
            cleaned_response = self._clean_json_response(response)
            strategy = json.loads(cleaned_response)
            return strategy
        except json.JSONDecodeError as e:
            logger.error(f"策略合成JSON解析失败: {e}")
            return self._create_fallback_strategy(analysis_results)

    def _build_synthesis_prompt(self, analysis_results: Dict[str, Dict]) -> str:
        """构建专业策略合成提示词"""
        analysis_summary = self._format_professional_analysis_summary(analysis_results)

        prompt = f"""
作为顶级投资策略师，请基于以下各专业团队的深度分析，合成统一的投资策略：

{analysis_summary}

请按照以下专业框架整合分析结果：

## 1. 宏观策略定位
- 基于宏观周期的资产配置基调
- 经济增长-通胀组合的策略含义
- 货币政策环境的配置影响

## 2. 政策驱动机会
- 政策红利受益领域
- 监管变化带来的结构性机会
- 产业政策导向的投资方向

## 3. 行业景气轮动
- 行业生命周期与景气度匹配
- 竞争优势和盈利增长前景
- 估值与增长匹配度

## 4. 市场技术时机
- 技术面支持的入场时机
- 市场情绪提供的逆向机会
- 资金流向指示的板块轮动

## 5. 风险预算配置
- 基于风险溢价的资产配置
- 下行风险保护策略
- 流动性管理和仓位控制

请严格按照以下JSON格式输出专业投资策略：
{{
    "investment_philosophy": "投资哲学核心理念",
    "macro_strategy_context": {{
        "cycle_position": "周期定位",
        "growth_inflation_regime": "增长-通胀组合",
        "monetary_policy_backdrop": "货币政策背景"
    }},
    "strategic_asset_allocation": {{
        "equities": {{
            "target_allocation": "目标配置",
            "regional_breakdown": {{
                "domestic": "国内配置",
                "international": "国际配置"
            }},
            "style_exposure": {{
                "growth": "成长风格",
                "value": "价值风格",
                "quality": "质量风格"
            }}
        }},
        "fixed_income": {{
            "target_allocation": "目标配置",
            "duration_position": "久期立场",
            "credit_exposure": "信用暴露",
            "yield_curve_position": "收益率曲线立场"
        }},
        "alternatives": {{
            "target_allocation": "目标配置",
            "real_assets": "实物资产",
            "hedge_strategies": "对冲策略"
        }},
        "cash": {{
            "target_allocation": "目标配置",
            "strategic_purpose": "战略目的"
        }}
    }},
    "tactical_positions": [
        {{
            "asset_class": "资产类别",
            "position_size": "头寸规模",
            "investment_thesis": "投资逻辑",
            "time_horizon": "时间框架",
            "catalyst": "催化剂",
            "exit_criteria": "退出条件"
        }}
    ],
    "sector_views": {{
        "overweight_sectors": [
            {{
                "sector": "行业",
                "conviction": "确信度",
                "key_companies": ["关键公司"],
                "rationale": "投资理由"
            }}
        ],
        "underweight_sectors": [
            {{
                "sector": "行业",
                "rationale": "低配理由"
            }}
        ]
    }},
    "risk_management_framework": {{
        "portfolio_volatility_target": "组合波动率目标",
        "maximum_drawdown_tolerance": "最大回撤容忍度",
        "liquidity_requirements": "流动性要求",
        "hedging_strategies": ["对冲策略1", "策略2"]
    }},
    "implementation_plan": {{
        "immediate_actions": ["立即行动1", "行动2"],
        "phased_approach": "分阶段执行计划",
        "monitoring_framework": "监控框架"
    }},
    "scenario_analysis": {{
        "base_case": {{
            "probability": "概率",
            "expected_return": "预期收益",
            "key_drivers": ["关键驱动1", "驱动2"]
        }},
        "stress_scenarios": [
            {{
                "scenario": "压力情景",
                "impact": "影响分析",
                "mitigation": "缓解措施"
            }}
        ]
    }},
    "conviction_score": 0.0-1.0,
    "key_success_factors": ["成功关键因素1", "因素2"]
}}

要求：策略要体现专业深度，各资产配置要有明确逻辑支撑，风险控制要具体可行。
"""
        return prompt

    def _format_professional_analysis_summary(self, analysis_results: Dict[str, Dict]) -> str:
        """格式化专业分析摘要"""
        summary = []

        for analyst_type, result in analysis_results.items():
            if analyst_type == 'policy':
                summary.append(self._format_policy_analysis(result))
            elif analyst_type == 'macro':
                summary.append(self._format_macro_analysis(result))
            elif analyst_type == 'industry':
                summary.append(self._format_industry_analysis(result))
            elif analyst_type == 'market':
                summary.append(self._format_market_analysis(result))

        return "\n\n".join(summary)

    def _format_policy_analysis(self, result: Dict) -> str:
        """格式化政策分析"""
        summary = ["## 政策分析核心观点"]
        thesis = result.get('investment_thesis', '')
        if thesis:
            summary.append(f"核心理念: {thesis}")

        winners = result.get('winners_losers_analysis', {}).get('direct_beneficiaries', [])
        if winners:
            summary.append("主要受益领域:")
            for winner in winners[:3]:
                summary.append(f"- {winner.get('sector', '')}: {winner.get('rationale', '')}")

        return "\n".join(summary)

    def _format_macro_analysis(self, result: Dict) -> str:
        """格式化宏观分析"""
        summary = ["## 宏观分析核心观点"]
        cycle = result.get('economic_cycle_assessment', {})
        if cycle:
            summary.append(f"周期定位: {cycle.get('current_phase', '未知')}")

        allocation = result.get('asset_allocation_framework', {})
        if allocation:
            summary.append("资产配置建议:")
            tactical = allocation.get('tactical_opportunities', [])
            for opp in tactical[:2]:
                summary.append(f"- {opp.get('asset_class', '')}: {opp.get('overweight_underweight', '')}")

        return "\n".join(summary)

    def _format_industry_analysis(self, result: Dict) -> str:
        """格式化行业分析"""
        summary = ["## 行业分析核心观点"]
        opportunities = result.get('investment_opportunities', [])
        if opportunities:
            summary.append("重点投资机会:")
            for opp in opportunities[:3]:
                summary.append(f"- {opp.get('opportunity_type', '')}: {opp.get('specific_companies', [])}")

        allocation = result.get('sector_allocation', {})
        if allocation:
            overweight = allocation.get('overweight_sectors', [])
            if overweight:
                summary.append("超配行业:")
                for sector in overweight[:3]:
                    summary.append(f"- {sector.get('sector', '')}")

        return "\n".join(summary)

    def _format_market_analysis(self, result: Dict) -> str:
        """格式化市场分析"""
        summary = ["## 市场分析核心观点"]
        regime = result.get('market_regime', {})
        if regime:
            summary.append(f"市场状态: {regime.get('current_regime', '未知')}")

        signals = result.get('trading_signals', [])
        if signals:
            summary.append("交易信号:")
            for signal in signals[:3]:
                summary.append(f"- {signal.get('asset', '')}: {signal.get('signal', '')}")

        return "\n".join(summary)

    def _clean_json_response(self, response: str) -> str:
        """清理JSON响应"""
        import re
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()

        start = response.find('{')
        end = response.rfind('}') + 1

        if start != -1 and end != 0:
            return response[start:end]

        return response

    def _create_default_strategy(self) -> Dict[str, Any]:
        """创建默认策略"""
        return {
            "investment_philosophy": "在不确定性中寻找确定性机会",
            "strategic_asset_allocation": {
                "equities": {"target_allocation": "均衡配置"},
                "fixed_income": {"target_allocation": "防御性配置"},
                "cash": {"target_allocation": "保持流动性"}
            },
            "risk_management_framework": {
                "maximum_drawdown_tolerance": "严格控制下行风险"
            },
            "conviction_score": 0.5
        }

    def _create_fallback_strategy(self, analysis_results: Dict) -> Dict[str, Any]:
        """创建备用策略"""
        return {
            "investment_philosophy": "基于专业分析的稳健配置",
            "strategic_asset_allocation": {
                "equities": {
                    "target_allocation": "重点关注",
                    "style_exposure": {"quality": "质量优先"}
                }
            },
            "tactical_positions": [{
                "asset_class": "多元化资产",
                "investment_thesis": "分散风险，把握结构性机会",
                "time_horizon": "中期"
            }],
            "conviction_score": 0.6,
            "key_success_factors": ["严格风险控制", "灵活战术调整"]
        }