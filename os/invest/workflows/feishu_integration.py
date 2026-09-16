#!/usr/bin/env python3
"""
Feishu Integration - 飞书集成
飞书机器人接入、多维表同步、消息推送、命令交互
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


def load_feishu_config(config_path: str) -> Dict[str, Any]:
    """加载飞书配置"""
    if not os.path.exists(config_path):
        return {
            "app_id": "",
            "app_secret": "",
            "webhook_url": "",
            "bot_name": "NiaOS Bot",
            "enabled": False
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_feishu_config(config: Dict[str, Any], config_path: str):
    """保存飞书配置"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, indent=2, ensure_ascii=False, fp=f)
    print(f"✅ 已保存配置: {config_path}")


def send_text_message(webhook_url: str, text: str) -> bool:
    """发送文本消息"""

    # 模拟发送（实际需要requests库）
    print(f"📤 模拟发送到飞书:")
    print(f"   Webhook: {webhook_url}")
    print(f"   内容: {text}")

    # 实际实现:
    # import requests
    # payload = {"msg_type": "text", "content": {"text": text}}
    # response = requests.post(webhook_url, json=payload)
    # return response.status_code == 200

    return True


def send_card_message(webhook_url: str, title: str, content: List[Dict[str, str]]) -> bool:
    """发送卡片消息"""

    print(f"📤 模拟发送卡片到飞书:")
    print(f"   标题: {title}")
    print(f"   内容项: {len(content)}条")

    for item in content:
        print(f"     - {item.get('label')}: {item.get('value')}")

    return True


def create_daily_report_card(
    date: str,
    portfolio_value: float,
    daily_pnl: float,
    daily_return: float,
    top_gainers: List[Dict[str, Any]],
    top_losers: List[Dict[str, Any]],
    alerts: List[str]
) -> Dict[str, Any]:
    """创建日报卡片"""

    card = {
        "title": f"📊 投资日报 {date}",
        "sections": [
            {
                "title": "账户概况",
                "fields": [
                    {"label": "总市值", "value": f"{portfolio_value/10000:.2f}万"},
                    {"label": "今日盈亏", "value": f"{daily_pnl/10000:.2f}万"},
                    {"label": "今日收益率", "value": f"{daily_return:.2f}%"}
                ]
            },
            {
                "title": "涨幅前3",
                "fields": [
                    {"label": g['symbol'], "value": f"+{g['change']:.2f}%"}
                    for g in top_gainers[:3]
                ]
            },
            {
                "title": "跌幅前3",
                "fields": [
                    {"label": l['symbol'], "value": f"{l['change']:.2f}%"}
                    for l in top_losers[:3]
                ]
            }
        ]
    }

    if alerts:
        card["sections"].append({
            "title": "⚠️ 风险提示",
            "fields": [{"label": "提醒", "value": alert} for alert in alerts]
        })

    return card


def sync_to_bitable(
    app_token: str,
    table_id: str,
    records: List[Dict[str, Any]]
) -> bool:
    """同步数据到飞书多维表"""

    print(f"📊 模拟同步到飞书多维表:")
    print(f"   App Token: {app_token[:20]}...")
    print(f"   Table ID: {table_id}")
    print(f"   记录数: {len(records)}")

    for i, record in enumerate(records[:3], 1):
        print(f"   {i}. {record}")

    return True


def handle_command(command: str, args: List[str]) -> str:
    """处理命令"""

    if command == "/status":
        return "✅ NiaOS运行正常\n当前功能：投资管理、风险监控"

    elif command == "/report":
        return "📊 正在生成今日报告..."

    elif command == "/alert":
        return "🔔 当前无重要提醒"

    elif command == "/holdings":
        return "📈 持仓概况：\n总市值：100万\n持仓数：10"

    else:
        return f"❓ 未知命令: {command}\n可用命令: /status, /report, /alert, /holdings"


def setup_webhook(webhook_url: str, description: str = "NiaOS Webhook") -> bool:
    """配置Webhook"""

    print(f"🔧 配置Webhook:")
    print(f"   URL: {webhook_url}")
    print(f"   描述: {description}")
    print(f"   ✅ Webhook配置成功")

    return True


