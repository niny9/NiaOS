"""Initialize SQLite database schema for the investment cockpit."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger


def init_database() -> None:
    """Create all core tables and indexes in SQLite database."""
    settings = load_app_settings()
    logger = setup_logger("init_database", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")

    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    logger.info("Initializing database at: %s", settings.db_path)

    for table_name, ddl in get_table_schemas().items():
        db.execute(ddl)
        logger.info("Created/verified table: %s", table_name)

    ensure_week4_schema(db)
    logger.info("Applied week-4 schema migration")

    for index_name, ddl in get_index_statements().items():
        db.execute(ddl)
        logger.info("Created/verified index: %s", index_name)

    logger.info("Database initialization completed. Total tables: %s", len(db.list_tables()))


if __name__ == "__main__":
    init_database()
