"""Trade sync CLI for real trades and positions."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.portfolio.trade_sync import TradeSyncService
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger


def main() -> None:
    """Entry point for interactive or batch trade sync."""
    parser = argparse.ArgumentParser(description="同步真实交易并自动更新持仓")
    parser.add_argument("--import", dest="import_file", type=str, help="批量导入JSON文件")
    parser.add_argument("--undo", action="store_true", help="撤销最近一笔交易")
    args = parser.parse_args()

    settings = load_app_settings()
    logger = setup_logger("sync_trade", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, settings.log_level)
    ensure_week4_schema(db)
    svc = TradeSyncService(db)

    if args.undo:
        ok = svc.undo_latest_trade()
        print("撤销成功" if ok else "没有可撤销的交易")
        return

    if args.import_file:
        count = svc.import_from_json(Path(args.import_file))
        logger.info("imported=%s file=%s", count, args.import_file)
        print(f"批量导入完成: {count} 笔")
        return

    trade = svc.interactive_input()
    trade_id = svc.sync_trade(trade)
    logger.info("synced trade_id=%s code=%s", trade_id, trade.code)
    print(f"同步成功，trade_id={trade_id}")


if __name__ == "__main__":
    main()
