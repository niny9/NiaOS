"""Trend factor computations."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def add_trend_factors(df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
    """Add MA and trend score columns.

    Expected columns: ``date``, ``code``, ``close``.
    """
    out = df.sort_values(["code", "date"]).copy()
    cfg = params or {}
    ma_short = int(cfg.get("ma_short", 5))
    ma_mid = int(cfg.get("ma_mid", 20))
    ma_long = int(cfg.get("ma_long", 60))

    out["ma5"] = out.groupby("code")["close"].transform(lambda s: s.rolling(ma_short, min_periods=1).mean())
    out["ma20"] = out.groupby("code")["close"].transform(lambda s: s.rolling(ma_mid, min_periods=1).mean())
    out["ma60"] = out.groupby("code")["close"].transform(lambda s: s.rolling(ma_long, min_periods=1).mean())

    cond_up = (out["close"] > out["ma5"]) & (out["ma5"] > out["ma20"]) & (out["ma20"] > out["ma60"])
    cond_mid = (out["close"] > out["ma20"]) & (out["ma20"] > out["ma60"])
    out["trend_score"] = 40.0
    out.loc[cond_mid, "trend_score"] = 70.0
    out.loc[cond_up, "trend_score"] = 90.0
    return out
