"""Momentum and relative strength factor computations."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


INDEX_RS_CODE = "INDEX:sh000001"


def _pct_change_by_code(df: pd.DataFrame, periods: int, col_name: str) -> pd.Series:
    return df.groupby("code")["close"].transform(lambda s: s.pct_change(periods=periods) * 100.0).rename(col_name)


def add_momentum_factors(df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
    """Add momentum and relative-strength columns."""
    out = df.sort_values(["code", "date"]).copy()
    out["ret_5d"] = _pct_change_by_code(out, 5, "ret_5d")
    out["ret_20d"] = _pct_change_by_code(out, 20, "ret_20d")
    out["ret_60d"] = _pct_change_by_code(out, 60, "ret_60d")

    idx = out[out["code"] == INDEX_RS_CODE][["date", "ret_20d"]].rename(columns={"ret_20d": "index_ret_20d"})
    out = out.merge(idx, on="date", how="left")
    out["relative_strength"] = out["ret_20d"] - out["index_ret_20d"]

    cfg = params or {}
    ret_5d_weight = float(cfg.get("ret_5d_weight", 0.2))
    ret_20d_weight = float(cfg.get("ret_20d_weight", 0.5))
    ret_60d_weight = float(cfg.get("ret_60d_weight", 0.3))
    rs_weight = float(cfg.get("relative_strength_weight", 0.5))

    out["momentum_score"] = (
        out["ret_5d"].fillna(0) * ret_5d_weight
        + out["ret_20d"].fillna(0) * ret_20d_weight
        + out["ret_60d"].fillna(0) * ret_60d_weight
        + out["relative_strength"].fillna(0) * rs_weight
    )
    out["momentum_score"] = out["momentum_score"].clip(-100, 100) * 0.5 + 50
    return out
