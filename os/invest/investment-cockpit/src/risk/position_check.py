"""Position limit and concentration checks."""

from __future__ import annotations

from typing import Any, Dict, List

from src.database.db_manager import DatabaseManager


class PositionChecker:
    """Check single-position and industry concentration risk."""

    LIMITS: Dict[str, float] = {
        "stable": 0.15,
        "swing": 0.10,
        "short_term": 0.05,
    }

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def check(self) -> List[Dict[str, Any]]:
        """Run position and concentration checks and return alerts."""
        alerts: List[Dict[str, Any]] = []
        rows = self.db.fetch_all(
            """
            SELECT p.code, p.name, p.position_ratio, COALESCE(p.holding_type, 'stable') AS holding_type,
                   w.industry_chain_l1
            FROM real_positions p
            LEFT JOIN watchlist w ON w.code = p.code
            WHERE p.status='active'
            """
        )
        if not rows:
            return alerts

        for row in rows:
            holding_type = row["holding_type"]
            limit = self.LIMITS.get(holding_type, 0.10)
            ratio = float(row.get("position_ratio") or 0.0)
            if ratio > limit:
                alerts.append(
                    {
                        "code": row["code"],
                        "risk": "仓位超限",
                        "level": "高",
                        "message": f"{row['code']} 当前仓位{ratio:.1%}超过{holding_type}上限{limit:.1%}",
                    }
                )

        industry_sum: Dict[str, float] = {}
        for row in rows:
            industry = row.get("industry_chain_l1") or "未知行业"
            industry_sum[industry] = industry_sum.get(industry, 0.0) + float(row.get("position_ratio") or 0.0)
        for industry, total in industry_sum.items():
            if total > 0.40:
                alerts.append(
                    {
                        "code": "*",
                        "risk": "行业集中",
                        "level": "中",
                        "message": f"{industry}仓位集中度{total:.1%}超过40%",
                    }
                )

        return alerts
