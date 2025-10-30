from core.agents.base_agent import BaseAgent
from typing import Dict, List, Any
import json
from loguru import logger


class RiskManager(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个专业的风险管理专家，专注于投资组合风险识别、测量和控制。

你的专长包括：
1. 市场风险、信用风险、流动性风险管理
2. VaR(风险价值)和压力测试
3. 风险因子分析和暴露管理
4. 止损策略和风险预算
5. 组合对冲和保险策略

请基于投资组合特征和市场环境提供全面的风险管理方案。"""

        super().__init__("RiskManager", system_prompt)

    def process(self, input_data: Any) -> Dict[str, Any]:
        """处理输入数据并生成风险管理建议"""
        if isinstance(input_data, dict):
            return self.assess_risks(
                portfolio_data=input_data.get('portfolio_data'),
                market_conditions=input_data.get('market_conditions', {}),
                investment_strategy=input_data.get('investment_strategy', {})
            )
        else:
            return self.assess_risks(portfolio_data=input_data)

    def assess_risks(self,
                     portfolio_data: Dict[str, Any] = None,
                     market_conditions: Dict[str, Any] = None,
                     investment_strategy: Dict[str, Any] = None) -> Dict[str, Any]:
        """评估投资组合风险"""
        prompt = self._build_risk_assessment_prompt(
            portfolio_data, market_conditions, investment_strategy
        )

        response = self.llm_call(prompt, use_cache=True)

        try:
            cleaned_response = self._clean_json_response(response)
            risk_assessment = json.loads(cleaned_response)
            return risk_assessment
        except json.JSONDecodeError as e:
            logger.error(f"风险评估JSON解析失败: {e}")
            return self._create_fallback_risk_assessment()

    def _build_risk_assessment_prompt(self,
                                      portfolio: Dict[str, Any],
                                      market_conditions: Dict[str, Any],
                                      strategy: Dict[str, Any]) -> str:
        """构建风险评估提示词"""
        portfolio_summary = self._format_portfolio_summary(portfolio)
        market_risk_summary = self._format_market_risk_summary(market_conditions)
        strategy_risk_summary = self._format_strategy_risk_summary(strategy)

        prompt = f"""
基于以下信息进行投资组合风险评估：

投资组合概况：
{portfolio_summary}

市场风险环境：
{market_risk_summary}

投资策略风险特征：
{strategy_risk_summary}

请提供全面的风险评估和控制建议，包括：

1. 主要风险识别和测量
2. 风险集中度和相关性分析
3. 压力测试和极端情景分析
4. 风险控制措施和应急预案
5. 风险监控指标和预警机制

请严格按照以下JSON格式输出：
{{
    "risk_assessment": {{
        "overall_risk_level": "低/中/高",
        "var_estimate": "风险价值估算",
        "expected_shortfall": "预期亏损",
        "stress_test_results": {{
            "2008_crisis": "2008年危机情景下的损失",
            "2020_covid": "2020年疫情情景下的损失",
            "inflation_shock": "通胀冲击情景下的损失"
        }}
    }},
    "risk_factors": [
        {{
            "factor": "风险因子名称",
            "exposure": "暴露程度",
            "contribution": "风险贡献",
            "management_action": "管理措施"
        }}
    ],
    "concentration_risks": [
        {{
            "type": "集中度类型",
            "assets": ["相关资产"],
            "risk_level": "风险等级",
            "mitigation": "缓解措施"
        }}
    ],
    "liquidity_analysis": {{
        "liquidity_profile": "流动性概况",
        "redemption_pressure": "赎回压力",
        "funding_liquidity": "融资流动性"
    }},
    "risk_controls": {{
        "position_limits": {{
            "single_asset": "单个资产限制",
            "sector": "行业限制",
            "country": "国家限制"
        }},
        "stop_loss_strategy": {{
            "individual_positions": "个股止损策略",
            "portfolio_level": "组合级止损策略",
            "trailing_stops": "移动止损设置"
        }},
        "hedging_recommendations": [
            {{
                "hedge_instrument": "对冲工具",
                "hedge_ratio": "对冲比例",
                "cost_benefit": "成本效益分析"
            }}
        ]
    }},
    "early_warning_indicators": [
        {{
            "indicator": "预警指标",
            "threshold": "阈值",
            "action": "触发行动"
        }}
    ],
    "contingency_plan": {{
        "crisis_scenarios": ["危机情景1", "危机情景2"],
        "immediate_actions": ["立即行动1", "立即行动2"],
        "recovery_plan": "恢复计划"
    }}
}}

要求：风险评估要全面，控制措施要具体可行。
"""
        return prompt

    def _format_portfolio_summary(self, portfolio: Dict[str, Any]) -> str:
        """格式化投资组合摘要"""
        if not portfolio:
            return "无详细投资组合信息"

        summary = ["投资组合特征:"]

        # 资产配置
        allocation = portfolio.get('target_allocation', {})
        if allocation:
            summary.append("资产配置:")
            for asset_class, alloc in allocation.items():
                if isinstance(alloc, dict) and 'target_weight' in alloc:
                    summary.append(f"  - {asset_class}: {alloc['target_weight']}")

        # 风险特征
        risk_metrics = portfolio.get('risk_metrics', {})
        if risk_metrics:
            summary.append("风险指标:")
            for metric, value in risk_metrics.items():
                summary.append(f"  - {metric}: {value}")

        return "\n".join(summary)

    def _format_market_risk_summary(self, market_conditions: Dict[str, Any]) -> str:
        """格式化市场风险摘要"""
        if not market_conditions:
            return "市场环境: 正常"

        summary = ["市场风险环境:"]

        volatility = market_conditions.get('volatility', '正常')
        summary.append(f"波动率: {volatility}")

        sentiment = market_conditions.get('sentiment', '中性')
        summary.append(f"市场情绪: {sentiment}")

        liquidity = market_conditions.get('liquidity', '正常')
        summary.append(f"流动性: {liquidity}")

        # 添加系统性风险指标
        systemic_risks = market_conditions.get('systemic_risks', [])
        if systemic_risks:
            summary.append("系统性风险:")
            for risk in systemic_risks[:3]:
                summary.append(f"  - {risk}")

        return "\n".join(summary)

    def _format_strategy_risk_summary(self, strategy: Dict[str, Any]) -> str:
        """格式化策略风险摘要"""
        if not strategy:
            return "投资策略: 无明确策略风险特征"

        summary = ["策略风险特征:"]

        thesis = strategy.get('unified_thesis', '')
        if thesis:
            summary.append(f"核心理念: {thesis}")

        # 识别策略中的风险偏好
        risk_taking = strategy.get('risk_taking', '')
        if risk_taking:
            summary.append(f"风险承担: {risk_taking}")

        # 杠杆使用
        leverage = strategy.get('leverage', '无杠杆')
        summary.append(f"杠杆使用: {leverage}")

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

    def _create_fallback_risk_assessment(self) -> Dict[str, Any]:
        """创建备用风险评估"""
        return {
            "risk_assessment": {
                "overall_risk_level": "中等",
                "var_estimate": "在95%置信度下，单日最大损失约2-3%",
                "expected_shortfall": "极端情况下损失约4-5%"
            },
            "risk_factors": [
                {
                    "factor": "市场风险",
                    "exposure": "中等",
                    "management_action": "分散投资，设置止损"
                },
                {
                    "factor": "流动性风险",
                    "exposure": "低",
                    "management_action": "保持适量现金"
                }
            ],
            "risk_controls": {
                "position_limits": {
                    "single_asset": "不超过5%",
                    "sector": "不超过20%"
                },
                "stop_loss_strategy": {
                    "individual_positions": "个股下跌8%止损",
                    "portfolio_level": "组合下跌10%减仓"
                }
            },
            "early_warning_indicators": [
                {
                    "indicator": "市场波动率(VIX)",
                    "threshold": "超过30",
                    "action": "降低风险资产暴露"
                }
            ]
        }