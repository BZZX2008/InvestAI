from core.agents.analysis.base_analyst import BaseAnalyst
from typing import Dict, List, Any
import yaml


class IndustryAnalyst(BaseAnalyst):
    def __init__(self):
        system_prompt = """你是一个顶级的行业分析师，具有深厚的产业研究和公司分析背景。

你的专长包括：
1. 行业生命周期和竞争格局分析
2. 公司基本面和估值分析
3. 行业趋势和颠覆性技术识别
4. 产业链和价值链分析

请基于深入的行业研究，提供专业的投资洞察。"""

        super().__init__("IndustryAnalyst", system_prompt)
        self.framework = self._load_industry_framework()
        # 定义必需输出字段
        self.required_output_fields = [
            "analysis_type", "investment_thesis", "time_horizon", "confidence"
        ]

    def _load_industry_framework(self):
        """加载行业分析框架"""
        try:
            with open('config/analysis_frameworks.yaml', 'r') as f:
                return yaml.safe_load(f)['industry_framework']
        except:
            return self._create_default_framework()

    def _create_default_framework(self):
        """创建默认行业框架"""
        return {
            "analysis_dimensions": [
                "行业前景", "竞争格局", "盈利能力", "增长驱动"
            ]
        }

    def analyze_events(self, events: List[Dict]) -> Dict[str, Any]:
        """深度行业事件分析"""
        industry_events = [e for e in events if self._is_industry_related(e)]

        if not industry_events:
            return self._create_default_analysis()

        return self.extract_investment_logic(industry_events)

    def _is_industry_related(self, event: Dict) -> bool:
        """判断是否为行业相关事件"""
        event_text = (event.get('core_event', '') + event.get('investment_implication', '')).lower()
        industry_keywords = [
            '行业', '板块', '财报', '盈利', '营收', '利润', '毛利率', '净利率',
            '产能', '供应链', '技术', '创新', '竞争', '市场份额', '龙头', '细分',
            '需求', '供给', '库存', '价格', '成本', '扩张', '收缩', '转型'
        ]
        return any(keyword in event_text for keyword in industry_keywords)

    def _build_analysis_prompt(self, events: List[Dict]) -> str:
        """构建深度行业分析提示词"""
        events_text = self._format_events_for_analysis(events)

        prompt = f"""
作为顶级行业分析师，请对以下行业事件进行深度分析：

{events_text}

请按照以下专业框架进行分析：

## 1. 行业基本面分析
- 行业生命周期阶段判断
- 市场规模和增长前景
- 盈利能力和现金流特征
- 资本开支和回报周期

## 2. 竞争格局分析
- 市场集中度和进入壁垒
- 主要竞争者的战略定位
- 定价能力和成本结构
- 差异化优势和护城河

## 3. 增长驱动分析
- 需求驱动因素和可持续性
- 供给端约束和产能周期
- 技术变革和颠覆性创新
- 政策和监管环境影响

## 4. 估值和风险评估
- 相对估值和绝对估值
- 盈利质量和可持续性
- 资产负债表健康状况
- 行业特定风险因素

## 5. 投资机会识别
- 结构性增长机会
- 周期性复苏机会
- 估值修复机会
- 事件驱动机会


请严格按照以下JSON格式输出深度分析结果：
{{
    "analysis_type": "industry",
    "industry_fundamentals": {{
        "lifecycle_stage": "生命周期阶段",
        "market_size_growth": "市场规模和增长",
        "profitability_profile": "盈利能力特征",
        "cash_flow_characteristics": "现金流特征"
    }},
    "competitive_analysis": {{
        "market_structure": "市场结构",
        "key_players": [
            {{
                "company": "公司名称",
                "market_share": "市场份额",
                "competitive_advantage": "竞争优势"
            }}
        ],
        "barriers_to_entry": "进入壁垒",
        "pricing_power": "定价能力"
    }},
    "growth_drivers": {{
        "demand_factors": ["需求因素1", "需求因素2"],
        "supply_dynamics": "供给动态",
        "technological_innovation": "技术创新",
        "regulatory_environment": "监管环境"
    }},
    "valuation_assessment": {{
        "relative_valuation": {{
            "metric": "估值指标",
            "vs_history": "与历史比较",
            "vs_peers": "与同行比较"
        }},
        "absolute_valuation": "绝对估值分析",
        "earnings_quality": "盈利质量",
        "balance_sheet_health": "资产负债表健康度"
    }},
    "investment_opportunities": [
        {{
            "opportunity_type": "机会类型",
            "specific_companies": ["具体公司"],
            "investment_thesis": "投资逻辑",
            "time_horizon": "时间框架",
            "risk_reward": "风险收益特征"
        }}
    ],
    "sector_allocation": {{
        "overweight_sectors": [
            {{
                "sector": "行业",
                "weighting": "配置权重",
                "rationale": "配置理由"
            }}
        ],
        "underweight_sectors": [
            {{
                "sector": "行业",
                "rationale": "低配理由"
            }}
        ]
    }},
    "key_risks": ["关键风险1", "风险2"],
    "monitoring_metrics": ["监控指标1", "指标2"],
    "confidence_score": 0.0-1.0,
    "conviction_level": "高/中/低"
}}

要求：分析要深入具体，引用行业数据和公司信息，投资建议要有明确的行业逻辑支撑。
分析禁令：
⚠️ 禁止空泛结论
⚠️ 禁止脱离新闻数据

"""
        return prompt

    def _format_events_for_analysis(self, events: List[Dict]) -> str:
        """格式化事件用于分析"""
        # 按行业分类事件
        sector_events = self._categorize_by_sector(events)

        formatted = ["## 行业事件汇总"]
        for sector, sector_events in sector_events.items():
            formatted.append(f"\n### {sector}行业")
            for i, event in enumerate(sector_events):
                formatted.append(f"{i + 1}. {event.get('core_event', '')}")
                companies = self._extract_companies(event.get('content', ''))
                if companies:
                    formatted.append(f"   涉及公司: {', '.join(companies)}")

        return "\n".join(formatted)

    def _categorize_by_sector(self, events: List[Dict]) -> Dict[str, List]:
        """按行业分类事件"""
        sectors = {
            '科技': ['科技', '互联网', '软件', '硬件', '半导体', '人工智能', '云计算'],
            '金融': ['金融', '银行', '保险', '证券', '券商', '支付', '金融科技'],
            '医疗': ['医疗', '医药', '生物', '器械', '健康', '制药', '医院'],
            '消费': ['消费', '零售', '食品', '饮料', '汽车', '家电', '旅游'],
            '能源': ['能源', '石油', '天然气', '电力', '新能源', '光伏', '风电'],
            '工业': ['工业', '制造', '机械', '化工', '材料', '建筑', '基建']
        }

        categorized = {sector: [] for sector in sectors.keys()}
        categorized['其他'] = []

        for event in events:
            content = (event.get('core_event', '') + event.get('content', '')).lower()
            matched = False

            for sector, keywords in sectors.items():
                if any(keyword in content for keyword in keywords):
                    categorized[sector].append(event)
                    matched = True
                    break

            if not matched:
                categorized['其他'].append(event)

        # 移除空行业
        return {k: v for k, v in categorized.items() if v}

    def _extract_companies(self, text: str) -> List[str]:
        """提取文本中提到的公司"""
        import re
        # 常见公司名称模式
        company_patterns = [
            r'([A-Z]{2,4})',  # 股票代码
            r'([a-zA-Z]+公司)',  # XX公司
            r'([a-zA-Z]+集团)',  # XX集团
        ]

        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)

        return list(set(companies))[:5]  # 去重并返回前5个

    def _create_default_analysis(self) -> Dict[str, Any]:
        """创建默认行业分析 - 确保包含必需字段"""
        return {
            "analysis_type": "industry",
            "investment_thesis": "各行业表现分化，关注结构性机会",
            "time_horizon": "mid",
            "confidence": 0.6,
            "investment_opportunities": [
                {
                    "opportunity_type": "结构性增长",
                    "specific_companies": ["行业龙头"],
                    "investment_thesis": "关注行业龙头和结构性增长机会",
                    "time_horizon": "长期",
                    "risk_reward": "中等"
                }
            ],
            "conviction_level": "中"
        }