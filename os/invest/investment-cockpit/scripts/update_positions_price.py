#!/usr/bin/env python3
"""Update active position prices with one batch spot snapshot."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager
from src.portfolio.price_updater import PositionPriceUpdater


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    fetcher = DataFetcher(log_level=settings.log_level)
    updater = PositionPriceUpdater(db=db, fetcher=fetcher)

    stats = updater.update_all_positions()
    summary = updater.get_position_summary()

    print("=== Position Price Update ===")
    print(
        f"total={stats['total_positions']} updated={stats['updated_count']} "
        f"missing={stats['missing_count']} skipped={stats['skipped_count']}"
    )
    if stats["missing_codes"]:
        print("missing_codes=" + ",".join(stats["missing_codes"]))

    print("\n=== Position Summary ===")
    print(f"positions={summary['position_count']}")
    print(
        f"total_market_value={summary['total_market_value']:.2f} "
        f"total_profit={summary['total_profit']:.2f} "
        f"total_profit_pct={summary['total_profit_pct']:.2%}"
    )
    if summary["best_position"]:
        best = summary["best_position"]
        worst = summary["worst_position"]
        print(f"best={best['code']} {best['name']} {best['profit_pct']:.2%}")
        print(f"worst={worst['code']} {worst['name']} {worst['profit_pct']:.2%}")


if __name__ == "__main__":
    main()
