"""Sync core data tables to Feishu bitable and send completion notification."""

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
from src.integrations.feishu_sync import FeishuSyncService
from src.integrations.feishu_notifier import FeishuNotifier
from src.portfolio.real_portfolio import RealPortfolioManager
from src.portfolio.trade_sync import TradeSyncService
from src.scoring.strategy_scorer import StrategyScorer
from src.universe.pool_manager import PoolManager
from src.utils.logger import setup_logger


def _count_records(sync_result: dict) -> int:
    return int(sync_result.get("created", 0)) + int(sync_result.get("updated", 0)) + int(sync_result.get("skipped", 0))


def _map_optimization_row(row: dict) -> dict:
    return {
        "优化日期": int(datetime.strptime(row["optimization_date"], "%Y-%m-%d").timestamp() * 1000),
        "旧参数版本": row["old_version_name"],
        "新参数版本": row["new_version_name"],
        "优化方法": row["optimization_method"],
        "旧Sharpe": float(row.get("old_sharpe") or 0),
        "新Sharpe": float(row.get("new_sharpe") or 0),
        "旧胜率": float(row.get("old_win_rate") or 0),
        "新胜率": float(row.get("new_win_rate") or 0),
        "改进幅度": float(row.get("improvement") or 0),
        "是否切换": row.get("switched") or "否",
        "切换原因": row.get("reason") or "",
        "唯一键": (
            f"opt:{row['optimization_date']}:{row['old_version_name']}:"
            f"{row['new_version_name']}:{row['optimization_method']}"
        ),
    }


def run_sync(report_date: str | None = None) -> dict:
    settings = load_app_settings()
    logger = setup_logger("sync_feishu_bitable", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    today = report_date or datetime.now().strftime("%Y-%m-%d")
    started_at = datetime.now()
    logger.info("Feishu bitable sync started report_date=%s", today)

    optimization_rows = db.fetch_all(
        """
        SELECT optimization_date, old_version_name, new_version_name, optimization_method,
               old_sharpe, new_sharpe, old_win_rate, new_win_rate, improvement, switched, reason
        FROM parameter_optimization_history
        WHERE optimization_date >= date(?, '-90 day')
        ORDER BY optimization_date DESC
        """,
        (today,),
    )
    feishu_service = FeishuSyncService(db, settings)

    feishu_sync = {}
    for key, fn in [
        ("positions", lambda: RealPortfolioManager(db).sync_to_feishu().__dict__),
        ("trades", lambda: TradeSyncService(db).sync_to_feishu().__dict__),
        ("signals", lambda: StrategyScorer(db).export_to_feishu(trade_date=today).__dict__),
        ("watchlist", lambda: PoolManager(db).sync_to_feishu().__dict__),
        (
            "optimization_history",
            lambda: feishu_service.sync_rows(
                "parameter_optimization_history",
                [_map_optimization_row(r) for r in optimization_rows],
            ).__dict__,
        ),
    ]:
        try:
            feishu_sync[key] = fn()
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Feishu sync failed for %s: %s", key, exc)
            feishu_sync[key] = {"table": key, "created": 0, "updated": 0, "skipped": 0, "error": str(exc)}

    table_stats = [
        {"table": "positions", "table_name": "持仓表", "records": _count_records(feishu_sync["positions"])},
        {"table": "trades", "table_name": "交易记录", "records": _count_records(feishu_sync["trades"])},
        {"table": "signals", "table_name": "策略信号", "records": _count_records(feishu_sync["signals"])},
        {"table": "watchlist", "table_name": "观察池", "records": _count_records(feishu_sync["watchlist"])},
        {"table": "optimization_history", "table_name": "参数优化历史", "records": _count_records(feishu_sync["optimization_history"])},
    ]

    notifier = FeishuNotifier(db=db, log_level=settings.log_level)
    notify_ok = notifier.send_bitable_sync_summary(
        report_date=today,
        table_stats=table_stats,
        base_url=f"https://feishu.cn/base/{settings.feishu_bitable_app_token}" if settings.feishu_bitable_app_token else "",
    )

    finished_at = datetime.now()
    summary = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "report_date": today,
        "table_stats": table_stats,
        "feishu_sync": feishu_sync,
        "notify_sent": notify_ok,
    }

    out = PROJECT_ROOT / "logs" / f"sync_feishu_bitable_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Feishu bitable sync finished summary=%s", summary)
    return summary


if __name__ == "__main__":
    run_sync()
