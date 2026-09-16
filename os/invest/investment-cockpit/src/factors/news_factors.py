"""News factor computations."""

from __future__ import annotations

from datetime import datetime
from typing import List

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

POSITIVE_KEYWORDS = ["业绩增长", "订单", "合作", "突破", "创新"]
NEGATIVE_KEYWORDS = ["亏损", "下滑", "风险", "调查", "处罚"]

DEFAULT_SCORE = 50.0
LOGGER = setup_logger("news_factors")


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _extract_news_rows(code: str, date: str, db: DatabaseManager) -> List[dict]:
    date_val = _parse_date(date)
    if date_val is None:
        return []

    # Prefer news_report if exists; fallback to news_events.
    if db.table_exists("news_report"):
        rows = db.fetch_all(
            """
            SELECT * FROM news_report
            WHERE code = ? AND date >= date(?, '-30 day') AND date <= ?
            ORDER BY date DESC
            """,
            [code, date, date],
        )
        if rows:
            return rows

    if db.table_exists("news_events"):
        rows = db.fetch_all(
            """
            SELECT * FROM news_events
            WHERE related_codes LIKE ? AND date >= date(?, '-30 day') AND date <= ?
            ORDER BY date DESC
            """,
            [f"%{code}%", date, date],
        )
        return rows

    return []


def calculate_news_score(code: str, date: str, db: DatabaseManager) -> float:
    """计算新闻因子得分（0-100）。"""
    try:
        rows = _extract_news_rows(code, date, db)
        if not rows:
            return DEFAULT_SCORE

        anchor = _parse_date(date)
        if anchor is None:
            return DEFAULT_SCORE

        weighted_sum = 0.0
        weight_total = 0.0
        for row in rows:
            text = " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("content") or ""),
                    str(row.get("summary") or ""),
                    str(row.get("evidence") or ""),
                ]
            )
            pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
            neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
            sentiment = 50.0 + (pos - neg) * 12.0

            news_time = _parse_date(row.get("date") or row.get("publish_time"))
            if news_time is None:
                recency_weight = 0.4
            else:
                days_gap = max((anchor - news_time).days, 0)
                recency_weight = max(0.2, 1.0 - days_gap / 30.0)

            weighted_sum += sentiment * recency_weight
            weight_total += recency_weight

        sentiment_score = weighted_sum / weight_total if weight_total > 0 else DEFAULT_SCORE
        heat_score = min(len(rows) * 10.0, 40.0) + 60.0 * min(weight_total / max(len(rows), 1), 1.0)

        final = sentiment_score * 0.7 + heat_score * 0.3
        return float(max(0.0, min(100.0, final)))
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("calculate_news_score failed code=%s date=%s err=%s", code, date, exc)
        return DEFAULT_SCORE
