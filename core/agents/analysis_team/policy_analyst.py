from core.agents.analysis.base_analyst import BaseAnalyst
from typing import Dict, List, Any
import yaml


class PolicyAnalyst(BaseAnalyst):
    def __init__(self):
        system_prompt = """你是一个顶级的政策分析专家，具有深厚的经济学和公共政策背景。

你的专长包括：
1. 货币政策分析（利率政策、量化宽松、信贷政策等）
2. 财政政策分析（税收政策、政府支出、财政刺激等） 
3. 监管政策分析（金融监管、行业规范、反垄断等）
4. 产业政策分析（补贴政策、技术标准、国产替代等）

请基于政策经济学原理，提供深度的政策影响分析。"""

        super().__init__("PolicyAnalyst", system_prompt)
        self.framework = self._load_policy_framework()
        # 定义必需输出字段
        self.required_output_fields = [
            "analysis_type", "investment_thesis", "time_horizon", "confidence"
        ]


    def _load_policy_framework(self):
        """加载政策分析框架"""
        try:
            with open('config/analysis_frameworks.yaml', 'r') as f:
                return yaml.safe_load(f)['policy_framework']
        except:
            return self._create_default_framework()

    def _create_default_framework(self):
        """创建默认政策框架"""
        return {
            "analysis_dimensions": [
                "政策意图", "传导机制", "影响范围", "时间框架"
            ]
        }


    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """深度政策事件分析"""
        policy_events = [e for e in events if self._is_policy_related(e)]

        if not policy_events:
            return self._create_default_analysis()

        return self.extract_investment_logic(policy_events)


    def _is_policy_related(self, event: Dict) -> bool:
        """判断是否为政策相关事件"""
        event_text = (event.get('core_event', '') + event.get('investment_implication', '')).lower()
        policy_keywords = [
            '政策', '监管', '立法', '法规', '利率', '准备金', '税收', '财政',
            '补贴', '央行', '证监会', '银保监', '发改委', '国务院', '政治局',
            '货币政策', '财政政策', '产业政策', '监管政策', '指导意见', '实施细则'
        ]
        return any(keyword in event_text for keyword in policy_keywords)


    def _build_analysis_prompt(self, events: List[Dict]) -> str:
        """构建深度政策分析提示词"""
        events_text = self._format_events_for_analysis(events)

        prompt = f"""
作为顶级政策分析专家，请对以下政策事件进行深度分析：

{events_text}

请按照以下专业框架进行分析：

## 1. 政策意图分析
- 政策出台的背景和目的
- 要解决的核心问题
- 政策的优先级和紧迫性

## 2. 传导机制分析  
- 政策如何影响实体经济
- 金融市场的传导路径
- 对各类资产的影响机制

## 3. 受益方与受损方分析
- 直接受益的行业和公司
- 间接受益的领域
- 可能受损的行业和公司
- 对消费者的影响

## 4. 时间框架分析
- 政策的立即影响（1-7天）
- 短期影响（1-3个月） 
- 中期影响（3-12个月）
- 长期结构性影响（1年以上）

## 5. 风险评估
- 政策执行的不确定性
- 可能的意外后果
- 与其他政策的相互作用

请严格按照以下JSON格式输出深度分析结果：
{{
    "analysis_type": "policy",
    "policy_intent": {{
        "background": "政策背景分析",
        "objectives": ["目标1", "目标2"],
        "urgency_level": "高/中/低"
    }},
    "transmission_mechanism": {{
        "economic_impact": "对实体经济的影响路径",
        "financial_impact": "对金融市场的影响路径",
        "asset_price_channels": ["影响资产价格的渠道1", "渠道2"]
    }},
    "winners_losers_analysis": {{
        "direct_beneficiaries": [
            {{
                "sector": "行业",
                "companies": ["公司1", "公司2"],
                "rationale": "受益逻辑"
            }}
        ],
        "indirect_beneficiaries": [
            {{
                "sector": "行业", 
                "rationale": "间接受益逻辑"
            }}
        ],
        "adversely_affected": [
            {{
                "sector": "行业",
                "rationale": "受损逻辑"
            }}
        ]
    }},
    "time_horizon_impact": {{
        "immediate_1_7_days": "立即影响分析",
        "short_term_1_3_months": "短期影响分析",
        "medium_term_3_12_months": "中期影响分析", 
        "long_term_1_plus_years": "长期影响分析"
    }},
    "investment_recommendations": [
        {{
            "asset_class": "资产类别",
            "specific_assets": ["具体标的"],
            "timeframe": "投资时间框架",
            "conviction_level": "高/中/低",
            "rationale": "投资逻辑"
        }}
    ],
    "risk_assessment": {{
        "execution_risk": "执行风险",
        "unintended_consequences": "意外后果",
        "policy_interactions": "政策相互作用风险"
    }},
    "monitoring_indicators": ["需要监控的指标1", "指标2"],
    "confidence_score": 0.0-1.0,
    "key_insights": ["核心洞察1", "核心洞察2"]
}}

要求：分析要深入专业，引用经济学原理，投资建议要具体可执行。
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
            formatted.append(f"事件{i + 1}: {event.get('core_event', '')}")
            formatted.append(f"原始内容: {event.get('content', '')[:200]}...")
            formatted.append(f"影响级别: {event.get('impact_level', '未知')}")
            formatted.append("")

        return "\n".join(formatted)


    def _create_default_analysis(self) -> Dict[str, Any]:
        """创建默认政策分析 - 确保包含必需字段"""
        return {
            "analysis_type": "policy",
            "investment_thesis": "当前政策环境相对稳定，建议关注常规政策执行",
            "time_horizon": "mid",
            "confidence": 0.6,
            "policy_intent": {
                "background": "政策环境稳定",
                "objectives": ["维持经济稳定"],
                "urgency_level": "低"
            },
            "investment_recommendations": [
                {
                    "asset_class": "政策敏感型资产",
                    "specific_assets": ["金融股"],
                    "timeframe": "中期",
                    "conviction_level": "中",
                    "rationale": "等待更明确的政策信号"
                }
            ],
            "key_insights": ["政策真空期，关注常规政策执行"]
        }