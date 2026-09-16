"""Trade sync service for real account."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult
from src.portfolio.real_portfolio import RealPortfolioManager


@dataclass
class TradeInput:
    """Structured trade input payload."""

    trade_date: str
    account_type: str
    code: str
    name: str
    side: str
    price: float
    quantity: float
    reason: str
    executed_by_model: bool
    deviation_reason: Optional[str] = None
    holding_type: str = "short_term"


class TradeSyncService:
    """Sync manual trades into DB and auto-adjust positions."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.real = RealPortfolioManager(db)

    def sync_trade(self, trade: TradeInput) -> int:
        """Record a trade and update real positions."""
        self._validate_trade(trade)
        amount = trade.price * trade.quantity
        self.db.execute(
            """
            INSERT INTO real_trades (
                trade_date, account_type, code, name, side, quantity, price, amount,
                strategy_tag, note, executed_by_model, deviation_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.trade_date,
                trade.account_type,
                trade.code,
                trade.name,
                trade.side,
                trade.quantity,
                trade.price,
                amount,
                trade.holding_type,
                trade.reason,
                1 if trade.executed_by_model else 0,
                trade.deviation_reason,
            ),
        )

        self._apply_trade_to_position(trade)
        row = self.db.fetch_one("SELECT MAX(trade_id) AS id FROM real_trades")
        self.sync_to_feishu()
        return int(row["id"]) if row else 0

    def undo_latest_trade(self, account_type: Optional[str] = None) -> bool:
        """Undo latest trade by reversing it and marking canceled."""
        sql = "SELECT * FROM real_trades WHERE status='active'"
        params: List[Any] = []
        if account_type:
            sql += " AND account_type=?"
            params.append(account_type)
        sql += " ORDER BY trade_id DESC LIMIT 1"
        trade = self.db.fetch_one(sql, params)
        if not trade:
            return False

        reverse_side = "sell" if trade["side"] == "buy" else "buy"
        reverse = TradeInput(
            trade_date=datetime.now().strftime("%Y-%m-%d"),
            account_type=trade["account_type"],
            code=trade["code"],
            name=trade.get("name") or "",
            side=reverse_side,
            price=float(trade["price"]),
            quantity=float(trade["quantity"]),
            reason=f"撤销交易#{trade['trade_id']}",
            executed_by_model=True,
            deviation_reason=None,
            holding_type=trade.get("strategy_tag") or "unknown",
        )
        self.sync_trade(reverse)
        self.db.execute("UPDATE real_trades SET status='canceled' WHERE trade_id=?", (trade["trade_id"],))
        self.sync_to_feishu()
        return True

    def sync_to_feishu(self) -> SyncResult:
        """Sync active trade rows to Feishu bitable table real_trades."""
        service = FeishuSyncService(self.db, load_app_settings())
        rows = self.db.fetch_all("SELECT * FROM real_trades WHERE status='active' ORDER BY trade_id DESC LIMIT 1000")
        payload = []
        for t in rows:
            payload.append(
                {
                    "交易日期": _to_feishu_ts(t["trade_date"]),
                    "股票代码": t["code"],
                    "股票名称": t.get("name") or "",
                    "操作类型": "买入" if t["side"] == "buy" else "卖出",
                    "价格": float(t["price"]),
                    "数量": float(t["quantity"]),
                    "金额": float(t.get("amount") or (float(t["price"]) * float(t["quantity"]))),
                    "原因": t.get("note") or "",
                    "是否按模型": "是" if int(t.get("executed_by_model") or 0) == 1 else "否",
                    "偏离原因": t.get("deviation_reason") or "",
                    "唯一键": f"trade:{t['trade_id']}",
                }
            )
        return service.sync_rows("real_trades", payload)

    def import_from_json(self, path: Path) -> int:
        """Import trades from a JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON内容必须是交易列表")
        count = 0
        for row in data:
            trade = TradeInput(
                trade_date=row["trade_date"],
                account_type=row.get("account_type", "stock"),
                code=row["code"],
                name=row.get("name", ""),
                side=row["side"],
                price=float(row["price"]),
                quantity=float(row["quantity"]),
                reason=row.get("reason", ""),
                executed_by_model=bool(row.get("executed_by_model", True)),
                deviation_reason=row.get("deviation_reason"),
                holding_type=row.get("holding_type", "short_term"),
            )
            self.sync_trade(trade)
            count += 1
        return count

    def interactive_input(self) -> TradeInput:
        """Read one trade from CLI interactive prompt."""
        print("交易同步：")
        trade_date = input("日期(YYYY-MM-DD，默认今天): ").strip() or datetime.now().strftime("%Y-%m-%d")
        code = input("代码: ").strip()
        name = input("名称: ").strip()
        side = input("操作(买入/卖出): ").strip()
        side = "buy" if side in ["买入", "buy", "BUY"] else "sell"
        price = float(input("价格: ").strip())
        quantity = float(input("数量: ").strip())
        reason = input("原因: ").strip()
        by_model = input("是否按模型建议(是/否): ").strip() in ["是", "y", "Y", "yes"]
        deviation = None
        if not by_model:
            deviation = input("偏离原因: ").strip()
        account_type = input("账户类型(默认stock): ").strip() or "stock"
        holding_type = input("持仓类型(short_term/swing/stable，默认short_term): ").strip() or "short_term"

        return TradeInput(
            trade_date=trade_date,
            account_type=account_type,
            code=code,
            name=name,
            side=side,
            price=price,
            quantity=quantity,
            reason=reason,
            executed_by_model=by_model,
            deviation_reason=deviation,
            holding_type=holding_type,
        )

    def _validate_trade(self, trade: TradeInput) -> None:
        if not trade.code:
            raise ValueError("code不能为空")
        if trade.side not in {"buy", "sell"}:
            raise ValueError("side必须为buy/sell")
        if trade.price <= 0 or trade.quantity <= 0:
            raise ValueError("price和quantity必须大于0")

    def _apply_trade_to_position(self, trade: TradeInput) -> None:
        pos = self.db.fetch_one(
            "SELECT * FROM real_positions WHERE account_type=? AND code=?",
            (trade.account_type, trade.code),
        )

        if trade.side == "buy":
            if not pos:
                self.real.add_position(
                    {
                        "account_type": trade.account_type,
                        "code": trade.code,
                        "name": trade.name,
                        "quantity": trade.quantity,
                        "cost_price": trade.price,
                        "market_price": trade.price,
                        "buy_date": trade.trade_date,
                        "buy_reason": trade.reason,
                        "holding_type": trade.holding_type,
                        "status": "active",
                    }
                )
                return
            old_qty = float(pos["quantity"])
            old_cost = float(pos["cost_price"])
            new_qty = old_qty + trade.quantity
            new_cost = ((old_qty * old_cost) + (trade.quantity * trade.price)) / new_qty
            self.real.update_position(
                account_type=trade.account_type,
                code=trade.code,
                quantity=new_qty,
                cost_price=new_cost,
                market_price=trade.price,
            )
            return

        if not pos:
            raise ValueError(f"卖出失败，当前无持仓: {trade.code}")

        old_qty = float(pos["quantity"])
        if trade.quantity > old_qty:
            raise ValueError(f"卖出数量超出持仓: {trade.code} 持仓{old_qty}")

        left_qty = old_qty - trade.quantity
        if left_qty == 0:
            self.real.delete_position(trade.account_type, trade.code)
            return
        self.real.update_position(
            account_type=trade.account_type,
            code=trade.code,
            quantity=left_qty,
            cost_price=float(pos["cost_price"]),
            market_price=trade.price,
        )


def _to_feishu_ts(date_str: Any) -> Optional[int]:
    if not date_str:
        return None
    return int(datetime.strptime(str(date_str)[:10], "%Y-%m-%d").timestamp() * 1000)
