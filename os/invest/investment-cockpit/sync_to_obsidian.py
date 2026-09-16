"""Backward-compatible Obsidian sync entrypoint."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.reporting.report_generator import ReportGenerator


def sync_all(report_date: str | None = None, top_n: int = 5) -> Dict[str, Any]:
    """Generate and export the daily report to Obsidian."""
    settings = load_app_settings()
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)
    generator = ReportGenerator(db=db, project_root=PROJECT_ROOT)
    artifacts = generator.generate(report_date=report_date or datetime.now().strftime("%Y-%m-%d"), top_n=top_n)
    return {
        "report_file": str(artifacts.report_file),
        "signal_count": int(artifacts.signal_count),
        "risk_level": str(artifacts.risk_level),
    }

