#!/usr/bin/env python3
"""
参数性能监控
每日监控当前参数的表现，如果持续下降则预警
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.optimization.parameter_manager import ParameterManager, ParameterSet
from src.optimization.optimizer import ParameterOptimizer
from src.integrations.feishu_notifier import FeishuNotifier
from src.utils.logger import setup_logger

logger = setup_logger("ParameterMonitor")


def _to_float(v: object, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _build_monitor_report(db: DatabaseManager, version_id: int, version_name: str, threshold: float) -> dict:
    rows = db.fetch_all(
        """
        SELECT id, test_start_date, test_end_date, sharpe_ratio, win_rate, profit_loss_ratio, trade_count, created_at
        FROM parameter_performance
        WHERE version_id = ?
          AND date(created_at) >= date('now', '-30 day')
        ORDER BY created_at DESC, id DESC
        """,
        (version_id,),
    )

    if not rows:
        return {
            "generated_at": datetime.now().isoformat(),
            "version_id": version_id,
            "version_name": version_name,
            "window_days": 30,
            "thresholds": {"sharpe_alert": threshold},
            "metrics": {
                "rolling_30d_sharpe": 0.0,
                "rolling_30d_win_rate": 0.0,
                "rolling_30d_profit_loss_ratio": 0.0,
                "records": 0,
            },
            "degradation": {
                "is_degraded": True,
                "is_persistent": True,
                "consecutive_below_threshold": 0,
            },
            "recent_records": [],
        }

    sharpe_values = [_to_float(r.get("sharpe_ratio")) for r in rows if r.get("sharpe_ratio") is not None]
    win_values = [_to_float(r.get("win_rate")) for r in rows if r.get("win_rate") is not None]
    pl_values = [_to_float(r.get("profit_loss_ratio")) for r in rows if r.get("profit_loss_ratio") is not None]

    rolling_sharpe = sum(sharpe_values) / len(sharpe_values) if sharpe_values else 0.0
    rolling_win_rate = sum(win_values) / len(win_values) if win_values else 0.0
    rolling_pl_ratio = sum(pl_values) / len(pl_values) if pl_values else 0.0

    consecutive = 0
    for row in rows:
        s = row.get("sharpe_ratio")
        if s is None:
            continue
        if float(s) < threshold:
            consecutive += 1
        else:
            break

    is_degraded = rolling_sharpe < threshold
    is_persistent = is_degraded and consecutive >= 3

    return {
        "generated_at": datetime.now().isoformat(),
        "version_id": version_id,
        "version_name": version_name,
        "window_days": 30,
        "thresholds": {"sharpe_alert": threshold},
        "metrics": {
            "rolling_30d_sharpe": round(rolling_sharpe, 4),
            "rolling_30d_win_rate": round(rolling_win_rate, 4),
            "rolling_30d_profit_loss_ratio": round(rolling_pl_ratio, 4),
            "records": len(rows),
        },
        "degradation": {
            "is_degraded": is_degraded,
            "is_persistent": is_persistent,
            "consecutive_below_threshold": consecutive,
        },
        "recent_records": rows[:5],
    }


def monitor_parameters(sharpe_threshold: float = 0.5) -> dict:
    """监控参数性能。"""
    logger.info("开始参数性能监控")

    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    param_manager = ParameterManager(db)
    optimizer = ParameterOptimizer(db)
    notifier = FeishuNotifier(db, log_level=settings.log_level)

    try:
        current_params = param_manager.get_active_version()
    except ValueError as exc:
        if "No active parameter version found" not in str(exc):
            raise
        logger.warning("未找到活跃参数版本，初始化默认参数版本")
        default_params = ParameterSet.get_default()
        version_id = param_manager.create_version(
            default_params,
            "Auto-initialized default parameter version",
        )
        param_manager.activate_version(version_id)
        current_params = param_manager.get_active_version()

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    score = optimizer._evaluate_params(
        current_params,
        start_date,
        end_date,
        "all",
        "sharpe_ratio",
    )

    logger.info("当前参数版本: %s", current_params.version_name)
    logger.info("30日滚动夏普: %.4f", score)

    active_row = db.fetch_one(
        "SELECT id FROM parameter_versions WHERE status='active' ORDER BY created_at DESC, id DESC LIMIT 1"
    )
    if active_row is None:
        raise ValueError("No active parameter version found for performance record")

    param_manager.record_performance(
        version_id=int(active_row["id"]),
        start_date=start_date,
        end_date=end_date,
        strategy_type="all",
        metrics={
            "sharpe_ratio": score,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_loss_ratio": 0.0,
            "trade_count": 0,
        },
    )

    report = _build_monitor_report(
        db=db,
        version_id=int(active_row["id"]),
        version_name=current_params.version_name,
        threshold=sharpe_threshold,
    )

    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    report_path = logs_dir / f"parameter_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("参数监控报告已生成: %s", report_path)

    degraded = bool(report["degradation"]["is_degraded"])
    persistent = bool(report["degradation"]["is_persistent"])
    if persistent:
        notifier.send_parameter_monitor_alert(report)
        logger.warning("参数性能持续下降，已发送飞书预警")
    elif degraded:
        logger.warning("参数性能下降但未达到持续下降阈值")
    else:
        logger.info("参数性能正常")

    return report


if __name__ == "__main__":
    monitor_parameters()
