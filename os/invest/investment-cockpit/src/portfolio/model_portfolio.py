"""Model simulation portfolio manager."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, pstdev
from typing import Any, Dict, List

from src.database.db_manager import DatabaseManager


INITIAL_CAPITAL = 100000.0
SLIPPAGE_BUY = 0.005
SLIPPAGE_SELL = 0.005
FEE_RATE = 0.0003
SELL_TAX = 0.001


@dataclass
class PortfolioStats:
    """Portfolio performance summary."""

    portfolio_type: str
    total_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    profit_loss_ratio: float
    trade_count: int


class ModelPortfolioManager:
    """Manage model-driven virtual portfolios and metrics."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self._model_portfolio_columns = self._load_model_portfolio_columns()

    def _load_model_portfolio_columns(self) -> set[str]:
        """Load current model_portfolio columns for schema compatibility."""
        rows = self.db.fetch_all("PRAGMA table_info(model_portfolio)")
        return {str(r.get("name")) for r in rows if r.get("name")}

    def rebalance_by_signals(self, trade_date: str) -> int:
        """Strictly execute daily signals into model portfolios."""
        signals = self.db.fetch_all(
            "SELECT id, code, signal, reason FROM daily_signals WHERE date=? ORDER BY score DESC",
            (trade_date,),
        )
        if not signals:
            return 0

        changed = 0
        processed_codes = set()
        for signal in signals:
            code = signal["code"]
            if code in processed_codes:
                continue
            strategy = self._map_signal_to_portfolio(signal["signal"])
            if not strategy:
                continue
            price_row = self.db.fetch_one(
                "SELECT close, name FROM stock_daily_bar WHERE date=? AND code=?",
                (trade_date, code),
            )
            if not price_row or price_row.get("close") is None:
                continue
            close_price = float(price_row["close"])
            if signal["signal"] in ["buy", "strong_buy", "short_term", "swing", "stable"]:
                self._execute_buy(
                    portfolio_type=strategy,
                    trade_date=trade_date,
                    code=code,
                    name=price_row.get("name") or code,
                    signal_id=int(signal["id"]),
                    signal_price=close_price,
                )
                changed += 1
            elif signal["signal"] in ["sell", "strong_sell"]:
                self._execute_sell(
                    portfolio_type=strategy,
                    trade_date=trade_date,
                    code=code,
                    signal_id=int(signal["id"]),
                    signal_price=close_price,
                )
                changed += 1
            processed_codes.add(code)
        self.update_market_prices(trade_date)
        return changed

    def update_market_prices(self, trade_date: str) -> None:
        """Refresh model portfolio latest market prices and ratios."""
        positions = self.db.fetch_all("SELECT * FROM model_portfolio WHERE status='active'")
        for pos in positions:
            px = self.db.fetch_one(
                "SELECT close FROM stock_daily_bar WHERE date=? AND code=?",
                (trade_date, pos["code"]),
            )
            if not px or px.get("close") is None:
                continue
            mkt = float(px["close"])
            value = mkt * float(pos["quantity"])
            self.db.execute(
                "UPDATE model_portfolio SET market_price=?, market_value=?, updated_at=datetime('now') WHERE id=?",
                (mkt, value, pos["id"]),
            )
        self._refresh_position_ratio_all()

    def get_stats(self, portfolio_type: str) -> PortfolioStats:
        """Compute return, drawdown, sharpe, win-rate and profit-loss ratio."""
        pnl_rows = self.db.fetch_all(
            """
            SELECT trade_date, pnl_after_cost FROM model_trades
            WHERE portfolio_type=? AND side='sell'
            ORDER BY trade_date
            """,
            (portfolio_type,),
        )
        returns = [float(r["pnl_after_cost"]) / INITIAL_CAPITAL for r in pnl_rows if r["pnl_after_cost"] is not None]
        win_pnls = [float(r["pnl_after_cost"]) for r in pnl_rows if float(r["pnl_after_cost"]) > 0]
        loss_pnls = [abs(float(r["pnl_after_cost"])) for r in pnl_rows if float(r["pnl_after_cost"]) < 0]

        nav_series = self._nav_series(portfolio_type)
        max_dd = self._max_drawdown(nav_series)
        sharpe = 0.0
        if len(returns) >= 2 and pstdev(returns) > 0:
            sharpe = mean(returns) / pstdev(returns) * (252 ** 0.5)

        win_rate = len(win_pnls) / len(pnl_rows) if pnl_rows else 0.0
        pl_ratio = (mean(win_pnls) / mean(loss_pnls)) if win_pnls and loss_pnls else 0.0
        total_return = nav_series[-1] - 1.0 if nav_series else 0.0

        return PortfolioStats(
            portfolio_type=portfolio_type,
            total_return=total_return,
            max_drawdown=max_dd,
            sharpe=sharpe,
            win_rate=win_rate,
            profit_loss_ratio=pl_ratio,
            trade_count=len(pnl_rows),
        )

    def _execute_buy(
        self,
        portfolio_type: str,
        trade_date: str,
        code: str,
        name: str,
        signal_id: int,
        signal_price: float,
    ) -> None:
        cash = self._get_cash(portfolio_type)
        if cash <= 1000:
            return
        budget = cash * 0.10
        fill_price = signal_price * (1 + SLIPPAGE_BUY)
        qty = int(budget / fill_price)
        if qty <= 0:
            return
        amount = qty * fill_price
        fee = amount * FEE_RATE

        pos = self.db.fetch_one(
            "SELECT * FROM model_portfolio WHERE portfolio_type=? AND code=? AND status='active'",
            (portfolio_type, code),
        )
        if pos:
            old_qty = float(pos["quantity"])
            old_cost = float(pos["cost_price"])
            new_qty = old_qty + qty
            new_cost = ((old_qty * old_cost) + amount + fee) / new_qty
            self.db.execute(
                "UPDATE model_portfolio SET quantity=?, cost_price=?, market_price=?, market_value=?, "
                "buy_signal_id=?, updated_at=datetime('now') WHERE id=?",
                (new_qty, new_cost, signal_price, new_qty * signal_price, signal_id, pos["id"]),
            )
        else:
            if "date" in self._model_portfolio_columns:
                self.db.execute(
                    """
                    INSERT INTO model_portfolio (
                        date, portfolio_type, code, name, quantity, cost_price, market_price, market_value,
                        position_ratio, buy_date, buy_signal_id, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        trade_date,
                        portfolio_type,
                        code,
                        name,
                        qty,
                        (amount + fee) / qty,
                        signal_price,
                        qty * signal_price,
                        0.0,
                        trade_date,
                        signal_id,
                    ),
                )
            else:
                self.db.execute(
                    """
                    INSERT INTO model_portfolio (
                        portfolio_type, code, name, quantity, cost_price, market_price, market_value,
                        position_ratio, buy_date, buy_signal_id, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        portfolio_type,
                        code,
                        name,
                        qty,
                        (amount + fee) / qty,
                        signal_price,
                        qty * signal_price,
                        0.0,
                        trade_date,
                        signal_id,
                    ),
                )
        self._set_cash(portfolio_type, cash - amount - fee)
        self._record_trade(portfolio_type, trade_date, code, name, 'buy', qty, fill_price, signal_id, fee, 0.0)

    def _execute_sell(self, portfolio_type: str, trade_date: str, code: str, signal_id: int, signal_price: float) -> None:
        pos = self.db.fetch_one(
            "SELECT * FROM model_portfolio WHERE portfolio_type=? AND code=? AND status='active'",
            (portfolio_type, code),
        )
        if not pos:
            return
        qty = float(pos["quantity"])
        fill_price = signal_price * (1 - SLIPPAGE_SELL)
        amount = qty * fill_price
        fee = amount * FEE_RATE
        tax = amount * SELL_TAX
        cost_amt = qty * float(pos["cost_price"])
        pnl = amount - fee - tax - cost_amt

        cash = self._get_cash(portfolio_type)
        self._set_cash(portfolio_type, cash + amount - fee - tax)

        self.db.execute(
            "UPDATE model_portfolio SET status='closed', quantity=0, market_value=0, updated_at=datetime('now') WHERE id=?",
            (pos["id"],),
        )
        self._record_trade(portfolio_type, trade_date, code, pos.get("name") or code, 'sell', qty, fill_price, signal_id, fee + tax, pnl)

    def _record_trade(
        self,
        portfolio_type: str,
        trade_date: str,
        code: str,
        name: str,
        side: str,
        quantity: float,
        price: float,
        signal_id: int,
        cost: float,
        pnl: float,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO model_trades (
                trade_date, portfolio_type, code, name, side, quantity, price,
                signal_id, trade_cost, pnl_after_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (trade_date, portfolio_type, code, name, side, quantity, price, signal_id, cost, pnl),
        )

    def _get_cash(self, portfolio_type: str) -> float:
        row = self.db.fetch_one("SELECT cash FROM model_account WHERE portfolio_type=?", (portfolio_type,))
        if row:
            return float(row["cash"])
        self.db.execute(
            "INSERT INTO model_account (portfolio_type, initial_capital, cash) VALUES (?, ?, ?)",
            (portfolio_type, INITIAL_CAPITAL, INITIAL_CAPITAL),
        )
        return INITIAL_CAPITAL

    def _set_cash(self, portfolio_type: str, cash: float) -> None:
        self.db.execute("UPDATE model_account SET cash=?, updated_at=datetime('now') WHERE portfolio_type=?", (cash, portfolio_type))

    def _refresh_position_ratio_all(self) -> None:
        for ptype in ["short_term", "swing", "stable"]:
            rows = self.db.fetch_all(
                "SELECT id, market_value FROM model_portfolio WHERE portfolio_type=? AND status='active'",
                (ptype,),
            )
            total = sum(float(r["market_value"] or 0) for r in rows)
            if total <= 0:
                continue
            for r in rows:
                self.db.execute(
                    "UPDATE model_portfolio SET position_ratio=? WHERE id=?",
                    (float(r["market_value"] or 0) / total, r["id"]),
                )

    def _map_signal_to_portfolio(self, signal: str) -> str:
        s = signal.lower()
        if "short" in s:
            return "short_term"
        if "swing" in s:
            return "swing"
        if "stable" in s:
            return "stable"
        return "short_term"

    def _nav_series(self, portfolio_type: str) -> List[float]:
        days = self.db.fetch_all(
            "SELECT DISTINCT trade_date FROM model_trades WHERE portfolio_type=? ORDER BY trade_date",
            (portfolio_type,),
        )
        cash = INITIAL_CAPITAL
        nav: List[float] = [1.0]
        for d in days:
            trades = self.db.fetch_all(
                "SELECT side, quantity, price, trade_cost, pnl_after_cost FROM model_trades WHERE portfolio_type=? AND trade_date=?",
                (portfolio_type, d["trade_date"]),
            )
            for t in trades:
                amt = float(t["quantity"]) * float(t["price"])
                cost = float(t["trade_cost"] or 0)
                if t["side"] == "buy":
                    cash -= amt + cost
                else:
                    cash += amt - cost
            nav.append(cash / INITIAL_CAPITAL)
        return nav

    def _max_drawdown(self, nav: List[float]) -> float:
        if not nav:
            return 0.0
        peak = nav[0]
        max_dd = 0.0
        for v in nav:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        return max_dd
