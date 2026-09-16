"""View real portfolio summary."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.portfolio.real_portfolio import RealPortfolioManager
from src.scripts_support.week4_schema import ensure_week4_schema


def main() -> None:
    """Print current positions and PnL summary."""
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, settings.log_level)
    ensure_week4_schema(db)
    manager = RealPortfolioManager(db)
    summary = manager.calculate_pnl()

    print("当前持仓:")
    for p in summary["positions"]:
        print(f"- {p['account_type']} {p['code']} {p['name']} 数量={p['quantity']:.0f} 成本={p['cost_price']:.2f} 现价={float(p['market_price'] or 0):.2f} 收益={p['pnl_ratio']:.2%}")

    print(f"总成本: {summary['total_cost']:.2f}")
    print(f"总市值: {summary['total_value']:.2f}")
    print(f"总收益率: {summary['total_pnl_ratio']:.2%}")


if __name__ == "__main__":
    main()
