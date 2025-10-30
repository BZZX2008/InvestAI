#!/usr/bin/env python3
"""
投资分析系统启动脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import OptimizedInvestmentSystem


def main():
    """主函数"""
    print("🚀 启动AI投资分析系统...")
    print("=" * 50)

    try:
        system = OptimizedInvestmentSystem()
        system.run()
        print("\n✅ 系统执行完成！")

    except KeyboardInterrupt:
        print("\n⏹️ 用户中断执行")
    except Exception as e:
        print(f"\n❌ 系统执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()