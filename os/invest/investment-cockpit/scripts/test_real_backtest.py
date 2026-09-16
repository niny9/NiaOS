"""Validate optimizer with real backtest engine."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.optimization import ParameterOptimizer
from src.optimization.parameter_manager import ParameterSet
from src.scripts_support.week4_schema import ensure_week4_schema


def ensure_schema(db: DatabaseManager) -> None:
    for _, ddl in get_table_schemas().items():
        db.execute(ddl)
    for _, ddl in get_index_statements().items():
        db.execute(ddl)
    ensure_week4_schema(db)


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)
    ensure_schema(db)

    optimizer = ParameterOptimizer(db)
    start_date = "2026-02-26"
    end_date = "2026-05-26"
    objective = "total_return"

    base = ParameterSet.get_default()
    aggressive = deepcopy(base)
    aggressive.version_name = "aggressive_trial"
    aggressive.trend_params.update({"ma_short": 3, "ma_mid": 12, "ma_long": 30})
    aggressive.momentum_params.update({"ret_5d_weight": 0.5, "ret_20d_weight": 0.3, "ret_60d_weight": 0.2})
    aggressive.short_term_weights.update({"technical_trend": 0.45, "capital_strength": 0.25})

    defensive = deepcopy(base)
    defensive.version_name = "defensive_trial"
    defensive.trend_params.update({"ma_short": 8, "ma_mid": 26, "ma_long": 80})
    defensive.momentum_params.update({"ret_5d_weight": 0.1, "ret_20d_weight": 0.4, "ret_60d_weight": 0.5})
    defensive.short_term_weights.update({"technical_trend": 0.25, "capital_strength": 0.35})

    score_a = optimizer._evaluate_params(aggressive, start_date, end_date, "all", objective)
    score_b = optimizer._evaluate_params(defensive, start_date, end_date, "all", objective)

    print("=== Real Backtest Comparison ===")
    print(f"period={start_date} -> {end_date}, objective={objective}")
    print(f"aggressive score={score_a:.6f}")
    print(f"defensive score={score_b:.6f}")
    if score_a == score_b:
        print("WARNING: two very different parameter sets returned identical score")
    else:
        better = "aggressive" if score_a > score_b else "defensive"
        print(f"better_params={better}")


if __name__ == "__main__":
    main()
