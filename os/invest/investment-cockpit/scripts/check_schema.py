"""Inspect SQLite schema and sample data for factor implementation."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager


def _print_table_info(db: DatabaseManager, table: str, sample_limit: int = 3) -> None:
    print(f"\n=== TABLE: {table} ===")
    if not db.table_exists(table):
        print("(missing)")
        return

    cols = db.fetch_all(f"PRAGMA table_info({table})")
    if not cols:
        print("(no columns)")
    else:
        print("Columns:")
        for col in cols:
            print(f"- {col.get('name')} ({col.get('type')})")

    rows = db.fetch_all(f"SELECT * FROM {table} LIMIT {sample_limit}")
    print(f"Sample rows: {len(rows)}")
    for idx, row in enumerate(rows, start=1):
        print(f"{idx}. {row}")


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)

    print(f"DB Path: {settings.db_path}")
    print("\nAll tables:")
    for t in db.list_tables():
        print(f"- {t}")

    _print_table_info(db, "watchlist")
    _print_table_info(db, "news_report")
    _print_table_info(db, "news_events")


if __name__ == "__main__":
    main()
