"""Validation script for week-2 data layer deliverables."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager


def main() -> None:
    """Run basic validation checks against database tables."""
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path)

    checks = {
        "stock_basic": "SELECT COUNT(1) AS c FROM stock_basic",
        "watchlist": "SELECT COUNT(1) AS c FROM watchlist",
        "stock_daily_bar": "SELECT COUNT(1) AS c FROM stock_daily_bar",
        "factor_scores": "SELECT COUNT(1) AS c FROM factor_scores",
    }

    for table, sql in checks.items():
        row = db.fetch_one(sql)
        count = int(row["c"]) if row else 0
        print(f"{table}: {count}")

    failed = db.fetch_all(
        "SELECT code, COUNT(1) AS n FROM stock_daily_bar WHERE close IS NULL GROUP BY code ORDER BY n DESC LIMIT 5"
    )
    print("null close top5:", failed)


if __name__ == "__main__":
    main()
