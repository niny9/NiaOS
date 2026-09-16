#!/usr/bin/env python3
"""
Invest OS Pre-Market Runner
投资OS盘前建议 - 写入Obsidian并生成详细卡片

Version: 3.2.0
Updated: 2026-06-29
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加feishu模块到路径
feishu_path = Path(__file__).parent.parent.parent / "system" / "feishu"
if str(feishu_path) not in sys.path:
    sys.path.insert(0, str(feishu_path))

import card_sender
import card_templates

create_card_sender = card_sender.create_card_sender
InvestOSCardTemplates = card_templates.InvestOSCardTemplates


def generate_weekend_trading_advice():
    """生成周末交易建议（详细版）"""
    return {
        "stage": "weekend_pre_market",
        "market_regime": "周末休市，关注海外市场动态",
        "real_account_advice": """
【周末交易建议 - 准备下周一】

1. **观察美股周五收盘**
   - 关注纳斯达克、标普500走势
   - AI板块情绪是否延续

2. **准备候选池**
   - 稳健账户：沪A主板白马股（金融、消费龙头）
   - 短线账户：周五尾盘放量的科技股
   - 波段账户：近期突破平台的中市值标的

3. **周一开盘策略**
   - 9:15-9:25 竞价观察：缺口大小、量能
   - 9:30-9:45 不追高，等回调
   - 优先观察，低吸为主

4. **风控纪律**
   - 单票仓位≤20%
   - 止损位设在支撑位下方8%
   - 周末无法盯盘，避免重仓
""",
        "risk_guard": """
⚠️ 周末风险提示：

1. **海外市场波动风险**
   - 关注美联储政策动向
   - 地缘政治事件

2. **周一跳空缺口风险**
   - 若大幅高开，先观察不追
   - 若大幅低开，等企稳再抄底

3. **流动性风险**
   - 周一开盘前30分钟波动较大
   - 建议分批操作，不要急于全仓

🔒 严格执行止损，触发立即退出！
""",
        "next_actions": [
            "周日晚复盘美股收盘情况",
            "整理候选池标的（3-5只）",
            "设定周一盯盘时间段",
            "准备执行交易剧本"
        ],
        "data_note": "周末无实时行情，建议基于周五收盘数据和美股动态"
    }


def write_to_obsidian(advice: dict, date_str: str) -> str:
    """写入Obsidian markdown文档"""

    obsidian_base = Path("/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS")

    # 尝试多个可能的目录
    possible_dirs = [
        obsidian_base / "investment-cockpit/obsidian/01_每日简报",
        obsidian_base / "01_signals",
        obsidian_base / "reports"
    ]

    daily_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            daily_dir = dir_path
            break

    if not daily_dir:
        daily_dir = obsidian_base / "01_signals"
        daily_dir.mkdir(parents=True, exist_ok=True)

    md_file = daily_dir / f"{date_str}_周末交易建议.md"

    # 生成markdown内容
    content = f"# 投资建议 - {date_str} (周末)\n\n"
    content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"**市场状态**: {advice['market_regime']}\n\n"
    content += "---\n\n"
    content += "## 交易策略\n\n"
    content += advice['real_account_advice']
    content += "\n\n---\n\n"
    content += "## 风险提示\n\n"
    content += advice['risk_guard']
    content += "\n\n---\n\n"
    content += "## 下一步行动\n\n"
    for i, action in enumerate(advice['next_actions'], 1):
        content += f"{i}. {action}\n"
    content += f"\n\n**数据说明**: {advice['data_note']}\n"

    # 写入文件
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(md_file)


def run_invest_pre_market(dry_run: bool = True):
    """运行Invest OS盘前建议"""

    # 1. 生成交易建议
    advice = generate_weekend_trading_advice()
    date_str = datetime.now().strftime("%Y-%m-%d")

    # 2. 写入Obsidian
    obsidian_path = write_to_obsidian(advice, date_str)

    # 3. 生成Asset证据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = Path("/Users/niny/Asset/Invest OS/01_trading_advice")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = str(evidence_dir / f"pre_market_{date_str}.json")

    # 保存证据
    with open(evidence_path, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "stage": advice["stage"],
            "market_regime": advice["market_regime"],
            "advice": advice["real_account_advice"],
            "risk": advice["risk_guard"],
            "next_actions": advice["next_actions"],
            "note": advice["data_note"],
            "obsidian_path": obsidian_path,
            "dry_run": dry_run
        }, f, indent=2, ensure_ascii=False)

    # 4. 生成飞书卡片
    card_result = InvestOSCardTemplates.trading_advice_card(
        stage=advice["stage"],
        real_account_advice=advice["real_account_advice"],
        risk_guard=advice["risk_guard"],
        evidence_path=evidence_path
    )

    # 5. 发送飞书卡片
    card_sender_obj = create_card_sender()

    send_result = card_sender_obj.send_card(
        source_os="Invest",
        card_data=card_result["card_data"],
        feishu_payload=card_result["feishu_payload"],
        dry_run=dry_run
    )

    return {
        "os_id": "Invest",
        "workflow_id": "invest_pre_market",
        "status": "success" if send_result["success"] else "failed",
        "generated_at": datetime.now().isoformat(),
        "asset_output_path": evidence_path,
        "obsidian_output_path": obsidian_path,
        "feishu_payload_path": send_result.get("payload_path", ""),
        "feishu_response_path": send_result.get("response_path", ""),
        "error": send_result.get("error"),
        "dry_run": dry_run
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Invest OS Pre-Market")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--send", action="store_true")

    args = parser.parse_args()
    dry_run = not args.send

    print(f"Running Invest OS Pre-Market (dry_run={dry_run})...")
    result = run_invest_pre_market(dry_run=dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["status"] == "success":
        print("\n✅ Invest OS Pre-Market completed")
        print(f"📝 Obsidian: {result['obsidian_output_path']}")
        print(f"📋 Asset: {result['asset_output_path']}")
        if not dry_run:
            print(f"📨 Feishu card sent!")
        sys.exit(0)
    else:
        print(f"\n❌ Failed: {result.get('error')}")
        sys.exit(1)
