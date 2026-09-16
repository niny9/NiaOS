"""Weekly review workflow script."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.portfolio.model_portfolio import ModelPortfolioManager
from src.reporting.weekly_review import WeeklyReviewGenerator
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger


def _default_week_range() -> tuple[str, str, str]:
    today = datetime.now().date()
    start = today - timedelta(days=6)
    week = f"{today.year}年第{today.isocalendar().week}周"
    return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), week


def main() -> None:
    """Run full weekly analysis and report export."""
    parser = argparse.ArgumentParser(description="周度复盘任务")
    parser.add_argument("--start", help="开始日期YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期YYYY-MM-DD")
    parser.add_argument("--week", help="周标签，如2026年第21周")
    args = parser.parse_args()

    ds, de, week = _default_week_range()
    start_date = args.start or ds
    end_date = args.end or de
    week_label = args.week or week

    settings = load_app_settings()
    logger = setup_logger("weekly_task", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, settings.log_level)
    ensure_week4_schema(db)

    model = ModelPortfolioManager(db)
    days = db.fetch_all("SELECT DISTINCT date FROM daily_signals WHERE date BETWEEN ? AND ? ORDER BY date", (start_date, end_date))
    for d in days:
        model.rebalance_by_signals(d["date"])

    generator = WeeklyReviewGenerator(db, PROJECT_ROOT)
    artifacts = generator.generate(start_date=start_date, end_date=end_date, week_label=week_label)
    feishu_result = generator.export_to_feishu(start_date=start_date, end_date=end_date, week_label=week_label)

    summary = {
        "week": week_label,
        "start_date": start_date,
        "end_date": end_date,
        "report": str(artifacts.file_path),
        "logged_rows": artifacts.logged_rows,
        "feishu_sync": feishu_result.__dict__,
    }
    out = PROJECT_ROOT / "logs" / f"weekly_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("weekly summary=%s", summary)
    print(f"周报已生成: {artifacts.file_path}")


if __name__ == "__main__":
    main()
