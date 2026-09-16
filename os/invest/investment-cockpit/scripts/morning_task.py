#!/usr/bin/env python3
"""Morning task entrypoint: update positions first, then update watchlist prices."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.update_data import run_update
from src.config.settings import load_app_settings
from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier
from src.portfolio.price_updater import PositionPriceUpdater
from src.utils.logger import setup_logger


def main() -> None:
    """Run morning pipeline."""
    settings = load_app_settings()
    logger = setup_logger("morning_task", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    fetcher = DataFetcher(log_level=settings.log_level)
    updater = PositionPriceUpdater(db=db, fetcher=fetcher)

    logger.info("Morning task started at %s", datetime.now().isoformat())

    # 1) update current holdings first
    logger.info("Step1 update real positions market price")
    stats = updater.update_all_positions()
    summary = updater.get_position_summary()
    logger.info("Step1 result stats=%s summary=%s", stats, summary)

    # 2) then update watchlist prices (inside update_data step3)
    logger.info("Step2 run daily data update for latest trading day window")
    run_update(days=1)

    # 3) send morning recommendation notification
    logger.info("Step3 send Feishu morning signals")
    sent = FeishuNotifier(db=db, log_level=settings.log_level).send_morning_signals()
    logger.info("Step3 Feishu morning signals sent=%s", sent)

    logger.info("Morning task finished")


if __name__ == "__main__":
    main()
