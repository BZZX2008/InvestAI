#!/usr/bin/env python3
"""
快速验证脚本 - 最小化测试
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_basic_instantiation():
    """测试基础实例化"""
    print("🔧 测试基础实例化...")

    try:
        from core.agents.analysis_team.policy_analyst import PolicyAnalyst
        policy = PolicyAnalyst()
        print("✅ PolicyAnalyst 实例化成功")

        from core.agents.analysis_team.macro_analyst import MacroAnalyst
        macro = MacroAnalyst()
        print("✅ MacroAnalyst 实例化成功")

        from core.agents.analysis_team.industry_analyst import IndustryAnalyst
        industry = IndustryAnalyst()
        print("✅ IndustryAnalyst 实例化成功")

        from core.agents.analysis_team.market_analyst import MarketAnalyst
        market = MarketAnalyst()
        print("✅ MarketAnalyst 实例化成功")

        from core.agents.decision_team.strategy_synthesizer import StrategySynthesizer
        synthesizer = StrategySynthesizer()
        print("✅ StrategySynthesizer 实例化成功")

        return True

    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_availability():
    """测试方法可用性"""
    print("\n🔧 测试方法可用性...")

    try:
        from core.agents.analysis_team.policy_analyst import PolicyAnalyst
        policy = PolicyAnalyst()

        # 测试必需方法
        test_events = [{"core_event": "测试事件"}]

        result = policy.process(test_events)
        print("✅ process() 方法可用")

        result2 = policy.analyze_events(test_events)
        print("✅ analyze_events() 方法可用")

        return True

    except Exception as e:
        print(f"❌ 方法测试失败: {e}")
        return False


if __name__ == "__main__":
    print("快速验证抽象类修复")
    print("=" * 40)

    success1 = test_basic_instantiation()
    success2 = test_method_availability()

    if success1 and success2:
        print("\n🎉 所有测试通过！架构修复成功。")
        print("\n现在可以运行: python test_phase2_fixed.py")
    else:
        print("\n💥 测试失败，需要进一步调试。")
