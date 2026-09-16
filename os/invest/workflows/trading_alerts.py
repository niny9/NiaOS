#!/usr/bin/env python3
"""
Trading Alerts - 三时段提醒系统
开盘前/盘中/收盘前提醒机制
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, time
import re


def load_alert_config(config_path: str) -> Dict[str, Any]:
    """加载提醒配置"""
    if not os.path.exists(config_path):
        return {
            "enabled": True,
            "alert_times": {
                "pre_market": "08:30",
                "mid_trading": "11:00,14:00",
                "pre_close": "14:45"
            },
            "alert_channels": ["feishu", "email"],
            "priority_rules": {}
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_pre_market_alert(
    date: str,
    market_overview: Dict[str, Any],
    portfolio_summary: Dict[str, Any],
    key_events: List[str]
) -> Dict[str, Any]:
    """生成开盘前提醒"""

    alert = {
        "type": "pre_market",
        "time": "08:30",
        "title": f"📊 开盘前准备 {date}",
        "priority": "high",
        "sections": []
    }

    # 市场概况
    alert["sections"].append({
        "title": "🌍 市场概况",
        "content": [
            f"A股指数: {market_overview.get('index', 'N/A')}",
            f"隔夜美股: {market_overview.get('us_market', 'N/A')}",
            f"市场情绪: {market_overview.get('sentiment', '中性')}"
        ]
    })

    # 持仓概况
    alert["sections"].append({
        "title": "💼 持仓概况",
        "content": [
            f"总市值: {portfolio_summary.get('total_value', 0)/10000:.2f}万",
            f"持仓数: {portfolio_summary.get('holdings_count', 0)}",
            f"昨日盈亏: {portfolio_summary.get('yesterday_pnl', 0)/10000:.2f}万"
        ]
    })

    # 关键事件
    if key_events:
        alert["sections"].append({
            "title": "📢 今日关键事件",
            "content": key_events
        })

    # 行动建议
    alert["sections"].append({
        "title": "💡 今日建议",
        "content": [
            "✅ 关注重点持仓表现",
            "⚠️ 注意风险控制",
            "📊 准备好交易计划"
        ]
    })

    return alert


def generate_mid_trading_alert(
    current_time: str,
    portfolio_status: Dict[str, Any],
    alerts: List[str]
) -> Dict[str, Any]:
    """生成盘中提醒"""

    alert = {
        "type": "mid_trading",
        "time": current_time,
        "title": f"🔔 盘中提醒 {current_time}",
        "priority": "medium",
        "sections": []
    }

    # 实时状态
    alert["sections"].append({
        "title": "📈 实时状态",
        "content": [
            f"当前市值: {portfolio_status.get('current_value', 0)/10000:.2f}万",
            f"今日盈亏: {portfolio_status.get('today_pnl', 0)/10000:.2f}万",
            f"收益率: {portfolio_status.get('today_return', 0):.2f}%"
        ]
    })

    # 风险提示
    if alerts:
        alert["sections"].append({
            "title": "⚠️ 风险提示",
            "content": alerts
        })
        alert["priority"] = "high"

    return alert


def generate_pre_close_alert(
    date: str,
    portfolio_summary: Dict[str, Any],
    today_performance: Dict[str, Any],
    pending_actions: List[str]
) -> Dict[str, Any]:
    """生成收盘前提醒"""

    alert = {
        "type": "pre_close",
        "time": "14:45",
        "title": f"⏰ 收盘前检查 {date}",
        "priority": "high",
        "sections": []
    }

    # 今日表现
    alert["sections"].append({
        "title": "📊 今日表现",
        "content": [
            f"今日盈亏: {today_performance.get('pnl', 0)/10000:.2f}万",
            f"收益率: {today_performance.get('return', 0):.2f}%",
            f"最佳持仓: {today_performance.get('top_gainer', 'N/A')}",
            f"最差持仓: {today_performance.get('top_loser', 'N/A')}"
        ]
    })

    # 待办事项
    if pending_actions:
        alert["sections"].append({
            "title": "✅ 待办事项",
            "content": pending_actions
        })

    # 收盘前建议
    alert["sections"].append({
        "title": "💡 收盘前建议",
        "content": [
            "🔍 检查挂单状态",
            "📊 复盘今日操作",
            "📝 记录交易日志"
        ]
    })

    return alert


def check_alert_conditions(
    portfolio: Dict[str, Any],
    risk_rules: Dict[str, Any]
) -> List[str]:
    """检查提醒条件"""

    alerts = []

    # 检查单只股票仓位
    if portfolio.get('max_position_pct', 0) > risk_rules.get('max_single_position', 30):
        alerts.append(f"⚠️ 单只股票仓位超限: {portfolio['max_position_pct']:.1f}%")

    # 检查回撤
    if portfolio.get('drawdown', 0) > risk_rules.get('max_drawdown', 10):
        alerts.append(f"⚠️ 回撤超限: {portfolio['drawdown']:.1f}%")

    # 检查盈亏
    if portfolio.get('today_pnl', 0) < -risk_rules.get('daily_loss_limit', 50000):
        alerts.append(f"⚠️ 日内亏损接近止损线")

    # 检查集中度
    if portfolio.get('top3_concentration', 0) > 60:
        alerts.append(f"⚠️ 持仓集中度过高")

    return alerts


def schedule_alerts(config: Dict[str, Any]) -> List[Dict[str, str]]:
    """调度提醒"""

    schedules = []

    alert_times = config.get('alert_times', {})

    # 开盘前
    if alert_times.get('pre_market'):
        schedules.append({
            'time': alert_times['pre_market'],
            'type': 'pre_market',
            'description': '开盘前准备提醒'
        })

    # 盘中
    if alert_times.get('mid_trading'):
        times = alert_times['mid_trading'].split(',')
        for t in times:
            schedules.append({
                'time': t.strip(),
                'type': 'mid_trading',
                'description': '盘中状态检查'
            })

    # 收盘前
    if alert_times.get('pre_close'):
        schedules.append({
            'time': alert_times['pre_close'],
            'type': 'pre_close',
            'description': '收盘前检查提醒'
        })

    return schedules


def main():
    parser = argparse.ArgumentParser(description='Trading Alerts - 三时段提醒系统')
    parser.add_argument('--action', required=True,
                        choices=['pre-market', 'mid-trading', 'pre-close', 'check', 'schedule'],
                        help='操作类型')
    parser.add_argument(
        '--config',
        default='/Users/niny/NiaOS/configs/invest/trading_alerts_config.json',
        help='配置文件路径'
    )

    args = parser.parse_args()

    print("🚀 Trading Alerts 启动...")
    print()

    config = load_alert_config(args.config)

    if args.action == 'pre-market':
        print(f"📊 生成开盘前提醒...")

        alert = generate_pre_market_alert(
            datetime.now().strftime('%Y-%m-%d'),
            {'index': '上证指数 3200', 'us_market': '道琼斯 +0.5%', 'sentiment': '乐观'},
            {'total_value': 1000000, 'holdings_count': 10, 'yesterday_pnl': 15000},
            ['某公司发布财报', '央行政策会议']
        )

        print()
        print("=" * 60)
        print(alert['title'])
        print("=" * 60)

        for section in alert['sections']:
            print(f"\n【{section['title']}】")
            for item in section['content']:
                print(f"  {item}")

    elif args.action == 'mid-trading':
        print(f"🔔 生成盘中提醒...")

        portfolio_alerts = check_alert_conditions(
            {'max_position_pct': 35, 'drawdown': 5, 'today_pnl': -20000, 'top3_concentration': 55},
            {'max_single_position': 30, 'max_drawdown': 10, 'daily_loss_limit': 50000}
        )

        alert = generate_mid_trading_alert(
            '11:00',
            {'current_value': 980000, 'today_pnl': -20000, 'today_return': -2.0},
            portfolio_alerts
        )

        print()
        print("=" * 60)
        print(alert['title'])
        print("=" * 60)
        print(f"优先级: {alert['priority']}")

        for section in alert['sections']:
            print(f"\n【{section['title']}】")
            for item in section['content']:
                print(f"  {item}")

    elif args.action == 'pre-close':
        print(f"⏰ 生成收盘前提醒...")

        alert = generate_pre_close_alert(
            datetime.now().strftime('%Y-%m-%d'),
            {'total_value': 1020000},
            {'pnl': 20000, 'return': 2.0, 'top_gainer': '600000 +5%', 'top_loser': '000001 -2%'},
            ['确认挂单', '记录日志']
        )

        print()
        print("=" * 60)
        print(alert['title'])
        print("=" * 60)

        for section in alert['sections']:
            print(f"\n【{section['title']}】")
            for item in section['content']:
                print(f"  {item}")

    elif args.action == 'check':
        print(f"🔍 检查提醒条件...")

        alerts = check_alert_conditions(
            {'max_position_pct': 35, 'drawdown': 5, 'today_pnl': -20000, 'top3_concentration': 65},
            {'max_single_position': 30, 'max_drawdown': 10, 'daily_loss_limit': 50000}
        )

        print()
        print("=" * 60)
        print("⚠️ 风险提示")
        print("=" * 60)

        if alerts:
            for alert in alerts:
                print(f"\n  {alert}")
        else:
            print("\n  ✅ 一切正常，无风险提示")

    elif args.action == 'schedule':
        print(f"📅 查看提醒调度...")

        schedules = schedule_alerts(config)

        print()
        print("=" * 60)
        print("📅 提醒时间表")
        print("=" * 60)

        for schedule in schedules:
            print(f"\n  {schedule['time']} - {schedule['description']}")
            print(f"    类型: {schedule['type']}")

    print("\n✅ Trading Alerts 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
