#!/usr/bin/env python3
"""Complete automation setup for investment cockpit."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.setup_cron import setup_cron
from scripts.init_feishu_tables import init_all_tables
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """Setup complete automation."""
    print("="*60)
    print("投资驾驶舱自动化配置")
    print("="*60)
    
    # Step 1: Initialize Feishu tables
    print("\n[1/2] 初始化飞书多维表格...")
    try:
        init_all_tables()
        print("✓ 飞书表格初始化完成")
    except Exception as e:
        print(f"✗ 飞书表格初始化失败: {e}")
        logger.error("Feishu initialization failed", exc_info=True)
    
    # Step 2: Setup cron jobs
    print("\n[2/2] 配置定时任务...")
    try:
        cron_content = setup_cron()
        print("✓ 定时任务配置完成")
        print("\n已配置的定时任务:")
        for line in cron_content.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"  {line}")
    except Exception as e:
        print(f"✗ 定时任务配置失败: {e}")
        logger.error("Cron setup failed", exc_info=True)
    
    # Summary
    print("\n" + "="*60)
    print("自动化配置完成")
    print("="*60)
    print("\n自动化任务时间表:")
    print("  • 09:15 工作日 - 早盘推荐 (morning_task.py)")
    print("  • 12:30 工作日 - 午盘决策 (midday_task.py)")
    print("  • 20:00 每天   - 每日任务 (daily_task.py)")
    print("    - 更新数据")
    print("    - 计算因子")
    print("    - 更新信号表现追踪")
    print("    - 生成策略信号")
    print("    - 同步飞书 (8张表)")
    print("    - 发送飞书通知")
    print("  • 21:00 工作日 - 参数监控 (monitor_parameters.py)")
    print("  • 21:00 周日   - 周报生成 (weekly_report.py)")
    print("  • 22:00 周日   - 参数优化 (weekly_optimization.py)")
    
    print("\n飞书多维表格 (8张表):")
    print("  1. 真实持仓 - 当前持仓明细")
    print("  2. 交易记录 - 历史交易流水")
    print("  3. 每日信号 - 策略推荐 (含买卖点)")
    print("  4. 股票池   - 观察池管理")
    print("  5. 信号表现追踪 - 推荐实时表现")
    print("  6. 每日策略表现 - 胜率/盈亏比统计")
    print("  7. 周度复盘 - 每周总结")
    print("  8. 参数优化历史 - 参数迭代记录")
    
    print("\n下一步:")
    print("  1. 在飞书多维表格中创建仪表盘")
    print("  2. 添加图表可视化:")
    print("     - 持仓分布饼图")
    print("     - 收益率趋势折线图")
    print("     - 策略胜率对比柱状图")
    print("     - 信号表现热力图")
    print("  3. 等待定时任务自动执行")
    print("\n所有流程已完全自动化！")


if __name__ == "__main__":
    main()
