"""Basic validation script for Feishu integration wiring."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, settings.log_level)
    service = FeishuSyncService(db, settings)
    print(f"enabled={service.enabled}")
    if not service.enabled:
        print("skip remote calls because feishu env is not fully configured")
        return
    mapping = service.ensure_remote_schema()
    print("table_mapping=")
    for k, v in mapping.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
