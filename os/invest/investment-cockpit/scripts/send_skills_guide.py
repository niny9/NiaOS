#!/usr/bin/env python3
"""Build and send Investment Cockpit usage guide to Feishu group."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier


def build_guide() -> str:
    lines = [
        "📚 投资驾驶舱 - Skill 使用指南",
        "",
        "## Claude Code Skill 命令",
        "",
        "### 1. 查看持仓",
        "/view-portfolio",
        "- 查看当前持仓和盈亏情况",
        "",
        "### 2. 更新持仓价格",
        "/update-price",
        "- 更新持仓股票的最新价格（交易时间使用）",
        "",
        "### 3. 生成今日报告",
        "/daily-report",
        "- 生成完整的投资日报（数据更新+策略信号+新闻+飞书通知）",
        "",
        "### 4. 测试飞书通知",
        "/test-notify",
        "- 测试早盘推荐和午盘决策通知",
        "",
        "### 5. 同步飞书多维表格",
        "/sync-feishu",
        "- 手动同步数据到飞书多维表格",
        "",
        "## 自动运行时间",
        "",
        "- 9:15 早盘：更新价格 + 推荐股票",
        "- 12:30 午盘：分析表现 + 操作建议",
        "- 20:00 晚盘：完整日报 + 新闻 + 飞书通知",
        "",
        "## 飞书多维表格",
        "https://feishu.cn/base/WWfIbvCw7agzDjsCXIUcjzZnnlh",
        "",
        "---",
        "使用方法：在 Claude Code 中直接输入 skill 命令（如 /view-portfolio）即可运行",
    ]
    return "\n".join(lines)


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    notifier = FeishuNotifier(db=db, log_level=settings.log_level)

    guide_text = build_guide()
    print(guide_text)
    print("\n---")

    sent = notifier.send_text(guide_text)
    print(f"feishu_sent={sent}")


if __name__ == "__main__":
    main()
