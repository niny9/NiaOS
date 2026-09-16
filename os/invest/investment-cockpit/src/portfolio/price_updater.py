"""Batch update real position prices from A-share spot quotes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager


class PositionPriceUpdater:
    """Update real position market price/value using one spot batch fetch."""

    def __init__(self, db: DatabaseManager, fetcher: DataFetcher) -> None:
        self.db = db
        self.fetcher = fetcher
        self.logger = fetcher.logger

    @staticmethod
    def _normalize_spot_df(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "代码" not in df.columns:
            return pd.DataFrame(columns=["代码", "最新价"])
        out = df.copy()
        out["代码"] = out["代码"].astype(str).str.zfill(6)
        return out

    def _get_active_positions(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all(
            """
            SELECT id, account_type, code, name, quantity, cost_price
            FROM real_positions
            WHERE status='active'
            ORDER BY code
            """
        )

    def update_all_positions(self) -> Dict[str, Any]:
        """Fetch full spot quotes once and update all active positions."""
        positions = self._get_active_positions()
        if not positions:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_positions": 0,
                "updated_count": 0,
                "missing_count": 0,
                "skipped_count": 0,
                "missing_codes": [],
            }

        spot = self._normalize_spot_df(self.fetcher.get_stock_spot())
        price_map: Dict[str, float] = {}
        for row in spot.to_dict("records"):
            code = str(row.get("代码", "")).zfill(6)
            raw_price = row.get("最新价")
            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                continue
            if price > 0:
                price_map[code] = price

        updated_count = 0
        skipped_count = 0
        missing_codes: List[str] = []

        for p in positions:
            code = str(p["code"]).zfill(6)
            latest_price = price_map.get(code)
            if latest_price is None:
                missing_codes.append(code)
                continue

            quantity = float(p["quantity"])
            market_value = quantity * latest_price
            if market_value <= 0:
                skipped_count += 1
                continue

            self.db.execute(
                """
                UPDATE real_positions
                SET market_price=?,
                    market_value=?,
                    updated_at=datetime('now')
                WHERE id=?
                """,
                (latest_price, market_value, p["id"]),
            )
            updated_count += 1

        self.logger.info(
            "Position price update done total=%s updated=%s missing=%s skipped=%s",
            len(positions),
            updated_count,
            len(missing_codes),
            skipped_count,
        )
        return {
            "timestamp": datetime.now().isoformat(),
            "total_positions": len(positions),
            "updated_count": updated_count,
            "missing_count": len(missing_codes),
            "skipped_count": skipped_count,
            "missing_codes": missing_codes,
        }

    def get_position_summary(self) -> Dict[str, Any]:
        """Return current active position PnL summary."""
        rows = self.db.fetch_all(
            """
            SELECT
                code, name, quantity, cost_price, market_price, market_value
            FROM real_positions
            WHERE status='active'
            ORDER BY market_value DESC
            """
        )
        if not rows:
            return {
                "position_count": 0,
                "total_cost": 0.0,
                "total_market_value": 0.0,
                "total_profit": 0.0,
                "total_profit_pct": 0.0,
                "best_position": None,
                "worst_position": None,
            }

        enriched: List[Dict[str, Any]] = []
        total_cost = 0.0
        total_market_value = 0.0
        for r in rows:
            qty = float(r["quantity"])
            cost_price = float(r["cost_price"])
            market_price = float(r["market_price"] if r["market_price"] is not None else cost_price)
            cost_amt = qty * cost_price
            market_amt = qty * market_price
            profit = market_amt - cost_amt
            profit_pct = (profit / cost_amt) if cost_amt > 0 else 0.0
            item = {
                **r,
                "cost_value": cost_amt,
                "market_value": market_amt,
                "profit": profit,
                "profit_pct": profit_pct,
            }
            enriched.append(item)
            total_cost += cost_amt
            total_market_value += market_amt

        best = max(enriched, key=lambda x: x["profit_pct"])
        worst = min(enriched, key=lambda x: x["profit_pct"])
        total_profit = total_market_value - total_cost
        return {
            "position_count": len(enriched),
            "total_cost": total_cost,
            "total_market_value": total_market_value,
            "total_profit": total_profit,
            "total_profit_pct": (total_profit / total_cost) if total_cost > 0 else 0.0,
            "best_position": {
                "code": best["code"],
                "name": best["name"],
                "profit_pct": best["profit_pct"],
            },
            "worst_position": {
                "code": worst["code"],
                "name": worst["name"],
                "profit_pct": worst["profit_pct"],
            },
        }
