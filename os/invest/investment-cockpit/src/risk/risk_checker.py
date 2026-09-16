"""Unified risk checking manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd

from src.database.db_manager import DatabaseManager
from src.risk.position_check import PositionChecker
from src.risk.stop_loss_check import StopLossChecker


@dataclass
class RiskResult:
    """Risk check summary."""

    level: str
    alerts: List[Dict[str, Any]]


class RiskChecker:
    """Aggregate risk checks and provide stock-level downgrade flags."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.position_checker = PositionChecker(db)
        self.stop_loss_checker = StopLossChecker(db)

    def _high_chasing_check(self) -> List[Dict[str, Any]]:
        rows = self.db.fetch_all(
            """
            WITH latest AS (
                SELECT code, date, pct_chg,
                       ROW_NUMBER() OVER(PARTITION BY code ORDER BY date DESC) AS rn
                FROM stock_daily_bar
                WHERE code IN (SELECT code FROM watchlist)
            )
            SELECT code,
                   SUM(CASE WHEN rn <= 3 AND pct_chg > 5 THEN 1 ELSE 0 END) AS jump_days,
                   SUM(CASE WHEN rn <= 5 AND pct_chg < -1 THEN 1 ELSE 0 END) AS pullback_days
            FROM latest
            GROUP BY code
            """
        )
        alerts: List[Dict[str, Any]] = []
        for row in rows:
            if int(row.get("jump_days") or 0) >= 2 and int(row.get("pullback_days") or 0) == 0:
                alerts.append({"code": row["code"], "risk": "高位追涨", "level": "高", "message": "连续大涨且无回踩，禁止追高"})
        return alerts

    def _liquidity_check(self) -> List[Dict[str, Any]]:
        rows = self.db.fetch_all(
            """
            SELECT b.code, b.amount
            FROM stock_daily_bar b
            JOIN (
                SELECT code, MAX(date) AS max_date
                FROM stock_daily_bar
                WHERE code IN (SELECT code FROM watchlist)
                GROUP BY code
            ) m ON m.code = b.code AND m.max_date = b.date
            """
        )
        alerts: List[Dict[str, Any]] = []
        for row in rows:
            amount = float(row.get("amount") or 0.0)
            if amount < 5.0e7:
                alerts.append({"code": row["code"], "risk": "流动性不足", "level": "中", "message": "近一日成交额低于5000万"})
        return alerts

    def run(self) -> RiskResult:
        """Run all risk checks and return overall risk level."""
        alerts = []
        alerts.extend(self.position_checker.check())
        alerts.extend(self.stop_loss_checker.check())
        alerts.extend(self._high_chasing_check())
        alerts.extend(self._liquidity_check())

        level = "低"
        levels = {a["level"] for a in alerts if "level" in a}
        if "高" in levels:
            level = "高"
        elif "中" in levels:
            level = "中"
        return RiskResult(level=level, alerts=alerts)

    @staticmethod
    def apply_risk_to_candidates(df: pd.DataFrame, alerts: List[Dict[str, Any]]) -> pd.DataFrame:
        """Downgrade or remove candidate stocks based on risk alerts."""
        if df.empty:
            return df
        out = df.copy()
        high_risk_codes = {a["code"] for a in alerts if a.get("level") == "高" and a.get("code") not in (None, "*")}
        mid_risk_codes = {a["code"] for a in alerts if a.get("level") == "中" and a.get("code") not in (None, "*")}

        out["risk_level"] = "低"
        out.loc[out["code"].isin(mid_risk_codes), "risk_level"] = "中"
        out.loc[out["code"].isin(high_risk_codes), "risk_level"] = "高"

        # Remove explicit forbidden buys.
        out = out[~((out["risk_level"] == "高") & (out.get("strategy") == "short_term"))]
        return out.reset_index(drop=True)
