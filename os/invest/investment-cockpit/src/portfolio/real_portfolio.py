"""Real portfolio management module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult


@dataclass
class RiskAlert:
    """Risk alert item for a position."""

    code: str
    name: str
    level: str
    reason: str


class RealPortfolioManager:
    """Manage real account positions with PnL and risk checks."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def get_positions(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """Query positions by account type and status."""
        sql = "SELECT * FROM real_positions WHERE 1=1"
        params: List[Any] = []
        if account_type:
            sql += " AND account_type=?"
            params.append(account_type)
        if active_only:
            sql += " AND status='active'"
        sql += " ORDER BY market_value DESC"
        rows = self.db.fetch_all(sql, params)
        return rows

    def add_position(self, data: Dict[str, Any]) -> None:
        """Insert or upsert a position record."""
        payload = {
            "account_type": data["account_type"],
            "code": data["code"],
            "name": data["name"],
            "quantity": float(data["quantity"]),
            "cost_price": float(data["cost_price"]),
            "market_price": data.get("market_price", data.get("cost_price")),
            "market_value": float(data.get("quantity", 0)) * float(data.get("market_price", data.get("cost_price", 0))),
            "position_ratio": float(data.get("position_ratio", 0)),
            "buy_date": data.get("buy_date"),
            "buy_reason": data.get("buy_reason"),
            "holding_type": data.get("holding_type", "unknown"),
            "stop_loss": data.get("stop_loss"),
            "target_price": data.get("target_price"),
            "status": data.get("status", "active"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.db.upsert("real_positions", payload, conflict_columns=["account_type", "code"])
        self.recalculate_position_ratios(account_type=payload["account_type"])
        self.sync_to_feishu()

    def update_position(
        self,
        account_type: str,
        code: str,
        quantity: Optional[float] = None,
        cost_price: Optional[float] = None,
        market_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        target_price: Optional[float] = None,
    ) -> None:
        """Update core fields for one position."""
        current = self.db.fetch_one(
            "SELECT * FROM real_positions WHERE account_type=? AND code=?",
            (account_type, code),
        )
        if not current:
            raise ValueError(f"Position not found: {account_type}/{code}")

        q = float(quantity if quantity is not None else current["quantity"])
        cp = float(cost_price if cost_price is not None else current["cost_price"])
        mp = float(market_price if market_price is not None else (current["market_price"] or cp))

        sql = (
            "UPDATE real_positions SET quantity=?, cost_price=?, market_price=?, market_value=?, "
            "stop_loss=COALESCE(?, stop_loss), target_price=COALESCE(?, target_price), "
            "updated_at=datetime('now') WHERE account_type=? AND code=?"
        )
        self.db.execute(sql, (q, cp, mp, q * mp, stop_loss, target_price, account_type, code))
        self.recalculate_position_ratios(account_type=account_type)
        self.sync_to_feishu()

    def delete_position(self, account_type: str, code: str) -> None:
        """Soft-delete a position."""
        self.db.execute(
            "UPDATE real_positions SET status='closed', quantity=0, market_value=0, updated_at=datetime('now') "
            "WHERE account_type=? AND code=?",
            (account_type, code),
        )
        self.recalculate_position_ratios(account_type=account_type)
        self.sync_to_feishu()

    def calculate_pnl(self, account_type: Optional[str] = None) -> Dict[str, Any]:
        """Calculate PnL summary for selected account(s)."""
        positions = self.get_positions(account_type=account_type)
        realized = 0.0
        total_cost = 0.0
        total_value = 0.0
        items: List[Dict[str, Any]] = []
        for p in positions:
            qty = float(p["quantity"])
            cost = float(p["cost_price"])
            mkt = float(p["market_price"] or cost)
            cost_amt = qty * cost
            val = qty * mkt
            pnl = val - cost_amt
            pnl_ratio = pnl / cost_amt if cost_amt > 0 else 0.0
            items.append({**p, "pnl": pnl, "pnl_ratio": pnl_ratio})
            total_cost += cost_amt
            total_value += val
        return {
            "positions": items,
            "total_cost": total_cost,
            "total_value": total_value,
            "total_pnl": total_value - total_cost + realized,
            "total_pnl_ratio": ((total_value - total_cost + realized) / total_cost) if total_cost > 0 else 0.0,
        }

    def recalculate_position_ratios(self, account_type: Optional[str] = None) -> None:
        """Recompute position ratio using current market value."""
        positions = self.get_positions(account_type=account_type, active_only=True)
        if not positions:
            return
        total = sum(float(p.get("market_value") or 0) for p in positions)
        if total <= 0:
            return
        for p in positions:
            ratio = float(p.get("market_value") or 0) / total
            self.db.execute(
                "UPDATE real_positions SET position_ratio=?, updated_at=datetime('now') WHERE id=?",
                (ratio, p["id"]),
            )

    def check_position_risk(self, account_type: Optional[str] = None) -> List[RiskAlert]:
        """Run risk checks for stop-loss and concentration."""
        positions = self.get_positions(account_type=account_type)
        alerts: List[RiskAlert] = []
        for p in positions:
            code, name = p["code"], p["name"]
            ratio = float(p.get("position_ratio") or 0)
            cost = float(p["cost_price"])
            mkt = float(p.get("market_price") or cost)
            stop_loss = p.get("stop_loss")
            if ratio > 0.20:
                alerts.append(RiskAlert(code=code, name=name, level="high", reason=f"仓位过高: {ratio:.2%}"))
            if stop_loss is not None and mkt < float(stop_loss):
                alerts.append(RiskAlert(code=code, name=name, level="high", reason=f"跌破止损价: {stop_loss}"))
            if (mkt - cost) / cost < -0.10:
                alerts.append(RiskAlert(code=code, name=name, level="medium", reason="浮亏超过10%"))
        return alerts

    def sync_to_feishu(self) -> SyncResult:
        """Sync active positions to Feishu bitable table real_positions."""
        service = FeishuSyncService(self.db, load_app_settings())
        rows: List[Dict[str, Any]] = []
        for p in self.calculate_pnl().get("positions", []):
            rows.append(
                {
                    "股票代码": p["code"],
                    "股票名称": p["name"],
                    "持仓数量": float(p["quantity"]),
                    "成本价": float(p["cost_price"]),
                    "当前价": float(p.get("market_price") or p["cost_price"]),
                    "市值": float(p.get("market_value") or 0),
                    "盈亏金额": float(p.get("pnl") or 0),
                    "盈亏比例": float(p.get("pnl_ratio") or 0),
                    "仓位比例": float(p.get("position_ratio") or 0),
                    "买入日期": _to_feishu_ts(p.get("buy_date")),
                    "持仓类型": _map_holding_type(p.get("holding_type")),
                    "止损位": p.get("stop_loss"),
                    "目标价": p.get("target_price"),
                    "状态": "持有",
                    "唯一键": f"position:{p['account_type']}:{p['code']}",
                }
            )
        return service.sync_rows("real_positions", rows)


def _to_feishu_ts(date_str: Any) -> Optional[int]:
    if not date_str:
        return None
    return int(datetime.strptime(str(date_str)[:10], "%Y-%m-%d").timestamp() * 1000)


def _map_holding_type(v: Any) -> str:
    m = {"short_term": "短线", "swing": "波段", "stable": "稳健", "unknown": "波段"}
    return m.get(str(v or "unknown"), "波段")
