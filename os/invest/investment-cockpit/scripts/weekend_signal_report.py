#!/usr/bin/env python3
"""Weekend signal report wrapper."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from weekly_report import main as weekly_report_main
from src.config.settings import load_app_settings
from src.utils.logger import setup_logger


def main() -> None:
    settings = load_app_settings()
    logger = setup_logger("weekend_signal_report", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    logger.info("Weekend signal report started")

    weekly_report_main()

    summary = {
        "task": "weekend_signal_report",
        "finished_at": datetime.now().isoformat(),
    }
    out = PROJECT_ROOT / "logs" / f"weekend_signal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Weekend signal report finished")


if __name__ == "__main__":
    main()
