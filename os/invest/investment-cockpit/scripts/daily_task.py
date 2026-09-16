"""Daily workflow entrypoint for week-3 strategy + risk + reporting."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import socket
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.update_data import run_update
from scripts.monitor_parameters import monitor_parameters
from src.config.settings import load_app_settings
from src.data_ingestion.news_fetcher import NewsFetcher
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_bot import FeishuBot
from src.integrations.feishu_notifier import FeishuNotifier
from src.portfolio.real_portfolio import RealPortfolioManager
from src.portfolio.trade_sync import TradeSyncService
from src.reporting.news_report import NewsReportGenerator
from src.reporting.report_generator import ReportGenerator
from src.scoring.strategy_scorer import StrategyScorer
from src.integrations.performance_sync import PerformanceSyncService
from src.universe.pool_manager import PoolManager
from src.utils.date_utils import latest_n_trading_days
from src.utils.logger import setup_logger
from scripts.update_signal_performance import create_new_signal_tracking, update_signal_performance, update_daily_strategy_performance
from scripts.sync_factor_radar import sync_factor_radar_data


def _can_resolve_market_hosts() -> bool:
    """Return True when core data hosts are DNS-resolvable."""
    for host in ["query.sse.com.cn", "push2his.eastmoney.com"]:
        try:
            socket.gethostbyname(host)
        except OSError:
            return False
    return True


def run_daily_task(days: int = 90) -> None:
    """Run full daily process with update, scoring, risk and report export.

    Steps:
    1. Update data
    2. Calculate factors
    3. Score strategies
    3.5. Update signal performance tracking
    4. Run risk checks
    5. Generate daily report
    6. Export to Obsidian
    6. Sync to Feishu
    7. Write execution log
    """
    settings = load_app_settings()
    logger = setup_logger("daily_task", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    started_at = datetime.now()
    logger.info("Daily task started")

    # 1) update raw data
    if _can_resolve_market_hosts():
        run_update(days=days)
    else:
        logger.warning("Skip update_data because market data hosts are not reachable in current environment")

    # 2) run_update already handles factor computation; only keep trade dates for downstream reporting
    dates = latest_n_trading_days(days)
    end_date = dates[-1]
    factor_rows = 0

    # 3.5) update signal performance tracking
    from src.data_ingestion.data_fetcher import DataFetcher
    fetcher = DataFetcher(log_level=settings.log_level)
    try:
        create_new_signal_tracking(db)
        update_signal_performance(db, fetcher)
        update_daily_strategy_performance(db)
        logger.info("Signal performance tracking updated")
    except Exception as e:
        logger.warning(f"Signal performance update failed: {e}")


    # 3) fetch portfolio news and write markdown report
    news_fetcher = NewsFetcher(db=db, log_level=settings.log_level)
    portfolio_news = news_fetcher.fetch_portfolio_news(limit=5)
    news_report_file = NewsReportGenerator(project_root=PROJECT_ROOT).generate(
        news_list=portfolio_news,
        report_date=end_date,
    )

    # 4-7) scoring + risk + reporting + obsidian export + Feishu sync
    generator = ReportGenerator(db=db, project_root=PROJECT_ROOT)
    artifacts = generator.generate(report_date=end_date, top_n=5)
    perf_sync = PerformanceSyncService(db, settings)
    feishu_sync = {
        "positions": RealPortfolioManager(db).sync_to_feishu().__dict__,
        "trades": TradeSyncService(db).sync_to_feishu().__dict__,
        "signals": StrategyScorer(db).export_to_feishu(trade_date=end_date).__dict__,
        "watchlist": PoolManager(db).sync_to_feishu().__dict__,
        "signal_performance": perf_sync.sync_signal_performance(date=end_date).__dict__,
        "strategy_performance": perf_sync.sync_daily_strategy_performance(date=end_date).__dict__,
        "factor_radar": sync_factor_radar_data(date=end_date).__dict__,
    }
    notifier = FeishuNotifier(db=db, log_level=settings.log_level)
    feishu_notify_ok = notifier.send_daily_report(report_date=end_date)
    bitable_sync_notify_ok = notifier.send_bitable_sync_summary(
        report_date=end_date,
        table_stats=[
            {"table": "positions", "table_name": "持仓表", "records": _count_records(feishu_sync["positions"])},
            {"table": "trades", "table_name": "交易记录", "records": _count_records(feishu_sync["trades"])},
            {"table": "signals", "table_name": "策略信号", "records": _count_records(feishu_sync["signals"])},
            {"table": "watchlist", "table_name": "观察池", "records": _count_records(feishu_sync["watchlist"])},
            {"table": "factor_radar", "table_name": "因子雷达数据", "records": _count_records(feishu_sync["factor_radar"])},
        ],
        base_url=f"https://feishu.cn/base/{settings.feishu_bitable_app_token}" if settings.feishu_bitable_app_token else "",
    )

    monitor_result = monitor_parameters(sharpe_threshold=0.5)
    monitor_degraded = bool(monitor_result.get("degradation", {}).get("is_degraded", False))
    if monitor_degraded:
        warning_md = (
            "\n\n---\n\n"
            "## 参数性能预警\n"
            f"- 30日Sharpe: {float(monitor_result.get('metrics', {}).get('rolling_30d_sharpe') or 0.0):.4f}\n"
            f"- 30日胜率: {float(monitor_result.get('metrics', {}).get('rolling_30d_win_rate') or 0.0) * 100:.2f}%\n"
            f"- 30日盈亏比: {float(monitor_result.get('metrics', {}).get('rolling_30d_profit_loss_ratio') or 0.0):.4f}\n"
            "- 建议: 尽快运行参数优化。\n"
        )
        artifacts.report_file.write_text(artifacts.report_file.read_text(encoding="utf-8") + warning_md, encoding="utf-8")

    # Send Feishu bot notification after daily task completed.
    feishu_bot_notify_ok = False
    try:
        bot = FeishuBot(settings.feishu_bot_webhook)
        signal_list = db.fetch_all(
            """
            SELECT s.code, COALESCE(w.name, '') AS name, s.signal, s.score
            FROM daily_signals s
            LEFT JOIN watchlist w ON w.code = s.code
            WHERE s.date = ?
            ORDER BY s.score DESC
            """,
            (end_date,),
        )
        feishu_bot_notify_ok = bot.send_daily_signal_notification(
            signals=signal_list,
            bitable_url=f"https://my.feishu.cn/base/{settings.feishu_bitable_app_token}",
            status="success",
        )
        logger.info("Feishu bot notification sent=%s", feishu_bot_notify_ok)
    except Exception as exc:
        logger.warning("Failed to send Feishu bot notification: %s", exc)

    # 7) execution log
    finished_at = datetime.now()
    summary = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "factor_rows": factor_rows,
        "signal_count": artifacts.signal_count,
        "risk_level": artifacts.risk_level,
        "report_file": str(artifacts.report_file),
        "news_count": len(portfolio_news),
        "news_report_file": str(news_report_file),
        "feishu_notify_sent": feishu_notify_ok,
        "feishu_bitable_sync_notify_sent": bitable_sync_notify_ok,
        "feishu_bot_notify_sent": feishu_bot_notify_ok,
        "parameter_monitor": monitor_result,
        "feishu_sync": feishu_sync,
    }
    out = PROJECT_ROOT / "logs" / f"daily_task_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Daily task finished summary=%s", summary)


def _count_records(sync_result: dict) -> int:
    return int(sync_result.get("created", 0)) + int(sync_result.get("updated", 0)) + int(sync_result.get("skipped", 0))


if __name__ == "__main__":
    run_daily_task()
