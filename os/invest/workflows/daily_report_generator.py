#!/usr/bin/env python3
"""
Daily Report Generator - 日报生成系统
自动生成每日投资报告
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


def generate_daily_report(
    date: str,
    portfolio_summary: Dict[str, Any],
    performance: Dict[str, Any],
    holdings: List[Dict[str, Any]],
    trades: List[Dict[str, Any]]
) -> str:
    """生成日报"""

    report_lines = [
        f"# 投资日报 {date}",
        "",
        "## 📊 账户概况",
        "",
        f"- **总市值**: {portfolio_summary['total_value']/10000:.2f}万",
        f"- **可用资金**: {portfolio_summary.get('cash', 0)/10000:.2f}万",
        f"- **持仓数**: {len(holdings)}",
        "",
        "## 📈 今日表现",
        "",
        f"- **今日盈亏**: {performance['pnl']/10000:.2f}万",
        f"- **收益率**: {performance['return']:.2f}%",
        f"- **累计收益率**: {performance.get('total_return', 0):.2f}%",
        "",
        "## 🏆 涨幅前3",
        ""
    ]

    top_gainers = sorted(holdings, key=lambda x: x.get('change', 0), reverse=True)[:3]
    for i, holding in enumerate(top_gainers, 1):
        report_lines.append(f"{i}. **{holding['symbol']}** {holding['name']}: +{holding['change']:.2f}%")

    report_lines.extend([
        "",
        "## 📉 跌幅前3",
        ""
    ])

    top_losers = sorted(holdings, key=lambda x: x.get('change', 0))[:3]
    for i, holding in enumerate(top_losers, 1):
        report_lines.append(f"{i}. **{holding['symbol']}** {holding['name']}: {holding['change']:.2f}%")

    if trades:
        report_lines.extend([
            "",
            "## 💰 今日交易",
            ""
        ])
        for trade in trades:
            report_lines.append(f"- {trade['action']} {trade['symbol']} {trade['shares']}股 @ {trade['price']}")

    report_lines.extend([
        "",
        "## 📌 风险提示",
        ""
    ])

    if portfolio_summary.get('concentration', 0) > 60:
        report_lines.append("- ⚠️ 持仓集中度较高")

    if performance['pnl'] < 0:
        report_lines.append("- ⚠️ 今日亏损，注意风险")

    report_lines.extend([
        "",
        f"---",
        f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    ])

    return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description='Daily Report Generator - 日报生成')
    parser.add_argument('--action', default='generate', choices=['generate', 'preview'],
                        help='操作类型')
    parser.add_argument('--output', help='输出路径')

    args = parser.parse_args()

    print("🚀 Daily Report Generator 启动...")
    print()

    # 示例数据
    portfolio = {'total_value': 1020000, 'cash': 20000}
    performance = {'pnl': 20000, 'return': 2.0, 'total_return': 15.5}
    holdings = [
        {'symbol': '600000', 'name': '浦发银行', 'change': 5.2},
        {'symbol': '000001', 'name': '平安银行', 'change': -2.1},
        {'symbol': '600036', 'name': '招商银行', 'change': 3.5}
    ]
    trades = [
        {'action': '买入', 'symbol': '600000', 'shares': 100, 'price': 10.5}
    ]

    report = generate_daily_report(
        datetime.now().strftime('%Y-%m-%d'),
        portfolio,
        performance,
        holdings,
        trades
    )

    print("=" * 60)
    print("📊 日报预览")
    print("=" * 60)
    print()
    print(report)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ 日报已保存: {args.output}")

    print("\n✅ Daily Report Generator 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
