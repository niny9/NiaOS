"""Parameter optimization engine with grid/random/Bayesian methods."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import itertools
import json
import os
from pathlib import Path
import random
import shutil
import tempfile
import time
from typing import Any, Dict, List, Tuple

from src.database.db_manager import DatabaseManager
from src.factors.factor_calculator import FactorCalculator
from src.optimization.parameter_manager import ParameterManager, ParameterSet
from src.portfolio.backtest_engine import BacktestEngine
from src.scoring.strategy_scorer import StrategyScorer
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger


def _parse_param_path(path: str, params: ParameterSet, value: Any) -> None:
    """Parse param path and set value, e.g. trend_params.ma_short."""
    parts = path.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid parameter path: {path}")

    group_name, key = parts
    if not hasattr(params, group_name):
        raise ValueError(f"Unknown parameter group: {group_name}")

    group = getattr(params, group_name)
    if not isinstance(group, dict):
        raise ValueError(f"Parameter group is not dict: {group_name}")

    group[key] = value


def _get_param_value(path: str, params: ParameterSet) -> Any:
    """Get value from parameter path."""
    parts = path.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid parameter path: {path}")

    group_name, key = parts
    if not hasattr(params, group_name):
        raise ValueError(f"Unknown parameter group: {group_name}")

    group = getattr(params, group_name)
    if not isinstance(group, dict):
        raise ValueError(f"Parameter group is not dict: {group_name}")
    return group.get(key)


def _generate_combinations(param_space: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Generate all parameter combinations for grid search."""
    keys = list(param_space.keys())
    value_lists = [param_space[k] for k in keys]
    return [dict(zip(keys, values)) for values in itertools.product(*value_lists)]


