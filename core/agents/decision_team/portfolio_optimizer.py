from core.agents.base_agent import BaseAgent
from typing import Dict, List, Any
import json
import yaml
from loguru import logger


class PortfolioOptimizer(BaseAgent):
    def __init__(self):
        system_prompt = """你是一个专业的投资组合优化专家，专注于资产配置和组合构建。

你的专长包括：
1. 现代投资组合理论(MPT)应用
2. 风险平价和风险预算模型
3. 战术资产配置和战略资产配置
4. 组合再平衡和优化
5. 多因子模型和smart beta策略

请基于投资策略和市场环境提供最优的资产配置方案。"""

        super().__init__("PortfolioOptimizer", system_prompt)

        # 加载投资标的库
        try:
            with open('config/investment_universe.yaml', 'r') as f:
                self.investment_universe = yaml.safe_load(f)
        except:
            self.investment_universe = self._create_default_universe()

    def process(self, input_data: Any) -> Dict[str, Any]:
        """处理输入数据并生成组合优化建议"""
        if isinstance(input_data, dict):
            return self.optimize_portfolio(
                investment_strategy=input_data.get('investment_strategy'),
                current_holdings=input_data.get('current_holdings', {}),
                market_conditions=input_data.get('market_conditions', {})
            )
        else:
            return self.optimize_portfolio(investment_strategy=input_data)

    def optimize_portfolio(self,
                           investment_strategy: Dict[str, Any] = None,
                           current_holdings: Dict[str, Any] = None,
                           market_conditions: Dict[str, Any] = None) -> Dict[str, Any]:
        """优化投资组合"""
        prompt = self._build_optimization_prompt(
            investment_strategy, current_holdings, market_conditions
        )

        response = self.llm_call(prompt, use_cache=True)

        try:
            cleaned_response = self._clean_json_response(response)
            optimization = json.loads(cleaned_response)
            return optimization
        except json.JSONDecodeError as e:
            logger.error(f"组合优化JSON解析失败: {e}")
            return self._create_fallback_optimization(investment_strategy)

    def _build_optimization_prompt(self,
                                   strategy: Dict[str, Any],
                                   holdings: Dict[str, Any],
                                   market_conditions: Dict[str, Any]) -> str:
        """构建组合优化提示词"""
        strategy_summary = self._format_strategy_summary(strategy)
        holdings_summary = self._format_holdings_summary(holdings)
        market_summary = self._format_market_summary(market_conditions)

        prompt = f"""
基于以下信息进行投资组合优化：

投资策略：
{strategy_summary}

当前持仓：
{holdings_summary}

市场环境：
{market_summary}

请提供具体的组合优化建议，包括：

1. 目标资产配置比例
2. 具体的标的和权重
3. 调整操作建议（买入/卖出/持有）
4. 再平衡逻辑和时机
5. 预期收益和风险特征

请严格按照以下JSON格式输出：
{{
    "optimization_type": "strategic/tactical/rebalancing",
    "target_allocation": {{
        "equities": {{
            "target_weight": "百分比",
            "sector_breakdown": {{
                "technology": "百分比",
                "financials": "百分比",
                "healthcare": "百分比",
                "consumer": "百分比",
                "energy": "百分比"
            }},
            "specific_recommendations": [
                {{
                    "asset": "标的代码",
                    "target_weight": "百分比",
                    "current_weight": "百分比",
                    "action": "买入/卖出/持有",
                    "amount": "调整金额或比例",
                    "rationale": "调整理由"
                }}
            ]
        }},
        "bonds": {{
            "target_weight": "百分比",
            "duration_guidance": "久期建议",
            "credit_quality": "信用质量建议"
        }},
        "cash": {{
            "target_weight": "百分比",
            "purpose": "用途说明"
        }},
        "alternatives": {{
            "target_weight": "百分比",
            "types": ["类型建议"]
        }}
    }},
    "rebalancing_plan": {{
        "urgency": "立即/本周/本月",
        "priority_actions": ["优先操作1", "优先操作2"],
        "phased_approach": "是否分阶段执行"
    }},
    "risk_metrics": {{
        "expected_return": "预期收益率",
        "expected_volatility": "预期波动率",
        "max_drawdown": "最大回撤预期",
        "sharpe_ratio": "夏普比率预期"
    }},
    "constraints": {{
        "position_limits": "个股限制",
        "sector_limits": "行业限制",
        "liquidity_requirements": "流动性要求"
    }},
    "monitoring_plan": {{
        "rebalancing_triggers": ["再平衡触发条件"],
        "review_schedule": "回顾频率"
    }}
}}

要求：建议要具体、可执行，考虑交易成本和流动性。
"""
        return prompt

    def _format_strategy_summary(self, strategy: Dict[str, Any]) -> str:
        """格式化策略摘要"""
        if not strategy:
            return "无明确投资策略"

        summary = []
        thesis = strategy.get('unified_thesis', '')
        if thesis:
            summary.append(f"核心理念: {thesis}")

        asset_allocation = strategy.get('asset_allocation', {})
        if asset_allocation:
            summary.append("资产配置方向:")
            for asset_class, alloc in asset_allocation.items():
                allocation_desc = alloc.get('allocation', '')
                if allocation_desc:
                    summary.append(f"  - {asset_class}: {allocation_desc}")

        return "\n".join(summary)

    def _format_holdings_summary(self, holdings: Dict[str, Any]) -> str:
        """格式化持仓摘要"""
        if not holdings:
            return "无当前持仓信息"

        summary = ["当前持仓:"]
        for asset_class, positions in holdings.items():
            if isinstance(positions, dict) and positions:
                summary.append(f"  - {asset_class}:")
                for asset, weight in list(positions.items())[:3]:  # 只显示前3个
                    summary.append(f"    * {asset}: {weight}")
            elif isinstance(positions, list):
                for position in positions[:3]:
                    summary.append(f"  - {position}")

        return "\n".join(summary)

    def _format_market_summary(self, market_conditions: Dict[str, Any]) -> str:
        """格式化市场环境摘要"""
        if not market_conditions:
            return "使用默认市场假设"

        summary = ["市场环境:"]
        if 'volatility' in market_conditions:
            summary.append(f"波动率: {market_conditions['volatility']}")
        if 'liquidity' in market_conditions:
            summary.append(f"流动性: {market_conditions['liquidity']}")
        if 'sentiment' in market_conditions:
            summary.append(f"市场情绪: {market_conditions['sentiment']}")

        return "\n".join(summary) if len(summary) > 1 else "使用默认市场假设"

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

    def _create_default_universe(self) -> Dict[str, Any]:
        """创建默认投资标的库"""
        return {
            "equities": {
                "technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "TSM"],
                "financials": ["JPM", "BAC", "GS", "MS", "V"],
                "healthcare": ["JNJ", "PFE", "UNH", "LLY", "MRK"],
                "consumer": ["AMZN", "TSLA", "WMT", "PG", "KO"],
                "energy": ["XOM", "CVX", "SHEL", "COP", "EOG"]
            },
            "bonds": {
                "government": ["TLT", "IEF", "SHY"],
                "corporate": ["LQD", "HYG", "JNK"]
            },
            "etfs": {
                "broad_market": ["SPY", "QQQ", "IWM", "VTI"],
                "sector": ["XLK", "XLF", "XLV", "XLE", "XLY"]
            }
        }

    def _create_fallback_optimization(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """创建备用优化方案"""
        return {
            "optimization_type": "strategic",
            "target_allocation": {
                "equities": {
                    "target_weight": "60%",
                    "sector_breakdown": {
                        "technology": "25%",
                        "financials": "15%",
                        "healthcare": "10%",
                        "consumer": "8%",
                        "energy": "2%"
                    }
                },
                "bonds": {
                    "target_weight": "30%",
                    "duration_guidance": "中短久期",
                    "credit_quality": "投资级"
                },
                "cash": {
                    "target_weight": "10%",
                    "purpose": "流动性和机会储备"
                }
            },
            "rebalancing_plan": {
                "urgency": "本月内完成",
                "priority_actions": ["建立核心仓位", "设置止损位"]
            },
            "risk_metrics": {
                "expected_return": "7-9%",
                "expected_volatility": "12-15%",
                "max_drawdown": "20-25%"
            }
        }