"""Market regime detector for weekly auto-optimization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

import pandas as pd

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger


class MarketRegime(Enum):
    """市场制度类型"""

    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"


@dataclass
class RegimeInfo:
    """市场制度信息"""

    regime: MarketRegime
    trend: float
    volatility: float
    confidence: float
    description: str


class MarketRegimeDetector:
    """市场制度检测器"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.logger = setup_logger("RegimeDetector")

    def detect_regime(self, index_code: str = "INDEX:sh000001") -> RegimeInfo:
        """检测当前市场制度。"""
        rows = self.db.fetch_all(
            """
            SELECT date, close
            FROM stock_daily_bar
            WHERE code = ? AND close IS NOT NULL
            ORDER BY date DESC
            LIMIT 120
            """,
            (index_code,),
        )
        if not rows:
            self.logger.warning("No index bars found for %s, fallback to sideways regime", index_code)
            return RegimeInfo(
                regime=MarketRegime.SIDEWAYS,
                trend=0.0,
                volatility=0.0,
                confidence=0.0,
                description="震荡市（缺少指数数据）",
            )

        prices = pd.Series([float(r["close"]) for r in reversed(rows)])
        trend = self._calculate_trend(prices)
        volatility = self._calculate_volatility(prices)

        if trend > 0.05 and volatility < 0.02:
            regime = MarketRegime.BULL
            confidence = min(1.0, (trend / 0.10) + ((0.02 - volatility) / 0.02)) / 2
            description = "牛市（趋势上行且波动较低）"
        elif trend < -0.05 and volatility > 0.03:
            regime = MarketRegime.BEAR
            confidence = min(1.0, (abs(trend) / 0.10) + ((volatility - 0.03) / 0.03)) / 2
            description = "熊市（趋势下行且波动较高）"
        else:
            regime = MarketRegime.SIDEWAYS
            trend_score = max(0.0, 1.0 - min(1.0, abs(trend) / 0.05))
            vol_score = max(0.0, 1.0 - min(1.0, abs(volatility - 0.025) / 0.025))
            confidence = (trend_score + vol_score) / 2
            description = "震荡市（趋势与波动均未触发牛熊阈值）"

        return RegimeInfo(
            regime=regime,
            trend=trend,
            volatility=volatility,
            confidence=max(0.0, min(1.0, confidence)),
            description=description,
        )

    def detect_current_regime(self, index_code: str = "INDEX:sh000001") -> RegimeInfo:
        """Backward-compatible alias."""
        return self.detect_regime(index_code=index_code)

    def get_regime_parameters(self, regime: MarketRegime) -> Dict[str, Any]:
        """根据市场制度返回推荐参数调整。"""
        if regime == MarketRegime.BULL:
            return {
                "short_term_weights": {
                    "technical_trend": 0.35,
                    "capital_strength": 0.30,
                },
                "risk_params": {"stop_loss_pct": 0.06},
                "note": "牛市：增加短线权重，降低止损阈值",
            }

        if regime == MarketRegime.BEAR:
            return {
                "stable_weights": {
                    "fundamental_quality": 0.40,
                    "industry_cycle": 0.30,
                },
                "risk_params": {"stop_loss_pct": 0.10},
                "note": "熊市：增加稳健权重，提高止损阈值",
            }

        return {
            "swing_weights": {
                "technical_trend": 0.35,
                "industry_cycle": 0.30,
            },
            "risk_params": {"stop_loss_pct": 0.08},
            "note": "震荡市：增加波段权重，使用默认风控参数",
        }

    def _calculate_trend(self, prices: pd.Series) -> float:
        """计算60日趋势（收益率）。"""
        if len(prices) < 61:
            return 0.0
        start = float(prices.iloc[-61])
        end = float(prices.iloc[-1])
        if start <= 0:
            return 0.0
        return (end / start) - 1.0

    def _calculate_volatility(self, prices: pd.Series) -> float:
        """计算20日波动率（标准差）。"""
        if len(prices) < 21:
            return 0.0
        returns = prices.pct_change().dropna()
        window_returns = returns.iloc[-20:]
        if window_returns.empty:
            return 0.0
        return float(window_returns.std(ddof=0))


class RegimeDetector(MarketRegimeDetector):
    """Backward-compatible alias for existing imports."""