class ParameterOptimizer:
    """Optimization engine for strategy parameters."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.param_manager = ParameterManager(db)
        self.logger = setup_logger("ParameterOptimizer")
        self._last_strategy_type = "all"

    @staticmethod
    def _normalize_objective(objective: str) -> str:
        mapping = {
            "sharpe": "sharpe_ratio",
            "sharpe_ratio": "sharpe_ratio",
            "win_rate": "win_rate",
            "profit_loss_ratio": "profit_loss_ratio",
            "total_return": "total_return",
            "composite": "composite",
        }
        if objective not in mapping:
            raise ValueError(f"Unsupported objective: {objective}")
        return mapping[objective]

    def _new_candidate(self) -> ParameterSet:
        try:
            return deepcopy(self.param_manager.get_active_version())
        except Exception:  # pylint: disable=broad-except
            return deepcopy(ParameterSet.get_default())

    @staticmethod
    def _enforce_weight_constraints(params: ParameterSet) -> None:
        """Ensure strategy weight sums equal 1.0."""
        for field in ["short_term_weights", "swing_weights", "stable_weights"]:
            weights = getattr(params, field, {})
            if not isinstance(weights, dict) or not weights:
                continue
            cleaned = {k: max(0.0, min(1.0, float(v))) for k, v in weights.items()}
            total = sum(cleaned.values())
            if total <= 0:
                n = len(cleaned)
                normalized = {k: round(1.0 / n, 4) for k in cleaned}
            else:
                normalized = {k: round(v / total, 4) for k, v in cleaned.items()}
            residual = round(1.0 - sum(normalized.values()), 4)
            if normalized:
                first_key = next(iter(normalized.keys()))
                normalized[first_key] = round(normalized[first_key] + residual, 4)
            setattr(params, field, normalized)

    def grid_search(
        self,
        param_space: Dict[str, List[Any]],
        start_date: str,
        end_date: str,
        strategy_type: str = "all",
        objective: str = "sharpe_ratio",
        max_combinations: int = 100,
    ) -> Tuple[ParameterSet, float]:
        """Grid search best parameter set."""
        started_at = time.time()
        self._last_strategy_type = strategy_type

        combinations = _generate_combinations(param_space)
        if len(combinations) > max_combinations:
            self.logger.warning(
                "Grid combinations exceed max (%s > %s), sampling subset.",
                len(combinations),
                max_combinations,
            )
            combinations = random.sample(combinations, max_combinations)

        best_params = None
        best_score = float("-inf")

        for combo in combinations:
            candidate = self._new_candidate()
            for path, value in combo.items():
                _parse_param_path(path, candidate, value)
            self._enforce_weight_constraints(candidate)

            score = self.evaluate_parameters(candidate, start_date, end_date, strategy_type, objective)
            if score > best_score:
                best_score = score
                best_params = deepcopy(candidate)

        if best_params is None:
            raise ValueError("No valid parameter combination found in grid search")

        best_params.version_name = f"grid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        best_version_id = self.param_manager.create_version(best_params, description="Best result from grid search")
        self._record_optimization(
            method="grid_search",
            param_space=param_space,
            best_version_id=best_version_id,
            best_score=best_score,
            iterations=len(combinations),
            duration=time.time() - started_at,
        )
        return best_params, best_score

    def random_search(
        self,
        param_space: Dict[str, Tuple[Any, Any]],
        n_iterations: int,
        start_date: str,
        end_date: str,
        strategy_type: str = "all",
        objective: str = "sharpe_ratio",
    ) -> Tuple[ParameterSet, float]:
        """Random search best parameter set."""
        started_at = time.time()
        self._last_strategy_type = strategy_type

        best_params = None
        best_score = float("-inf")

        for _ in range(n_iterations):
            candidate = self._new_candidate()
            for path, bounds in param_space.items():
                low, high = bounds
                if isinstance(low, int) and isinstance(high, int):
                    value = random.randint(low, high)
                elif isinstance(low, (int, float)) and isinstance(high, (int, float)):
                    value = random.uniform(float(low), float(high))
                else:
                    value = random.choice([low, high])
                _parse_param_path(path, candidate, value)
            self._enforce_weight_constraints(candidate)

            score = self.evaluate_parameters(candidate, start_date, end_date, strategy_type, objective)
            if score > best_score:
                best_score = score
                best_params = deepcopy(candidate)

        if best_params is None:
            raise ValueError("No valid parameter set found in random search")

        best_params.version_name = f"random_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        best_version_id = self.param_manager.create_version(best_params, description="Best result from random search")
        self._record_optimization(
            method="random_search",
            param_space=param_space,
            best_version_id=best_version_id,
            best_score=best_score,
            iterations=n_iterations,
            duration=time.time() - started_at,
        )
        return best_params, best_score

    def bayesian_optimize(
        self,
        param_space: Dict[str, Tuple[float, float]],
        n_iterations: int,
        start_date: str,
        end_date: str,
        strategy_type: str = "all",
        objective: str = "sharpe_ratio",
        n_initial_points: int = 10,
    ) -> Tuple[ParameterSet, float]:
        """Bayesian optimization using skopt.gp_minimize."""
        try:
            from skopt import gp_minimize
            from skopt.space import Real
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Bayesian optimization requires scikit-optimize. Install with: pip install scikit-optimize scipy"
            ) from exc

        started_at = time.time()
        self._last_strategy_type = strategy_type

        names = list(param_space.keys())
        dimensions = [Real(bounds[0], bounds[1], name=name) for name, bounds in param_space.items()]

        best_score_holder = {"score": float("-inf"), "params": None}

        def objective_fn(values: List[float]) -> float:
            candidate = self._new_candidate()
            for i, value in enumerate(values):
                _parse_param_path(names[i], candidate, value)
            self._enforce_weight_constraints(candidate)
            score = self.evaluate_parameters(candidate, start_date, end_date, strategy_type, objective)
            if score > best_score_holder["score"]:
                best_score_holder["score"] = score
                best_score_holder["params"] = deepcopy(candidate)
            return -score

        result = gp_minimize(
            func=objective_fn,
            dimensions=dimensions,
            n_calls=n_iterations,
            n_initial_points=min(n_initial_points, n_iterations),
            random_state=42,
        )

        best_params = best_score_holder["params"]
        if best_params is None:
            best_params = self._new_candidate()
            for i, value in enumerate(result.x):
                _parse_param_path(names[i], best_params, value)
            self._enforce_weight_constraints(best_params)

        best_score = -float(result.fun)
        best_params.version_name = f"bayes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        best_version_id = self.param_manager.create_version(
            best_params, description="Best result from bayesian optimization"
        )
        self._record_optimization(
            method="bayesian",
            param_space=param_space,
            best_version_id=best_version_id,
            best_score=best_score,
            iterations=n_iterations,
            duration=time.time() - started_at,
        )
        return best_params, best_score

    def evaluate_parameters(
        self,
        params: ParameterSet,
        start_date: str,
        end_date: str,
        strategy_type: str = "all",
        objective: str = "sharpe",
    ) -> float:
        """Public evaluation entry for optimization scripts."""
        normalized = self._normalize_objective(objective)
        return self._evaluate_params(params, start_date, end_date, strategy_type, normalized)

    def _evaluate_params(
        self,
        params: ParameterSet,
        start_date: str,
        end_date: str,
        strategy_type: str,
        objective: str,
    ) -> float:
        """Evaluate parameter set performance using real backtest."""
        supported = {"sharpe_ratio", "total_return", "win_rate", "profit_loss_ratio", "composite"}
        if objective not in supported:
            raise ValueError(f"Unsupported objective: {objective}")

        tmp_file = tempfile.NamedTemporaryFile(prefix="opt_backtest_", suffix=".db", delete=False)
        tmp_db_path = tmp_file.name
        tmp_file.close()
        try:
            shutil.copy2(self.db.db_path, tmp_db_path)
            tmp_db = DatabaseManager(db_path=Path(tmp_db_path))
            ensure_week4_schema(tmp_db)

            trial_params = deepcopy(params)
            trial_params.version_name = f"trial_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            tmp_param_manager = ParameterManager(tmp_db)
            trial_version_id = tmp_param_manager.create_version(
                trial_params,
                description=f"Temporary trial for {objective} ({start_date} to {end_date})",
            )

            factor_calculator = FactorCalculator(tmp_db, params=trial_params)
            factor_calculator.run_incremental(start_date, end_date)

            scorer = StrategyScorer(tmp_db, params=trial_params)
            days = tmp_db.fetch_all(
                "SELECT DISTINCT date FROM factor_scores WHERE date BETWEEN ? AND ? ORDER BY date",
                (start_date, end_date),
            )
            for row in days:
                day = row["date"]
                scores = scorer.score_all(trade_date=day)
                scorer.write_daily_signals(scores, trade_date=day)

            report = BacktestEngine(tmp_db).run(start_date=start_date, end_date=end_date)
            key_map = {
                "sharpe_ratio": "sharpe",
                "total_return": "total_return",
                "win_rate": "win_rate",
                "profit_loss_ratio": "profit_loss_ratio",
            }
            score = self._score_report(report.stats, strategy_type, objective, key_map)

            selected = (
                report.stats[strategy_type]
                if strategy_type in report.stats
                else {
                    k: sum(report.stats[p].get(k, 0.0) for p in ["short_term", "swing", "stable"]) / 3.0
                    for k in ["total_return", "max_drawdown", "sharpe", "win_rate", "profit_loss_ratio", "trade_count"]
                }
            )
            perf_payload = {
                "total_return": float(selected.get("total_return", 0.0)),
                "max_drawdown": float(selected.get("max_drawdown", 0.0)),
                "sharpe_ratio": float(selected.get("sharpe", 0.0)),
                "win_rate": float(selected.get("win_rate", 0.0)),
                "profit_loss_ratio": float(selected.get("profit_loss_ratio", 0.0)),
                "trade_count": int(selected.get("trade_count", 0.0)),
            }
            tmp_param_manager.record_performance(trial_version_id, start_date, end_date, strategy_type, perf_payload)
            tmp_db.execute(
                "UPDATE parameter_versions SET performance_score = ? WHERE id = ?",
                (float(score), trial_version_id),
            )
            return float(score)
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.exception("Real backtest evaluation failed: %s", exc)
            return -999.0
        finally:
            if os.path.exists(tmp_db_path):
                os.remove(tmp_db_path)

    @staticmethod
    def _score_report(
        stats: Dict[str, Dict[str, float]],
        strategy_type: str,
        objective: str,
        key_map: Dict[str, str],
    ) -> float:
        if strategy_type == "all":
            selected = {
                k: sum(float(stats[p].get(k, 0.0)) for p in ["short_term", "swing", "stable"]) / 3.0
                for k in ["total_return", "max_drawdown", "sharpe", "win_rate", "profit_loss_ratio"]
            }
        else:
            if strategy_type not in stats:
                raise ValueError(f"Unsupported strategy_type: {strategy_type}")
            selected = {k: float(v) for k, v in stats[strategy_type].items()}

        if objective == "composite":
            return (
                selected.get("sharpe", 0.0) * 0.5
                + selected.get("win_rate", 0.0) * 0.3
                + selected.get("profit_loss_ratio", 0.0) * 0.2
            )

        return float(selected.get(key_map[objective], 0.0))

    def _record_optimization(
        self,
        method: str,
        param_space: Dict,
        best_version_id: int,
        best_score: float,
        iterations: int,
        duration: float,
    ) -> None:
        """Record optimization history into optimization_history table."""
        self.db.execute(
            """
            INSERT INTO optimization_history (
                optimization_date,
                strategy_type,
                method,
                param_space,
                best_version_id,
                best_score,
                iterations,
                duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d"),
                self._last_strategy_type,
                method,
                json.dumps(param_space, ensure_ascii=False, sort_keys=True),
                best_version_id,
                best_score,
                iterations,
                duration,
            ),
        )
