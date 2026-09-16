"""Industry factor computations."""

from __future__ import annotations

import pandas as pd

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

DEFAULT_SCORE = 50.0
LOGGER = setup_logger("industry_factors")


def _clip(v: float) -> float:
    return float(max(0.0, min(100.0, v)))


def _watchlist_industry_col(db: DatabaseManager) -> str | None:
    cols = db.fetch_all("PRAGMA table_info(watchlist)")
    names = [str(c.get("name") or "") for c in cols]
    for candidate in ["industry", "sector", "industry_chain_l1", "industry_chain_l2"]:
        if candidate in names:
            return candidate
    return None


def _get_industry_for_code(code: str, db: DatabaseManager) -> tuple[str | None, str | None]:
    if not db.table_exists("watchlist"):
        return None, None
    col = _watchlist_industry_col(db)
    if not col:
        return None, None
    row = db.fetch_one(f"SELECT {col} AS industry_name FROM watchlist WHERE code = ?", [code])
    if row and row.get("industry_name"):
        return str(row["industry_name"]), col
    return None, col


def calculate_industry_score(code: str, date: str, db: DatabaseManager) -> float:
    """计算行业因子得分（0-100）。"""
    try:
        industry, col = _get_industry_for_code(code, db)
        if not industry or not col:
            return DEFAULT_SCORE

        rows = db.fetch_all(
            f"""
            WITH wl AS (
                SELECT code
                FROM watchlist
                WHERE {col} = ?
            ),
            bars AS (
                SELECT b.code, b.date, b.close, b.amount,
                       ROW_NUMBER() OVER(PARTITION BY b.code ORDER BY b.date DESC) AS rn
                FROM stock_daily_bar b
                JOIN wl ON wl.code = b.code
                WHERE b.date <= ?
            )
            SELECT code, date, close, amount, rn
            FROM bars
            WHERE rn <= 21
            ORDER BY code, date
            """,
            [industry, date],
        )
        if not rows:
            return DEFAULT_SCORE

        df = pd.DataFrame(rows)
        if df.empty:
            return DEFAULT_SCORE

        df = df.sort_values(["code", "date"])
        df["ret_20d"] = df.groupby("code")["close"].transform(lambda s: (s / s.shift(20) - 1.0) * 100.0)

        latest = df.groupby("code", as_index=False).tail(1)
        if latest.empty:
            return DEFAULT_SCORE

        industry_ret = latest["ret_20d"].mean(skipna=True)
        if pd.isna(industry_ret):
            industry_ret = 0.0

        stock_ret = latest.loc[latest["code"] == code, "ret_20d"]
        if stock_ret.empty:
            return DEFAULT_SCORE
        stock_ret_val = float(stock_ret.iloc[0]) if pd.notna(stock_ret.iloc[0]) else 0.0

        amt = df.groupby("code", as_index=False).tail(10).copy().sort_values(["code", "date"])
        amt["bucket"] = amt.groupby("code").cumcount()
        recent_amt = float(amt[amt["bucket"] >= 5]["amount"].sum())
        prior_amt = float(amt[amt["bucket"] < 5]["amount"].sum())
        flow_ratio = recent_amt / prior_amt if prior_amt > 0 else 1.0

        industry_score = _clip(50.0 + float(industry_ret) * 1.5)
        relative_score = _clip(50.0 + (stock_ret_val - float(industry_ret)) * 2.0)
        flow_score = _clip(50.0 + (flow_ratio - 1.0) * 50.0)

        final = industry_score * 0.4 + relative_score * 0.4 + flow_score * 0.2
        return _clip(final)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("calculate_industry_score failed code=%s date=%s err=%s", code, date, exc)
        return DEFAULT_SCORE
