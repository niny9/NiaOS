"""Volume factor computations."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def add_volume_factors(df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
    """Add amount/turnover/volume-ratio based score columns."""
    out = df.sort_values(["code", "date"]).copy()
    out["amount_ma5"] = out.groupby("code")["amount"].transform(lambda s: s.rolling(5, min_periods=1).mean())
    out["volume_ma5"] = out.groupby("code")["volume"].transform(lambda s: s.rolling(5, min_periods=1).mean())
    out["volume_ratio"] = out["volume"] / out["volume_ma5"].replace(0, pd.NA)

    cfg = params or {}
    turnover_threshold = float(cfg.get("turnover_threshold", 5))
    amount_multiplier = float(cfg.get("amount_multiplier", 3))
    volume_ratio_multiplier = float(cfg.get("volume_ratio_multiplier", 3))

    turnover_score = out["turnover"].fillna(0).clip(0, turnover_threshold) / max(turnover_threshold, 1e-6) * 30
    amount_score = (
        (out["amount"] / out["amount_ma5"].replace(0, pd.NA)).fillna(1).clip(0, amount_multiplier) / max(amount_multiplier, 1e-6) * 40
    )
    vr_score = out["volume_ratio"].fillna(1).clip(0, volume_ratio_multiplier) / max(volume_ratio_multiplier, 1e-6) * 30

    out["volume_score"] = (turnover_score + amount_score + vr_score).clip(0, 100)
    return out
