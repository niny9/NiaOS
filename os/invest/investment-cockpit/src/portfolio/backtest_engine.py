"""Simple backtest engine for signal based simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.database.db_manager import DatabaseManager
from src.portfolio.model_portfolio import ModelPortfolioManager


@dataclass
class BacktestReport:
    """Backtest output payload."""

    start_date: str
    end_date: str
    rebalanced_days: int
    stats: Dict[str, Dict[str, float]]


class BacktestEngine:
    """Replay historical signals and generate summary metrics."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.model = ModelPortfolioManager(db)

    def run(self, start_date: str, end_date: str) -> BacktestReport:
        """Run backtest between date range based on `daily_signals`."""
        days = self.db.fetch_all(
            "SELECT DISTINCT date FROM daily_signals WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date),
        )
        rebalanced_days = 0
        for day in days:
            changed = self.model.rebalance_by_signals(day["date"])
            if changed > 0:
                rebalanced_days += 1

        stats = {}
        for p in ["short_term", "swing", "stable"]:
            s = self.model.get_stats(p)
            stats[p] = {
                "total_return": s.total_return,
                "max_drawdown": s.max_drawdown,
                "sharpe": s.sharpe,
                "win_rate": s.win_rate,
                "profit_loss_ratio": s.profit_loss_ratio,
                "trade_count": float(s.trade_count),
            }

        return BacktestReport(
            start_date=start_date,
            end_date=end_date,
            rebalanced_days=rebalanced_days,
            stats=stats,
        )
