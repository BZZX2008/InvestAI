from core.agents.analysis.base_analyst import BaseAnalyst
from typing import Dict, List, Any
import yaml


class MacroAnalyst(BaseAnalyst):
    def __init__(self):
        system_prompt = """你是一个顶级的宏观经济分析师，具有深厚的经济学理论和实证研究背景。

你的专长包括：
1. 经济周期分析和预测
2. 通货膨胀动态和货币政策互动
3. 全球宏观经济联动分析
4. 资产配置的宏观经济基础

请基于宏观经济理论和实证证据，提供深度的宏观分析。"""

        super().__init__("MacroAnalyst", system_prompt)
        self.framework = self._load_macro_framework()
        # 定义必需输出字段
        self.required_output_fields = [
            "analysis_type", "investment_thesis", "time_horizon", "confidence"
        ]

    def _load_macro_framework(self):
        """加载宏观分析框架"""
        try:
            with open('config/analysis_frameworks.yaml', 'r') as f:
                return yaml.safe_load(f)['macro_framework']
        except:
            return self._create_default_framework()

    def _create_default_framework(self):
        """创建默认宏观框架"""
        return {
            "economic_cycles": ["复苏", "扩张", "滞胀", "衰退"],
            "key_indicators": ["GDP", "CPI", "失业率"]
        }

    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """深度宏观事件分析"""
        macro_events = [e for e in events if self._is_macro_related(e)]

        if not macro_events:
            return self._create_default_analysis()

        return self.extract_investment_logic(macro_events)

    def _is_macro_related(self, event: Dict) -> bool:
        """判断是否为宏观相关事件"""
        event_text = (event.get('core_event', '') + event.get('investment_implication', '')).lower()
        macro_keywords = [
            'gdp', 'cpi', 'ppi', 'pce', 'pmi', '通胀', '通缩', '失业', '就业',
            '经济数据', '工业产值', '零售销售', '消费者信心', '制造业', '服务业',
            '贸易数据', '经常账户', '财政赤字', '货币供应', '社融', '信贷'
        ]
        return any(keyword in event_text for keyword in macro_keywords)

    def _build_analysis_prompt(self, events: List[Dict]) -> str:
        """构建深度宏观分析提示词"""
        events_text = self._format_events_for_analysis(events)

        prompt = f"""
作为顶级宏观经济分析师，请对以下宏观经济事件进行深度分析：

{events_text}

请按照以下专业框架进行分析：

## 1. 经济周期定位
- 当前经济处于哪个周期阶段
- 周期转折点的领先指标信号
- 周期持续性和强度评估

## 2. 增长-通胀动态
- 经济增长的动力和阻力
- 通货膨胀的驱动因素
- 增长-通胀组合的资产配置含义

## 3. 货币政策展望
- 央行政策立场和未来路径
- 利率和流动性环境
- 对各类资产的估值影响

## 4. 全球宏观联动
- 主要经济体的周期差异
- 汇率和资本流动影响
- 全球风险情绪的传导

## 5. 资产配置策略
- 基于宏观环境的资产轮动
- 风险溢价和估值评估
- 战术配置和战略配置建议

请严格按照以下JSON格式输出深度分析结果：
{{
    "analysis_type": "macro",
    "economic_cycle_assessment": {{
        "current_phase": "周期阶段",
        "leading_indicators": ["领先指标1", "领先指标2"],
        "cycle_strength": "强/中/弱",
        "duration_outlook": "周期持续时间预期"
    }},
    "growth_inflation_analysis": {{
        "growth_drivers": ["增长驱动1", "增长驱动2"],
        "inflation_dynamics": "通胀动态分析",
        "output_gap": "产出缺口状态",
        "growth_inflation_regime": "增长-通胀组合类型"
    }},
    "monetary_policy_outlook": {{
        "central_bank_stance": "央行立场",
        "policy_trajectory": "政策路径预期",
        "liquidity_conditions": "流动性状况",
        "real_rates_outlook": "实际利率展望"
    }},
    "global_context": {{
        "cycle_divergence": "周期分化情况",
        "currency_implications": "汇率影响",
        "capital_flows": "资本流动趋势"
    }},
    "asset_allocation_framework": {{
        "strategic_allocation": {{
            "equities": "战略股票配置",
            "bonds": "战略债券配置",
            "commodities": "战略商品配置",
            "cash": "战略现金配置"
        }},
        "tactical_opportunities": [
            {{
                "asset_class": "资产类别",
                "overweight_underweight": "超配/低配",
                "timeframe": "时间框架",
                "rationale": "战术逻辑"
            }}
        ]
    }},
    "risk_scenarios": {{
        "base_case": {{
            "probability": "概率",
            "macro_outlook": "宏观前景",
            "asset_implications": "资产含义"
        }},
        "upside_case": {{
            "probability": "概率", 
            "macro_outlook": "宏观前景",
            "asset_implications": "资产含义"
        }},
        "downside_case": {{
            "probability": "概率",
            "macro_outlook": "宏观前景", 
            "asset_implications": "资产含义"
        }}
    }},
    "key_macro_signals": ["关键宏观信号1", "信号2"],
    "confidence_score": 0.0-1.0,
    "investment_thesis": "基于宏观环境的投资核心理念"
}}

要求：分析要基于宏观经济理论，引用具体数据和指标，投资建议要有明确的宏观逻辑支撑。
分析禁令：
⚠️ 禁止空泛结论
⚠️ 禁止脱离新闻数据

"""
        return prompt

    def _format_events_for_analysis(self, events: List[Dict]) -> str:
        """格式化事件用于分析"""
        formatted = []
        for i, event in enumerate(events):
            # 提取可能的数值信息
            content = event.get('content', '')
            numbers = self._extract_numbers(content)

            formatted.append(f"事件{i + 1}: {event.get('core_event', '')}")
            formatted.append(f"数据内容: {content[:300]}...")
            if numbers:
                formatted.append(f"关键数值: {numbers}")
            formatted.append(f"时间框架: {event.get('time_horizon', '未知')}")
            formatted.append("")

        return "\n".join(formatted)

    def _extract_numbers(self, text: str) -> List[str]:
        """提取文本中的数值信息"""
        import re
        # 匹配百分比、数值等
        patterns = [
            r'(\d+\.?\d*)%',  # 百分比
            r'[+-]?\d+\.?\d*',  # 数值
            r'[一二三四五六七八九十]+倍',  # 倍数
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)

        return numbers[:5]  # 返回前5个数值

    def _create_default_analysis(self) -> Dict[str, Any]:
        """创建默认宏观分析 - 确保包含必需字段"""
        return {
            "analysis_type": "macro",
            "investment_thesis": "宏观经济环境相对稳定，建议均衡配置",
            "time_horizon": "mid",
            "confidence": 0.6,
            "economic_cycle_assessment": {
                "current_phase": "数据不足，无法确定",
                "cycle_strength": "中等"
            },
            "asset_allocation_framework": {
                "strategic_allocation": {
                    "equities": "中性",
                    "bonds": "中性",
                    "cash": "中性"
                }
            }
        }