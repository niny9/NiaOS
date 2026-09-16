"""Short-term strategy scoring module."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def _num(series: pd.Series, default: float) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default).clip(0, 100)


DEFAULT_WEIGHTS: Dict[str, float] = {
    "technical_trend": 0.40,
    "capital_strength": 0.35,
    "news_catalyst": 0.15,
    "sentiment_heat": 0.05,
    "risk_penalty": 0.05,
}


class ShortTermScorer:
    """Score short-term opportunities with 1-5 trading day horizon."""

    def __init__(self, weights: Dict[str, float] | None = None, default_news: float = 50.0, default_sentiment: float = 50.0) -> None:
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self.default_news = float(default_news)
        self.default_sentiment = float(default_sentiment)

    def score(self, df: pd.DataFrame, top_n: int = 5, thresholds: Dict[str, float] | None = None) -> pd.DataFrame:
        """Compute short-term scores and return ranked candidates.

        Args:
            df: Input frame containing at least code/name/trend_score/volume_score/amount/turnover.
            top_n: Number of rows to keep.
        """
        if df.empty:
            return pd.DataFrame()

        out = df.copy()
        out["technical_trend"] = _num(out["trend_score"], 50.0) if "trend_score" in out.columns else 50.0
        out["capital_strength"] = _num(out["volume_score"], 50.0) if "volume_score" in out.columns else 50.0
        out["news_catalyst"] = _num(out["sentiment_score"], self.default_news) if "sentiment_score" in out.columns else self.default_news
        out["sentiment_heat"] = _num(out["momentum_score"], self.default_sentiment) if "momentum_score" in out.columns else self.default_sentiment
        out["risk_penalty"] = _num(out["risk_score"], 0.0) if "risk_score" in out.columns else 0.0

        raw_score = (
            out["technical_trend"] * self.weights["technical_trend"]
            + out["capital_strength"] * self.weights["capital_strength"]
            + out["news_catalyst"] * self.weights["news_catalyst"]
            + out["sentiment_heat"] * self.weights["sentiment_heat"]
            - out["risk_penalty"] * self.weights["risk_penalty"]
        )
        out["short_term_score"] = raw_score.clip(0, 100)

        cfg = thresholds or {}
        min_trend = float(cfg.get("min_trend_score", 40))  # 降低到40（原60）
        min_capital = float(cfg.get("min_capital_score", 30))  # 降低到30（原45）
        min_amount = float(cfg.get("min_amount", 5.0e7))  # 降低到5000万（原1亿）
        max_price = float(cfg.get("max_price", 200))  # 提高到200（原100）

        out = out[
            (out["technical_trend"] >= min_trend)
            & (out["capital_strength"] >= min_capital)
            & (out.get("amount", 0).fillna(0) >= min_amount)
            & (out["close"] <= max_price)
        ]
        if out.empty:
            return pd.DataFrame()

        out = out.sort_values(["short_term_score", "capital_strength"], ascending=False).head(top_n).reset_index(drop=True)
        out["rank"] = out.index + 1
        out["strategy"] = "short_term"
        out["buy_trigger"] = "突破近5日高点且放量"
        out["stop_loss_rule"] = "-5%~-8%"
        out["reason"] = out.apply(
            lambda r: f"趋势{r['technical_trend']:.0f}/资金{r['capital_strength']:.0f}/新闻{r['news_catalyst']:.0f}",
            axis=1,
        )
        return out
