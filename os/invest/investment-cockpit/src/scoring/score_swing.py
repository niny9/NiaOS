"""Swing strategy scoring module."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def _num(series: pd.Series, default: float) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default).clip(0, 100)


DEFAULT_WEIGHTS: Dict[str, float] = {
    "technical_trend": 0.25,
    "industry_cycle": 0.35,
    "capital_strength": 0.20,
    "fundamental_quality": 0.15,
    "risk_penalty": 0.05,
}


class SwingScorer:
    """Score swing opportunities with 2-8 week horizon."""

    def __init__(self, weights: Dict[str, float] | None = None, default_industry: float = 55.0, default_fundamental: float = 50.0) -> None:
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.default_industry = float(default_industry)
        self.default_fundamental = float(default_fundamental)

    def score(self, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """Compute swing scores and return ranked candidates."""
        if df.empty:
            return pd.DataFrame()

        out = df.copy()
        out["technical_trend"] = _num(out["trend_score"], 50.0) if "trend_score" in out.columns else 50.0
        # Industry score is stored in reversal_score (schema compatibility).
        out["industry_cycle"] = _num(out["reversal_score"], self.default_industry) if "reversal_score" in out.columns else self.default_industry
        out["capital_strength"] = _num(out["volume_score"], 50.0) if "volume_score" in out.columns else 50.0
        out["fundamental_quality"] = _num(out["fundamental_score"], self.default_fundamental) if "fundamental_score" in out.columns else self.default_fundamental
        out["risk_penalty"] = _num(out["risk_score"], 0.0) if "risk_score" in out.columns else 0.0

        out["swing_score"] = (
            out["technical_trend"] * self.weights["technical_trend"]
            + out["industry_cycle"] * self.weights["industry_cycle"]
            + out["capital_strength"] * self.weights["capital_strength"]
            + out["fundamental_quality"] * self.weights["fundamental_quality"]
            - out["risk_penalty"] * self.weights["risk_penalty"]
        ).clip(0, 100)

        out = out[out["close"] <= 100]
        out = out.sort_values(["swing_score", "technical_trend"], ascending=False).head(top_n).reset_index(drop=True)
        out["rank"] = out.index + 1
        out["strategy"] = "swing"
        out["current_range"] = out.apply(lambda r: f"{r.get('ma20', 0):.2f}~{r.get('ma5', 0):.2f}", axis=1)
        out["ideal_buy_point"] = "回踩MA20企稳或放量突破平台"
        out["reduce_condition"] = "跌破MA20且量能放大"
        out["reason"] = out.apply(
            lambda r: f"趋势{r['technical_trend']:.0f}/行业{r['industry_cycle']:.0f}/资金{r['capital_strength']:.0f}/基本面{r['fundamental_quality']:.0f}",
            axis=1,
        )
        return out
