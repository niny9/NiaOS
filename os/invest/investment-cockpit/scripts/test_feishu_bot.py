#!/usr/bin/env python3
"""Test Feishu bot notification."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_bot import FeishuBot


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    bot = FeishuBot(settings.feishu_bot_webhook)

    signals = db.fetch_all(
        """
        SELECT s.code, COALESCE(w.name, '') AS name, s.signal, s.score
        FROM daily_signals s
        LEFT JOIN watchlist w ON w.code = s.code
        ORDER BY s.date DESC, s.score DESC
        LIMIT 10
        """
    )

    success = bot.send_daily_signal_notification(
        signals=signals,
        bitable_url=f"https://my.feishu.cn/base/{settings.feishu_bitable_app_token}",
        status="success",
    )
    print(f"通知发送{'成功' if success else '失败'}")


if __name__ == "__main__":
    main()
