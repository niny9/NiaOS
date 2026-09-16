"""Initialize real positions from CSV/JSON."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.portfolio.real_portfolio import RealPortfolioManager
from src.scripts_support.week4_schema import ensure_week4_schema


def _load_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON必须是列表")
    return data


def main() -> None:
    """Import initial position data file."""
    parser = argparse.ArgumentParser(description="初始化真实持仓")
    parser.add_argument("--file", required=True, help="CSV/JSON路径")
    parser.add_argument("--account", default="stock", help="默认账户类型")
    args = parser.parse_args()

    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, settings.log_level)
    ensure_week4_schema(db)
    manager = RealPortfolioManager(db)

    path = Path(args.file)
    rows = _load_json(path) if path.suffix.lower() == ".json" else _load_csv(path)

    for row in rows:
        manager.add_position(
            {
                "account_type": row.get("account_type") or args.account,
                "code": row["code"],
                "name": row.get("name") or row["code"],
                "quantity": float(row["quantity"]),
                "cost_price": float(row["cost_price"]),
                "market_price": float(row.get("market_price") or row["cost_price"]),
                "buy_date": row.get("buy_date"),
                "buy_reason": row.get("buy_reason"),
                "holding_type": row.get("holding_type", "unknown"),
                "stop_loss": float(row["stop_loss"]) if row.get("stop_loss") else None,
                "target_price": float(row["target_price"]) if row.get("target_price") else None,
            }
        )
    print(f"初始化完成: {len(rows)} 条")


if __name__ == "__main__":
    main()
