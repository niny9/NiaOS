"""Fundamental factor computations."""

from __future__ import annotations

from typing import Any

import akshare as ak
import pandas as pd

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger

DEFAULT_SCORE = 50.0
LOGGER = setup_logger("fundamental_factors")


def _to_num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        text = str(value).replace("%", "").replace(",", "").strip()
        if not text:
            return None
        return float(text)
    except Exception:  # noqa: BLE001
        return None


def _clip_score(v: float) -> float:
    return float(max(0.0, min(100.0, v)))


def _resolve_symbol(code: str) -> str:
    c = str(code).strip()
    if c.startswith(("sh", "sz", "bj")):
        return c
    if c.startswith(("6", "9")):
        return f"sh{c}"
    return f"sz{c}"


def _fetch_indicator_df(symbol: str) -> pd.DataFrame:
    # Main endpoint (A股个股财务分析指标)
    try:
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        if df is not None and not df.empty:
            return df
    except Exception:
        pass
    return pd.DataFrame()


def calculate_fundamental_score(code: str, db: DatabaseManager) -> float:
    """计算基本面因子得分（0-100）。"""
    del db  # reserved for future cache/persistence usage
    try:
        symbol = _resolve_symbol(code)
        df = _fetch_indicator_df(symbol)
        if df.empty:
            return DEFAULT_SCORE

        row = df.iloc[0].to_dict()

        roe = _to_num(row.get("净资产收益率(%)") or row.get("净资产收益率"))
        revenue_yoy = _to_num(row.get("主营业务收入增长率(%)") or row.get("营业收入同比增长"))
        profit_yoy = _to_num(row.get("净利润增长率(%)") or row.get("净利润同比增长"))
        debt_ratio = _to_num(row.get("资产负债率(%)") or row.get("资产负债率"))

        if roe is None and revenue_yoy is None and profit_yoy is None and debt_ratio is None:
            return DEFAULT_SCORE

        roe_score = 50.0 if roe is None else _clip_score(roe * 2.5)
        rev_score = 50.0 if revenue_yoy is None else _clip_score(50.0 + revenue_yoy)
        profit_score = 50.0 if profit_yoy is None else _clip_score(50.0 + profit_yoy * 1.2)
        debt_score = 50.0 if debt_ratio is None else _clip_score(100.0 - debt_ratio)

        final = roe_score * 0.35 + rev_score * 0.25 + profit_score * 0.25 + debt_score * 0.15
        return _clip_score(final)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("calculate_fundamental_score failed code=%s err=%s", code, exc)
        return DEFAULT_SCORE
