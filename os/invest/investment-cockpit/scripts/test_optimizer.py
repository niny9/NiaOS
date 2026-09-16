"""Quick validation script for optimization engine (Phase 2)."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.optimization import ParameterOptimizer


def ensure_schema(db: DatabaseManager) -> None:
    for _, ddl in get_table_schemas().items():
        db.execute(ddl)
    for _, ddl in get_index_statements().items():
        db.execute(ddl)


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)
    ensure_schema(db)

    optimizer = ParameterOptimizer(db)

    print("=== Grid Search ===")
    grid_space = {
        "trend_params.ma_short": [5, 10],
        "trend_params.ma_mid": [20, 30],
    }
    best_params, best_score = optimizer.grid_search(
        param_space=grid_space,
        start_date="2026-02-26",
        end_date="2026-05-26",
        strategy_type="short_term",
        objective="sharpe_ratio",
    )
    print(f"best_score={best_score:.4f}, version={best_params.version_name}")

    print("=== Random Search ===")
    random_space = {
        "trend_params.ma_short": (5, 15),
        "trend_params.ma_mid": (15, 30),
    }
    best_params, best_score = optimizer.random_search(
        param_space=random_space,
        n_iterations=10,
        start_date="2026-02-26",
        end_date="2026-05-26",
        strategy_type="short_term",
    )
    print(f"best_score={best_score:.4f}, version={best_params.version_name}")

    print("=== Bayesian Optimize ===")
    bayes_space = {
        "trend_params.ma_short": (5.0, 15.0),
        "trend_params.ma_mid": (15.0, 30.0),
    }
    try:
        best_params, best_score = optimizer.bayesian_optimize(
            param_space=bayes_space,
            n_iterations=20,
            start_date="2026-02-26",
            end_date="2026-05-26",
            strategy_type="short_term",
        )
        print(f"best_score={best_score:.4f}, version={best_params.version_name}")
    except ModuleNotFoundError as exc:
        print(f"Bayesian optimize skipped: {exc}")

    history_count = db.fetch_one("SELECT COUNT(*) AS cnt FROM optimization_history")
    version_count = db.fetch_one("SELECT COUNT(*) AS cnt FROM parameter_versions")
    print(f"optimization_history rows={history_count['cnt']}, parameter_versions rows={version_count['cnt']}")


if __name__ == "__main__":
    main()
