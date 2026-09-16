#!/usr/bin/env python3
"""Generate daily holdings/watchlist news summary."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.data_ingestion.news_fetcher import NewsFetcher
from src.reporting.news_report import NewsReportGenerator
from src.utils.date_utils import latest_n_trading_days
from src.utils.logger import setup_logger


def main() -> None:
    settings = load_app_settings()
    logger = setup_logger("holdings_news_daily", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)

    report_date = latest_n_trading_days(1)[-1]
    logger.info("Generating holdings news for %s", report_date)

    news = NewsFetcher(db=db, log_level=settings.log_level).fetch_portfolio_news(limit=15)

    # 降级策略：如果新闻数量少于10条，尝试使用前一天的数据
    if len(news) < 10:
        logger.warning("News count (%d) below threshold, attempting fallback to previous day", len(news))
        previous_days = latest_n_trading_days(5)
        for prev_date in reversed(previous_days[:-1]):
            prev_report_path = PROJECT_ROOT / "reports" / f"news_report_{prev_date}.md"
            if prev_report_path.exists():
                prev_content = prev_report_path.read_text(encoding="utf-8")
                if len(prev_content) > 200 and "暂无可用新闻" not in prev_content:
                    logger.info("Using fallback report from %s (has %d bytes)", prev_date, len(prev_content))
                    
                    parts = prev_content.split("\n\n", 1)
                    fallback_report = f"# 持仓股票新闻汇总 {report_date}\n\n"
                    fallback_report += f"> ⚠️ 数据降级：当日新闻获取失败（仅获取 {len(news)} 条），使用 {prev_date} 的新闻作为参考\n\n"
                    fallback_report += parts[1] if len(parts) > 1 else prev_content

                    report_file = PROJECT_ROOT / "reports" / f"news_report_{report_date}.md"
                    report_file.write_text(fallback_report, encoding="utf-8")

                    summary = {
                        "report_date": report_date,
                        "news_count": len(news),
                        "fallback_from": prev_date,
                        "fallback_used": True,
                        "report_file": str(report_file),
                        "generated_at": datetime.now().isoformat(),
                    }
                    out = PROJECT_ROOT / "logs" / f"holdings_news_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
                    logger.warning("Holdings news generated with fallback: %s", summary)
                    print(f"持仓新闻已生成（使用降级数据）: {report_file}")
                    return

    report_file = NewsReportGenerator(project_root=PROJECT_ROOT).generate(news_list=news, report_date=report_date)

    summary = {
        "report_date": report_date,
        "news_count": len(news),
        "fallback_used": False,
        "report_file": str(report_file),
        "generated_at": datetime.now().isoformat(),
    }
    out = PROJECT_ROOT / "logs" / f"holdings_news_daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Holdings news summary=%s", summary)
    print(f"持仓新闻已生成: {report_file}")


if __name__ == "__main__":
    main()
