#!/usr/bin/env python3
"""Test Feishu morning and midday notification sending."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier


def main() -> None:
    settings = load_app_settings()
    report_date = datetime.now().strftime("%Y-%m-%d")

    print(f"report_date={report_date}")
    print(f"db_path={settings.db_path}")

    if not settings.feishu_webhook_url.strip():
        print("skip notify tests: FEISHU_WEBHOOK_URL is empty")
        return

    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    notifier = FeishuNotifier(db=db, log_level=settings.log_level)

    print("test_1: send morning recommendation notification")
    morning_ok = notifier.send_morning_signals(report_date=report_date)
    print(f"morning_sent={morning_ok}")

    print("test_2: send midday decision notification")
    midday_ok = notifier.send_midday_advice(report_date=report_date)
    print(f"midday_sent={midday_ok}")


if __name__ == "__main__":
    main()
