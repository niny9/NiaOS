#!/usr/bin/env python3
"""Test end-to-end automation wiring for Phase 5."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys

PROJECT_ROOT = Path("/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier
from src.reporting.optimization_report import OptimizationReportGenerator
from scripts.monitor_parameters import monitor_parameters


def check_crontab() -> dict:
    try:
        proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except PermissionError:
        return {
            "loaded": False,
            "permission_denied": True,
            "checks": {
                "daily_task": False,
                "monitor_parameters": False,
                "weekly_optimization": False,
            },
            "all_present": False,
        }
    content = proc.stdout if proc.returncode == 0 else ""
    checks = {
        "daily_task": "scripts/daily_task.py" in content,
        "monitor_parameters": "scripts/monitor_parameters.py" in content,
        "weekly_optimization": "scripts/weekly_optimization.py" in content,
    }
    return {
        "loaded": proc.returncode == 0,
        "checks": checks,
        "all_present": all(checks.values()),
    }


def run_tests() -> dict:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    notifier = FeishuNotifier(db=db, log_level=settings.log_level)

    monitor_report = monitor_parameters(sharpe_threshold=0.5)
    opt_path, _ = OptimizationReportGenerator(db=db, project_root=PROJECT_ROOT).generate()

    notify_ok = notifier.send_text("✅ automation test: phase5 pipeline check")

    result = {
        "timestamp": datetime.now().isoformat(),
        "crontab": check_crontab(),
        "monitor_report_generated": True,
        "monitor_degraded": bool(monitor_report.get("degradation", {}).get("is_degraded", False)),
        "optimization_report_path": str(opt_path),
        "feishu_notify_test_sent": notify_ok,
        "status": "pass",
    }
    if not result["crontab"]["all_present"]:
        result["status"] = "warning"
    return result


def main() -> None:
    report = run_tests()
    out = PROJECT_ROOT / "logs" / f"automation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"saved={out}")


if __name__ == "__main__":
    main()
