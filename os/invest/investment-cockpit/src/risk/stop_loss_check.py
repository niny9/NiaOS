"""Stop-loss trigger checks."""

from __future__ import annotations

from typing import Any, Dict, List

from src.database.db_manager import DatabaseManager


class StopLossChecker:
    """Check stop-loss trigger status for active positions."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def check(self) -> List[Dict[str, Any]]:
        """Return positions requiring stop-loss actions."""
        rows = self.db.fetch_all(
            """
            SELECT code, name, cost_price, market_price, COALESCE(holding_type, 'stable') AS holding_type
            FROM real_positions
            WHERE status='active'
            """
        )
        alerts: List[Dict[str, Any]] = []
        for row in rows:
            cost = float(row.get("cost_price") or 0.0)
            mkt = float(row.get("market_price") or 0.0)
            if cost <= 0 or mkt <= 0:
                continue
            drawdown = (mkt - cost) / cost
            holding_type = row["holding_type"]

            if holding_type == "short_term" and drawdown <= -0.05:
                alerts.append({"code": row["code"], "level": "高", "message": f"短线跌幅{drawdown:.1%}，触发止损区间-5%~-8%"})
            elif holding_type == "swing" and drawdown <= -0.08:
                alerts.append({"code": row["code"], "level": "高", "message": f"波段跌幅{drawdown:.1%}，触发止损区间-8%~-12%"})
            elif holding_type == "stable" and drawdown <= -0.15:
                alerts.append({"code": row["code"], "level": "中", "message": "稳健仓位回撤较大，请检查长期逻辑是否证伪"})

        return alerts
