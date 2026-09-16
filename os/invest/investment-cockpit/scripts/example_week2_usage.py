"""Example script for week-2 modules."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.universe.pool_manager import PoolManager


def main() -> None:
    """Show basic usage of week-2 modules."""
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path)

    pool = PoolManager(db)
    core = pool.get_by_status("核心池")
    print(f"核心池数量: {len(core)}")

    sw = pool.get_by_chain("半导体")
    print(f"半导体数量: {len(sw)}")

    latest = db.fetch_all(
        "SELECT date, code, close, amount FROM stock_daily_bar ORDER BY date DESC, code LIMIT 10"
    )
    print("最新10条行情:")
    for row in latest:
        print(row)


if __name__ == "__main__":
    main()
