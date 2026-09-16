"""Initialize default parameter version into database."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.optimization import ParameterManager, ParameterSet
from src.utils.logger import setup_logger


def init_default_parameters() -> int:
    """Create default parameter version and set it active."""
    settings = load_app_settings()
    logger = setup_logger("init_parameters", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    for _, ddl in get_table_schemas().items():
        db.execute(ddl)
    for _, ddl in get_index_statements().items():
        db.execute(ddl)

    manager = ParameterManager(db)
    default_params = ParameterSet.get_default()

    existing = db.fetch_one(
        "SELECT id FROM parameter_versions WHERE version_name = ?",
        (default_params.version_name,),
    )

    if existing is not None:
        version_id = int(existing["id"])
        logger.info("Default parameter version already exists: id=%s", version_id)
    else:
        version_id = manager.create_version(default_params, description="Initial default parameters from hardcoded logic")
        logger.info("Created default parameter version: id=%s", version_id)

    manager.activate_version(version_id)
    logger.info("Activated default parameter version: id=%s", version_id)
    return version_id


if __name__ == "__main__":
    created_id = init_default_parameters()
    print(f"Initialized parameter version id={created_id}")
