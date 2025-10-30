from core.agents.analysis.base_analyst import BaseAnalyst
from typing import Dict, List, Any
import yaml


class MarketAnalyst(BaseAnalyst):
    def __init__(self):
        system_prompt = """你是一个顶级的市场分析师，具有深厚的技术分析和行为金融学背景。

你的专长包括：
1. 技术分析和图表模式识别
2. 市场情绪和资金流向分析
3. 市场微观结构和流动性分析
4. 行为金融学和市场心理学

请基于全面的市场分析，提供专业的市场时机建议。"""

        super().__init__("MarketAnalyst", system_prompt)
        self.framework = self._load_market_framework()
        # 定义必需输出字段
        self.required_output_fields = [
            "analysis_type", "investment_thesis", "time_horizon", "confidence"
        ]

    def _load_market_framework(self):
        """加载市场分析框架"""
        try:
            with open('config/analysis_frameworks.yaml', 'r') as f:
                return yaml.safe_load(f)['market_framework']
        except:
            return self._create_default_framework()

    def _create_default_framework(self):
        """创建默认市场框架"""
        return {
            "technical_analysis": ["趋势", "支撑阻力", "动量"],
            "sentiment_indicators": ["情绪", "仓位", "资金流"]
        }

    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """深度市场事件分析"""
        market_events = [e for e in events if self._is_market_related(e)]

        if not market_events:
            return self._create_default_analysis()

        return self.extract_investment_logic(market_events)

    def _is_market_related(self, event: Dict) -> bool:
        """判断是否为市场相关事件"""
        event_text = (event.get('core_event', '') + event.get('investment_implication', '')).lower()
        market_keywords = [
            '市场', '情绪', '资金', '流动性', '波动', '技术面', '突破', '支撑',
            '阻力', '成交量', '仓位', '杠杆', '恐慌', '贪婪', '超买', '超卖',
            '趋势', '反弹', '回调', '盘整', '牛市', '熊市', '调整', '反转'
        ]
        return any(keyword in event_text for keyword in market_keywords)

    def _build_analysis_prompt(self, events: List[Dict]) -> str:
        """构建深度市场分析提示词"""
        events_text = self._format_events_for_analysis(events)

        prompt = f"""
作为顶级市场分析师，请对以下市场事件进行深度分析：

{events_text}

请按照以下专业框架进行分析：

## 1. 技术分析
- 主要指数的趋势和关键技术水平
- 图表模式和形态识别
- 动量指标和震荡指标信号
- 成交量确认和背离分析

## 2. 市场情绪分析
- 投资者情绪指标和调查
- 仓位数据和资金流向
- 恐慌贪婪指数和市场广度
- 媒体情绪和社交网络情绪

## 3. 市场微观结构
- 流动性和交易成本分析
- 市场深度和买卖价差
- 机构和个人投资者行为
- 市场异常和套利机会

## 4. 市场周期定位
- 当前市场处于哪个周期阶段
- 周期转折点的技术信号
- 不同资产类别的轮动规律
- 历史相似周期的比较分析

## 5. 风险管理
- 关键技术支撑和阻力位
- 止损和止盈策略
- 仓位管理和风险暴露
- 市场冲击和黑天鹅防护

请严格按照以下JSON格式输出深度分析结果：
{{
    "analysis_type": "market",
    "technical_analysis": {{
        "trend_assessment": "趋势评估",
        "key_levels": {{
            "support": ["支撑位1", "支撑位2"],
            "resistance": ["阻力位1", "阻力位2"]
        }},
        "chart_patterns": ["图表模式1", "模式2"],
        "momentum_indicators": {{
            "rsi": "RSI状态",
            "macd": "MACD信号",
            "stochastic": "随机指标"
        }},
        "volume_analysis": "成交量分析"
    }},
    "market_sentiment": {{
        "sentiment_indicators": {{
            "vix": "VIX水平",
            "put_call_ratio": "看跌看涨比率",
            "bull_bear_spread": "牛熊利差"
        }},
        "positioning_data": "仓位数据",
        "fund_flows": "资金流向",
        "overall_sentiment": "整体情绪"
    }},
    "market_regime": {{
        "current_regime": "当前市场状态",
        "regime_strength": "状态强度",
        "regime_duration": "状态持续时间",
        "transition_signals": ["转换信号1", "信号2"]
    }},
    "trading_signals": [
        {{
            "asset": "资产",
            "signal": "买入/卖出/持有",
            "timeframe": "时间框架",
            "entry_level": "入场位",
            "stop_loss": "止损位",
            "target": "目标位",
            "confidence": "信号置信度"
        }}
    ],
    "risk_management": {{
        "market_volatility": "市场波动率",
        "correlation_analysis": "相关性分析",
        "position_sizing": "仓位规模建议",
        "hedging_recommendations": ["对冲建议1", "建议2"]
    }},
    "market_outlook": {{
        "base_case_scenario": "基准情景",
        "alternative_scenarios": ["替代情景1", "情景2"],
        "catalyst_watch": ["催化剂1", "催化剂2"]
    }},
    "key_technical_levels": ["关键技术位1", "技术位2"],
    "confidence_score": 0.0-1.0,
    "market_timing_conviction": "高/中/低"
}}

要求：分析要基于具体的技术指标和市场数据，交易建议要有明确的技术逻辑支撑。
分析禁令：
⚠️ 禁止空泛结论
⚠️ 禁止脱离新闻数据
⚠️ 禁止忽视政策市特征
"""
        return prompt

    def _format_events_for_analysis(self, events: List[Dict]) -> str:
        """格式化事件用于分析"""
        formatted = []

        for i, event in enumerate(events):
            # 提取市场相关关键词
            content = event.get('content', '')
            market_terms = self._extract_market_terms(content)

            formatted.append(f"事件{i + 1}: {event.get('core_event', '')}")
            formatted.append(f"市场影响: {event.get('investment_implication', '未知')}")
            if market_terms:
                formatted.append(f"市场关键词: {', '.join(market_terms)}")
            formatted.append("")

        return "\n".join(formatted)

    def _extract_market_terms(self, text: str) -> List[str]:
        """提取市场相关术语"""
        market_terms = [
            '上涨', '下跌', '反弹', '回调', '突破', '跌破', '支撑', '阻力',
            '放量', '缩量', '金叉', '死叉', '超买', '超卖', '背离', '共振',
            '牛市', '熊市', '震荡', '趋势', '动量', '波动', '仓位', '杠杆'
        ]

        found_terms = []
        for term in market_terms:
            if term in text:
                found_terms.append(term)

        return found_terms[:5]

    def _create_default_analysis(self) -> Dict[str, Any]:
        """创建默认市场分析 - 确保包含必需字段"""
        return {
            "analysis_type": "market",
            "investment_thesis": "市场情绪平稳，技术面中性",
            "time_horizon": "short",
            "confidence": 0.5,
            "technical_analysis": {
                "trend_assessment": "需要更多数据",
                "key_levels": {
                    "support": ["待确定"],
                    "resistance": ["待确定"]
                }
            },
            "trading_signals": [
                {
                    "asset": "主要指数",
                    "signal": "持有",
                    "timeframe": "短期",
                    "confidence": "中等"
                }
            ],
            "market_timing_conviction": "低"
        }