"""Unified manager for real and model portfolio comparison."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.database.db_manager import DatabaseManager
from src.portfolio.model_portfolio import ModelPortfolioManager
from src.portfolio.real_portfolio import RealPortfolioManager


class PortfolioManager:
    """Aggregate and compare real/model portfolios."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.real = RealPortfolioManager(db)
        self.model = ModelPortfolioManager(db)

    def get_comparison(self) -> Dict[str, Any]:
        """Get side-by-side summary for real and model portfolios."""
        real_summary = self.real.calculate_pnl()
        model_stats = {ptype: self.model.get_stats(ptype) for ptype in ["short_term", "swing", "stable"]}
        return {
            "real": {
                "total_value": real_summary["total_value"],
                "total_pnl_ratio": real_summary["total_pnl_ratio"],
                "position_count": len(real_summary["positions"]),
            },
            "model": {
                k: {
                    "total_return": v.total_return,
                    "max_drawdown": v.max_drawdown,
                    "sharpe": v.sharpe,
                    "trade_count": v.trade_count,
                }
                for k, v in model_stats.items()
            },
        }

    def generate_report(self) -> str:
        """Build markdown report text for holdings overview."""
        c = self.get_comparison()
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"# 持仓对比报告｜{today}", "", "## 真实持仓", f"- 持仓市值：{c['real']['total_value']:.2f}", f"- 总收益率：{c['real']['total_pnl_ratio']:.2%}", f"- 持仓数量：{c['real']['position_count']}只", "", "## 模型组合"]
        for k, v in c["model"].items():
            lines.extend([
                f"### {k}",
                f"- 收益率：{v['total_return']:.2%}",
                f"- 最大回撤：-{v['max_drawdown']:.2%}",
                f"- 夏普：{v['sharpe']:.2f}",
                f"- 交易次数：{v['trade_count']}",
            ])
        return "\\n".join(lines) + "\\n"
