from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.optimization.parameter_manager import ParameterManager, ParameterSet
from src.optimization.optimizer import ParameterOptimizer


class OptimizationModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test.db"
        self.db = DatabaseManager(self.db_path)

        for _, ddl in get_table_schemas().items():
            self.db.execute(ddl)
        for _, ddl in get_index_statements().items():
            self.db.execute(ddl)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_parameter_version_create_and_activate(self) -> None:
        manager = ParameterManager(self.db)
        p1 = ParameterSet.get_default()
        p1.version_name = "v1"
        id1 = manager.create_version(p1, "test v1")
        manager.activate_version(id1)

        p2 = ParameterSet.get_default()
        p2.version_name = "v2"
        p2.risk_params["stop_loss_pct"] = 0.09
        id2 = manager.create_version(p2, "test v2")
        manager.activate_version(id2)

        active = manager.get_active_version()
        self.assertEqual(active.version_name, "v2")

    def test_optimizer_random_search_runs(self) -> None:
        optimizer = ParameterOptimizer(self.db)

        def fake_eval(params, start_date, end_date, strategy_type, objective):
            return float(params.risk_params.get("stop_loss_pct", 0.0))

        optimizer._evaluate_params = fake_eval  # type: ignore[attr-defined]

        best_params, best_score = optimizer.random_search(
            param_space={"risk_params.stop_loss_pct": (0.05, 0.15)},
            n_iterations=5,
            start_date="2026-01-01",
            end_date="2026-03-31",
            strategy_type="all",
            objective="sharpe",
        )

        self.assertIsNotNone(best_params)
        self.assertGreaterEqual(best_score, 0.05)

    def test_evaluate_parameters_wrapper(self) -> None:
        optimizer = ParameterOptimizer(self.db)

        def fake_eval(params, start_date, end_date, strategy_type, objective):
            self.assertEqual(objective, "sharpe_ratio")
            return 1.23

        optimizer._evaluate_params = fake_eval  # type: ignore[attr-defined]
        score = optimizer.evaluate_parameters(
            params=ParameterSet.get_default(),
            start_date="2026-01-01",
            end_date="2026-03-31",
            strategy_type="all",
            objective="sharpe",
        )
        self.assertEqual(score, 1.23)


if __name__ == "__main__":
    unittest.main()
