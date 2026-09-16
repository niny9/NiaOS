#!/usr/bin/env python3
"""Setup cron jobs for investment cockpit automation on macOS."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess

PROJECT_ROOT = Path("/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit")
LOG_DIR = PROJECT_ROOT / "logs"
PYTHON_BIN = "/usr/bin/python3"

START_MARKER = "# >>> investment-cockpit automation >>>"
END_MARKER = "# <<< investment-cockpit automation <<<"


JOBS = [
    f'15 9 * * 1-5 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/trading_day_morning.py >> logs/cron_morning.log 2>&1',
    f'30 12 * * 1-5 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/trading_day_noon.py >> logs/cron_midday.log 2>&1',
    f'0 20 * * 1-5 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/trading_day_evening.py >> logs/cron_daily.log 2>&1',
    f'0 20 * * 6,0 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/holdings_news_daily.py >> logs/cron_holdings_news.log 2>&1',
    f'0 21 * * 1-5 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/monitor_parameters.py >> logs/cron_monitor.log 2>&1',
    f'0 21 * * 0 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/weekend_signal_report.py >> logs/cron_weekly_report.log 2>&1',
    f'0 22 * * 0 cd "{PROJECT_ROOT}" && {PYTHON_BIN} scripts/weekly_optimization.py >> logs/cron_optimize.log 2>&1',
]


def _read_current_crontab() -> str:
    try:
        proc = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except PermissionError:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout


def _strip_managed_block(content: str) -> str:
    lines = content.splitlines()
    out: list[str] = []
    in_block = False
    for line in lines:
        if line.strip() == START_MARKER:
            in_block = True
            continue
        if line.strip() == END_MARKER:
            in_block = False
            continue
        if not in_block:
            out.append(line)
    return "\n".join([l for l in out if l.strip()])


def setup_cron() -> str:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    current = _read_current_crontab()
    base = _strip_managed_block(current)

    managed = "\n".join([START_MARKER, f"# generated_at={datetime.now().isoformat()}", *JOBS, END_MARKER])
    new_cron = (base + "\n\n" + managed).strip() + "\n"

    try:
        subprocess.run(["crontab", "-"], input=new_cron, text=True, check=True)
    except PermissionError as exc:
        raise RuntimeError("当前环境无 crontab 执行权限，请在本机终端运行该脚本") from exc
    return new_cron


def main() -> None:
    try:
        updated = setup_cron()
        print("crontab updated")
        print(updated)
    except RuntimeError as exc:
        print(f"crontab setup skipped: {exc}")


if __name__ == "__main__":
    main()
