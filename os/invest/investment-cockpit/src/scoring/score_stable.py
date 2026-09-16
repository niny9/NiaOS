"""Stable strategy scoring module."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def _num(series: pd.Series, default: float) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default).clip(0, 100)


DEFAULT_WEIGHTS: Dict[str, float] = {
    "fundamental_quality": 0.40,
    "industry_cycle": 0.20,
    "valuation_safety": 0.25,
    "technical_trend": 0.05,
    "institutional_recognition": 0.10,
    "risk_penalty": 1.00,
}


class StableScorer:
    """Score long-term opportunities with 3+ month horizon."""

    def __init__(
        self,
        weights: Dict[str, float] | None = None,
        default_fundamental: float = 55.0,
        default_industry: float = 55.0,
        default_valuation: float = 50.0,
        default_institutional: float = 50.0,
    ) -> None:
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.default_fundamental = float(default_fundamental)
        self.default_industry = float(default_industry)
        self.default_valuation = float(default_valuation)
        self.default_institutional = float(default_institutional)

    def score(self, df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
        """Compute stable scores and return ranked candidates."""
        if df.empty:
            return pd.DataFrame()

        out = df.copy()
        out["fundamental_quality"] = _num(out["fundamental_score"], self.default_fundamental) if "fundamental_score" in out.columns else self.default_fundamental
        out["industry_cycle"] = _num(out["reversal_score"], self.default_industry) if "reversal_score" in out.columns else self.default_industry
        out["valuation_safety"] = self.default_valuation
        out["technical_trend"] = _num(out["trend_score"], 50.0) if "trend_score" in out.columns else 50.0
        out["institutional_recognition"] = _num(out["sentiment_score"], self.default_institutional) if "sentiment_score" in out.columns else self.default_institutional
        out["risk_penalty"] = _num(out["risk_score"], 0.0) if "risk_score" in out.columns else 0.0

        out["stable_score"] = (
            out["fundamental_quality"] * self.weights["fundamental_quality"]
            + out["industry_cycle"] * self.weights["industry_cycle"]
            + out["valuation_safety"] * self.weights["valuation_safety"]
            + out["technical_trend"] * self.weights["technical_trend"]
            + out["institutional_recognition"] * self.weights["institutional_recognition"]
            - out["risk_penalty"]
        ).clip(0, 100)

        out = out[out["close"] <= 100]
        out = out.sort_values(["stable_score", "technical_trend"], ascending=False).head(top_n).reset_index(drop=True)
        out["rank"] = out.index + 1
        out["strategy"] = "stable"
        out["long_term_logic"] = "行业景气度+基本面质量双验证"
        out["valuation_position"] = "中性（估值模块待扩展）"
        out["falsification_condition"] = "产业逻辑弱化或财务质量显著恶化"
        out["reason"] = out.apply(
            lambda r: f"基本面{r['fundamental_quality']:.0f}/行业{r['industry_cycle']:.0f}/趋势{r['technical_trend']:.0f}",
            axis=1,
        )
        return out
