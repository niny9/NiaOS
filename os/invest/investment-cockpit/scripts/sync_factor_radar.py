"""Sync long-format factor radar data to Feishu bitable."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult
from src.utils.logger import setup_logger

FACTOR_NAME_MAP = {
    "trend_score": "趋势因子",
    "momentum_score": "动量因子",
    "volume_score": "成交量因子",
    "news_score": "新闻因子",
    "fundamental_score": "基本面因子",
    "industry_score": "行业因子",
}

SIGNAL_NAME_MAP = {
    "short_term": "短线",
    "swing": "波段",
    "stable": "稳健",
}


def _to_feishu_ts(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)


def _build_payload(rows: list[dict]) -> list[dict]:
    payload: list[dict] = []
    for row in rows:
        date_value = row["date"]
        code = row["code"]
        signal = row["signal"]
        signal_name = SIGNAL_NAME_MAP.get(signal, "短线")
        stock_name = row.get("name") or ""
        for field_name, factor_name in FACTOR_NAME_MAP.items():
            score = row.get(field_name)
            payload.append(
                {
                    "日期": _to_feishu_ts(date_value),
                    "股票代码": code,
                    "股票名称": stock_name,
                    "策略类型": signal_name,
                    "因子名称": factor_name,
                    "因子分数": float(score or 0),
                    "唯一键": f"{date_value}_{code}_{signal}_{factor_name}",
                }
            )
    return payload


def sync_factor_radar_data(date: str | None = None) -> SyncResult:
    settings = load_app_settings()
    logger = setup_logger("sync_factor_radar", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)
    sync_service = FeishuSyncService(db, settings)

    target_date = date
    if not target_date:
        latest = db.fetch_one("SELECT MAX(date) AS d FROM daily_signals")
        target_date = str((latest or {}).get("d") or "").strip()
    if not target_date:
        logger.warning("No daily_signals data found, skip factor_radar sync")
        return SyncResult(table="factor_radar", created=0, updated=0, skipped=0)

    rows = db.fetch_all(
        """
        SELECT
            s.date, s.code, w.name, s.signal,
            f.trend_score, f.momentum_score, f.volume_score,
            f.sentiment_score AS news_score,
            f.fundamental_score,
            f.reversal_score AS industry_score
        FROM daily_signals s
        LEFT JOIN watchlist w ON w.code=s.code
        LEFT JOIN factor_scores f ON f.date=s.date AND f.code=s.code
        WHERE s.date=?
        ORDER BY s.score DESC
        """,
        (target_date,),
    )
    payload = _build_payload(rows)
    result = sync_service.sync_rows("factor_radar", payload)
    logger.info(
        "factor_radar synced date=%s source_rows=%s long_rows=%s created=%s updated=%s skipped=%s",
        target_date,
        len(rows),
        len(payload),
        result.created,
        result.updated,
        result.skipped,
    )
    return result


if __name__ == "__main__":
    sync_result = sync_factor_radar_data()
    total = int(sync_result.created) + int(sync_result.updated) + int(sync_result.skipped)
    print(
        f"因子雷达数据同步完成: table={sync_result.table}, created={sync_result.created}, "
        f"updated={sync_result.updated}, skipped={sync_result.skipped}, total={total}"
    )
