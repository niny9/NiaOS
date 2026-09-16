"""Example script for week-3 full workflow."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.reporting.report_generator import ReportGenerator


def main() -> None:
    """Run report generator and print key outputs."""
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path)
    generator = ReportGenerator(db=db, project_root=PROJECT_ROOT)
    artifacts = generator.generate(top_n=5)

    print(f"report_date={artifacts.report_date}")
    print(f"risk_level={artifacts.risk_level}")
    print(f"signal_count={artifacts.signal_count}")
    print(f"report_file={artifacts.report_file}")


if __name__ == "__main__":
    main()