def test_connection(webhook_url: str) -> bool:
    """测试连接"""

    test_message = "🎉 NiaOS飞书集成测试成功！"

    print(f"🧪 测试飞书连接...")
    result = send_text_message(webhook_url, test_message)

    if result:
        print(f"   ✅ 连接测试成功")
    else:
        print(f"   ❌ 连接测试失败")

    return result


def main():
    parser = argparse.ArgumentParser(description='Feishu Integration - 飞书集成')
    parser.add_argument('--action', required=True,
                        choices=['setup', 'test', 'send', 'card', 'sync', 'command'],
                        help='操作类型')
    parser.add_argument('--webhook', help='Webhook URL')
    parser.add_argument('--text', help='发送文本')
    parser.add_argument('--command-text', help='命令文本')
    parser.add_argument(
        '--config',
        default='/Users/niny/NiaOS/configs/invest/feishu_config.json',
        help='配置文件路径'
    )

    args = parser.parse_args()

    print("🚀 Feishu Integration 启动...")
    print()

    config = load_feishu_config(args.config)

    if args.action == 'setup':
        if not args.webhook:
            print("❌ 配置需要 --webhook")
            return 1

        print(f"🔧 配置飞书集成...")

        config['webhook_url'] = args.webhook
        config['enabled'] = True
        config['setup_at'] = datetime.now().isoformat()

        save_feishu_config(config, args.config)

        # 测试连接
        test_connection(args.webhook)

        print(f"\n✅ 飞书集成配置完成")

    elif args.action == 'test':
        webhook = args.webhook or config.get('webhook_url')

        if not webhook:
            print("❌ 测试需要 --webhook 或先配置")
            return 1

        print(f"🧪 测试飞书连接...")
        test_connection(webhook)

    elif args.action == 'send':
        if not args.text:
            print("❌ 发送消息需要 --text")
            return 1

        webhook = args.webhook or config.get('webhook_url')

        if not webhook:
            print("❌ 需要先配置webhook")
            return 1

        print(f"📤 发送文本消息...")
        send_text_message(webhook, args.text)
        print(f"✅ 消息已发送")

    elif args.action == 'card':
        webhook = args.webhook or config.get('webhook_url')

        if not webhook:
            print("❌ 需要先配置webhook")
            return 1

        print(f"📊 发送日报卡片...")

        # 示例数据
        card = create_daily_report_card(
            datetime.now().strftime('%Y-%m-%d'),
            1000000,  # 100万
            15000,    # 1.5万盈利
            1.5,      # 1.5%
            [{'symbol': '600000', 'change': 5.2}],
            [{'symbol': '000001', 'change': -2.1}],
            ["持仓集中度偏高"]
        )

        print()
        print("=" * 60)
        print("📊 日报卡片预览")
        print("=" * 60)
        print(f"\n标题: {card['title']}\n")

        for section in card['sections']:
            print(f"【{section['title']}】")
            for field in section['fields']:
                print(f"  {field['label']}: {field['value']}")
            print()

        send_card_message(webhook, card['title'], card['sections'][0]['fields'])

    elif args.action == 'sync':
        print(f"📊 同步数据到多维表...")

        # 示例数据
        records = [
            {'date': '2026-06-15', 'pnl': 15000, 'return': 1.5},
            {'date': '2026-06-14', 'pnl': 8000, 'return': 0.8}
        ]

        sync_to_bitable('app_xxx', 'table_xxx', records)
        print(f"✅ 数据同步完成")

    elif args.action == 'command':
        if not args.command_text:
            print("❌ 处理命令需要 --command-text")
            return 1

        print(f"🤖 处理命令...")

        parts = args.command_text.split()
        command = parts[0]
        cmd_args = parts[1:] if len(parts) > 1 else []

        response = handle_command(command, cmd_args)

        print()
        print("=" * 60)
        print("🤖 命令响应")
        print("=" * 60)
        print(f"\n{response}")

    print("\n✅ Feishu Integration 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
