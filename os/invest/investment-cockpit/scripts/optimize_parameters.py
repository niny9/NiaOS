#!/usr/bin/env python3
"""Run parameter optimization from CLI."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.database.schema import get_index_statements, get_table_schemas
from src.optimization import ParameterManager, ParameterOptimizer, ParameterSet
from src.utils.logger import setup_logger


logger = setup_logger("OptimizeParameters")


def _ensure_schema(db: DatabaseManager) -> None:
    for _, ddl in get_table_schemas().items():
        db.execute(ddl)
    for _, ddl in get_index_statements().items():
        db.execute(ddl)


def _default_dates() -> Tuple[str, str]:
    end = datetime.now()
    start = end - timedelta(days=90)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _get_validation_start(end_date: str) -> str:
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end - timedelta(days=30)).strftime("%Y-%m-%d")


def _weight_param_space(weight_keys: List[str]) -> Dict[str, Tuple[float, float]]:
    # 0.0-1.0 with effective 0.05 resolution in random/bayes paths.
    return {f"short_term_weights.{k}": (0.0, 1.0) for k in weight_keys}


def _build_search_space(active: ParameterSet, strategy: str, method: str) -> Dict:
    base_random: Dict[str, Tuple[float, float]] = {
        "trend_params.ma_short": (3, 20),
        "trend_params.ma_mid": (10, 60),
        "filter_thresholds.min_trend_score": (40, 80),
        "risk_params.stop_loss_pct": (0.04, 0.15),
    }

    if strategy in {"short_term", "all"}:
        base_random.update(_weight_param_space(list(active.short_term_weights.keys())))
    if strategy in {"swing", "all"}:
        base_random.update({f"swing_weights.{k}": (0.0, 1.0) for k in active.swing_weights.keys()})
    if strategy in {"stable", "all"}:
        base_random.update({f"stable_weights.{k}": (0.0, 1.0) for k in active.stable_weights.keys()})

    if method != "grid":
        return base_random

    grid: Dict[str, List[float]] = {
        "trend_params.ma_short": [5, 8, 12],
        "trend_params.ma_mid": [20, 30, 45],
        "risk_params.stop_loss_pct": [0.06, 0.08, 0.10],
    }
    for w in list(active.short_term_weights.keys())[:3]:
        grid[f"short_term_weights.{w}"] = [0.2, 0.3, 0.4]
    return grid


def _objective_arg_to_internal(name: str) -> str:
    mapping = {
        "sharpe": "sharpe",
        "win_rate": "win_rate",
        "profit_loss_ratio": "profit_loss_ratio",
        "composite": "composite",
    }
    return mapping[name]


def _write_report(
    report_path: Path,
    method: str,
    strategy: str,
    objective: str,
    train_range: Tuple[str, str],
    valid_range: Tuple[str, str],
    current_score: float,
    best_train_score: float,
    best_valid_score: float,
    switched: bool,
    old_version: str,
    new_version: str,
) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        f"# 参数优化报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 配置",
        f"- method: {method}",
        f"- strategy: {strategy}",
        f"- objective: {objective}",
        f"- train: {train_range[0]} ~ {train_range[1]}",
        f"- valid: {valid_range[0]} ~ {valid_range[1]}",
        "",
        "## 结果",
        f"- 当前参数验证集分数: {current_score:.4f}",
        f"- 新参数训练集最优分数: {best_train_score:.4f}",
        f"- 新参数验证集分数: {best_valid_score:.4f}",
        f"- 是否切换: {'是' if switched else '否'}",
        f"- 旧版本: {old_version}",
        f"- 新版本: {new_version}",
    ]
    report_path.write_text("\n".join(content), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize strategy parameters")
    parser.add_argument("--method", choices=["grid", "random", "bayesian"], default="random")
    parser.add_argument("--strategy", choices=["short_term", "swing", "stable", "all"], default="all")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--objective", choices=["sharpe", "win_rate", "profit_loss_ratio", "composite"], default="sharpe")
    args = parser.parse_args()

    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    _ensure_schema(db)

    manager = ParameterManager(db)
    optimizer = ParameterOptimizer(db)

    train_start, train_end = (args.start_date, args.end_date) if args.start_date and args.end_date else _default_dates()
    valid_start, valid_end = _get_validation_start(train_end), train_end

    try:
        active = manager.get_active_version()
    except ValueError:
        active = ParameterSet.get_default()
        vid = manager.create_version(active, "bootstrap default parameter version")
        manager.activate_version(vid)

    search_space = _build_search_space(active, args.strategy, args.method)
    objective = _objective_arg_to_internal(args.objective)

    if args.method == "grid":
        best_params, best_train_score = optimizer.grid_search(
            param_space=search_space,
            start_date=train_start,
            end_date=train_end,
            strategy_type=args.strategy,
            objective=objective,
            max_combinations=max(10, args.iterations),
        )
    elif args.method == "bayesian":
        best_params, best_train_score = optimizer.bayesian_optimize(
            param_space=search_space,
            n_iterations=args.iterations,
            start_date=train_start,
            end_date=train_end,
            strategy_type=args.strategy,
            objective=objective,
        )
    else:
        best_params, best_train_score = optimizer.random_search(
            param_space=search_space,
            n_iterations=args.iterations,
            start_date=train_start,
            end_date=train_end,
            strategy_type=args.strategy,
            objective=objective,
        )

    current_valid = optimizer.evaluate_parameters(active, valid_start, valid_end, args.strategy, "sharpe")
    best_valid = optimizer.evaluate_parameters(best_params, valid_start, valid_end, args.strategy, "sharpe")

    improvement = best_valid - current_valid
    switched = improvement > 0.2

    best_version_id = db.fetch_one("SELECT id FROM parameter_versions WHERE version_name = ?", (best_params.version_name,))
    if switched and best_version_id is not None:
        manager.activate_version(int(best_version_id["id"]))
        logger.info("Activated optimized version: %s", best_params.version_name)
    elif switched and best_version_id is None:
        new_id = manager.create_version(best_params, "Optimized parameter version from CLI")
        manager.activate_version(new_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_yaml = PROJECT_ROOT / "reports" / f"optimized_parameters_{timestamp}.yaml"
    manager.save_to_yaml(best_params, out_yaml)

    report_path = _write_report(
        report_path=PROJECT_ROOT / "reports" / f"optimization_report_{timestamp}.md",
        method=args.method,
        strategy=args.strategy,
        objective=args.objective,
        train_range=(train_start, train_end),
        valid_range=(valid_start, valid_end),
        current_score=current_valid,
        best_train_score=best_train_score,
        best_valid_score=best_valid,
        switched=switched,
        old_version=active.version_name,
        new_version=best_params.version_name,
    )

    print("Optimization completed")
    print(f"method={args.method} strategy={args.strategy} objective={args.objective}")
    print(f"train_score={best_train_score:.4f} valid_score={best_valid:.4f} current_valid={current_valid:.4f}")
    print(f"improvement={improvement:.4f} switched={'yes' if switched else 'no'}")
    print(f"parameter_yaml={out_yaml}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
