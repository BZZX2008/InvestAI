import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from loguru import logger
from core.agents.base_agent import BaseAgent

# 导入所有智能体
from core.agents.analysis_team.policy_analyst import PolicyAnalyst
from core.agents.analysis_team.macro_analyst import MacroAnalyst
from core.agents.analysis_team.industry_analyst import IndustryAnalyst
from core.agents.analysis_team.market_analyst import MarketAnalyst
from core.agents.decision_team.strategy_synthesizer import StrategySynthesizer
from core.agents.decision_team.portfolio_optimizer import PortfolioOptimizer
from core.agents.decision_team.risk_manager import RiskManager


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        system_prompt = """你是投资分析系统的协调中心，负责任务分配、分析整合和决策协调。"""
        super().__init__("CoordinatorAgent", system_prompt)
        self.executor = ThreadPoolExecutor(max_workers=6)

        # 初始化所有智能体
        self._initialize_agents()

    def _initialize_agents(self):
        """初始化所有智能体"""
        logger.info("初始化所有智能体...")

        # 分析智能体
        self.analysts = {
            'policy': PolicyAnalyst(),
            'macro': MacroAnalyst(),
            'industry': IndustryAnalyst(),
            'market': MarketAnalyst()
        }

        # 决策智能体
        self.strategy_synthesizer = StrategySynthesizer()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_manager = RiskManager()

        logger.info("所有智能体初始化完成")

    def process(self, events_data: Dict[str, Any]) -> Dict[str, Any]:
        """协调处理事件数据"""
        events = events_data.get("extracted_events", [])

        if not events:
            return {"error": "没有需要处理的事件"}

        logger.info(f"开始协调分析 {len(events)} 个事件")

        try:
            # 1. 分类事件并分配任务
            analysis_tasks = self._categorize_events(events)

            # 2. 执行分析任务
            analysis_results = self._execute_analysis(analysis_tasks)

            # 3. 合成投资策略
            investment_strategy = self.strategy_synthesizer.synthesize_strategy(analysis_results)

            # 4. 组合优化
            portfolio_optimization = self._optimize_portfolio(investment_strategy)

            # 5. 风险管理
            risk_assessment = self._assess_risks(portfolio_optimization, investment_strategy)

            return {
                "analysis_tasks": analysis_tasks,
                "analysis_results": analysis_results,
                "investment_strategy": investment_strategy,
                "portfolio_optimization": portfolio_optimization,
                "risk_assessment": risk_assessment,
                "coordination_summary": self._generate_coordination_summary(
                    analysis_tasks, analysis_results, portfolio_optimization, risk_assessment
                )
            }

        except Exception as e:
            logger.error(f"协调处理失败: {e}")
            return {
                "error": str(e),
                "analysis_tasks": {},
                "analysis_results": {},
                "investment_strategy": {},
                "portfolio_optimization": {},
                "risk_assessment": {}
            }

    def _categorize_events(self, events: List[Dict]) -> Dict[str, List]:
        """将事件分类到不同的分析类型"""
        categorized = {analyst: [] for analyst in self.analysts.keys()}

        for event in events:
            event_types = self._classify_event_types(event)
            for event_type in event_types:
                if event_type in categorized:
                    categorized[event_type].append(event)

        return categorized

    def _classify_event_types(self, event: Dict) -> List[str]:
        """分类事件类型（一个事件可能属于多个类型）"""
        event_text = (event.get('core_event', '') + event.get('investment_implication', '')).lower()
        types = []

        # 政策相关
        policy_keywords = ['政策', '监管', '立法', '法规', '利率', '税收', '财政', '补贴', '央行']
        if any(keyword in event_text for keyword in policy_keywords):
            types.append('policy')

        # 宏观相关
        macro_keywords = ['gdp', 'cpi', 'ppi', '通胀', '通缩', '失业', '就业', '经济数据', 'pmi']
        if any(keyword in event_text for keyword in macro_keywords):
            types.append('macro')

        # 行业相关
        industry_keywords = ['行业', '板块', '财报', '盈利', '营收', '产能', '供应链', '技术']
        if any(keyword in event_text for keyword in industry_keywords):
            types.append('industry')

        # 市场相关
        market_keywords = ['市场', '情绪', '资金', '流动性', '波动', '技术面', '突破']
        if any(keyword in event_text for keyword in market_keywords):
            types.append('market')

        # 如果没有明确分类，默认分配到market
        if not types:
            types.append('market')

        return types

    def _execute_analysis(self, analysis_tasks: Dict[str, List]) -> Dict[str, Dict]:
        """执行分析任务"""
        analysis_results = {}

        for analyst_type, events in analysis_tasks.items():
            if events and analyst_type in self.analysts:
                logger.info(f"执行{analyst_type}分析，处理{len(events)}个事件")
                try:
                    result = self.analysts[analyst_type].analyze_events(events)
                    analysis_results[analyst_type] = result
                    logger.info(f"{analyst_type}分析完成，置信度: {result.get('confidence', 0)}")
                except Exception as e:
                    logger.error(f"{analyst_type}分析失败: {e}")
                    analysis_results[analyst_type] = {
                        "analysis_type": analyst_type,
                        "error": str(e),
                        "investment_thesis": "分析失败",
                        "confidence": 0.1
                    }
            else:
                logger.info(f"{analyst_type}无相关事件，跳过分析")

        return analysis_results

    def _optimize_portfolio(self, investment_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """执行组合优化"""
        logger.info("执行组合优化...")

        try:
            # 模拟当前持仓（在实际系统中可以从数据库获取）
            current_holdings = {
                "equities": {
                    "AAPL": "8%",
                    "MSFT": "7%",
                    "GOOGL": "5%",
                    "SPY": "15%"
                },
                "bonds": {
                    "TLT": "10%",
                    "IEF": "8%"
                },
                "cash": {
                    "CASH": "15%"
                }
            }

            # 模拟市场环境
            market_conditions = {
                "volatility": "中等",
                "liquidity": "充足",
                "sentiment": "谨慎乐观"
            }

            optimization_input = {
                "investment_strategy": investment_strategy,
                "current_holdings": current_holdings,
                "market_conditions": market_conditions
            }

            optimization_result = self.portfolio_optimizer.process(optimization_input)
            logger.info("组合优化完成")
            return optimization_result

        except Exception as e:
            logger.error(f"组合优化失败: {e}")
            return {
                "error": f"组合优化失败: {str(e)}",
                "optimization_type": "fallback",
                "target_allocation": {
                    "equities": {"target_weight": "60%"},
                    "bonds": {"target_weight": "30%"},
                    "cash": {"target_weight": "10%"}
                }
            }

    def _assess_risks(self, portfolio_optimization: Dict[str, Any],
                      investment_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """执行风险评估"""
        logger.info("执行风险评估...")

        try:
            risk_input = {
                "portfolio_data": portfolio_optimization,
                "investment_strategy": investment_strategy,
                "market_conditions": {
                    "volatility": "中等",
                    "sentiment": "谨慎乐观",
                    "systemic_risks": ["地缘政治风险", "通胀不确定性"]
                }
            }

            risk_result = self.risk_manager.process(risk_input)
            logger.info("风险评估完成")
            return risk_result

        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return {
                "error": f"风险评估失败: {str(e)}",
                "risk_assessment": {
                    "overall_risk_level": "中等"
                },
                "risk_controls": {
                    "stop_loss_strategy": {
                        "individual_positions": "个股下跌8%止损"
                    }
                }
            }

    def _generate_coordination_summary(self, analysis_tasks: Dict,
                                       analysis_results: Dict,
                                       portfolio_optimization: Dict,
                                       risk_assessment: Dict) -> str:
        """生成协调摘要"""
        summary = "## 协调执行摘要\n\n"

        # 任务分配情况
        summary += "### 任务分配\n"
        for analyst_type, events in analysis_tasks.items():
            summary += f"- {analyst_type}: {len(events)}个事件\n"

        # 分析结果概况
        summary += "\n### 分析结果\n"
        for analyst_type, result in analysis_results.items():
            confidence = result.get('confidence', 0)
            thesis = result.get('investment_thesis', '')[:50] + "..." if len(
                result.get('investment_thesis', '')) > 50 else result.get('investment_thesis', '')
            summary += f"- {analyst_type}: 置信度{confidence:.2f}, {thesis}\n"

        # 组合优化结果
        summary += "\n### 组合优化\n"
        allocation = portfolio_optimization.get('target_allocation', {})
        for asset_class, alloc in allocation.items():
            if isinstance(alloc, dict) and 'target_weight' in alloc:
                summary += f"- {asset_class}: {alloc['target_weight']}\n"

        # 风险评估结果
        summary += "\n### 风险评估\n"
        risk_level = risk_assessment.get('risk_assessment', {}).get('overall_risk_level', '未知')
        summary += f"- 总体风险等级: {risk_level}\n"

        return summary