"""Parameter versioning and performance management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger


@dataclass
class ParameterSet:
    """Container for a complete strategy parameter set."""

    version_name: str

    trend_params: Dict[str, Any]
    momentum_params: Dict[str, Any]
    volume_params: Dict[str, Any]

    short_term_weights: Dict[str, float]
    swing_weights: Dict[str, float]
    stable_weights: Dict[str, float]

    filter_thresholds: Dict[str, float]
    risk_params: Dict[str, Any]

    def to_json(self) -> str:
        """Convert parameter set (except version name) to JSON string."""
        payload = {
            "trend_params": self.trend_params,
            "momentum_params": self.momentum_params,
            "volume_params": self.volume_params,
            "short_term_weights": self.short_term_weights,
            "swing_weights": self.swing_weights,
            "stable_weights": self.stable_weights,
            "filter_thresholds": self.filter_thresholds,
            "risk_params": self.risk_params,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str, version_name: str) -> "ParameterSet":
        """Create a parameter set from JSON string and version name."""
        data = json.loads(json_str)
        return cls(
            version_name=version_name,
            trend_params=data.get("trend_params", {}),
            momentum_params=data.get("momentum_params", {}),
            volume_params=data.get("volume_params", {}),
            short_term_weights=data.get("short_term_weights", {}),
            swing_weights=data.get("swing_weights", {}),
            stable_weights=data.get("stable_weights", {}),
            filter_thresholds=data.get("filter_thresholds", {}),
            risk_params=data.get("risk_params", {}),
        )

    @classmethod
    def get_default(cls) -> "ParameterSet":
        """Default parameter set based on current hardcoded values."""
        return cls(
            version_name="default_v1",
            trend_params={"ma_short": 5, "ma_mid": 20, "ma_long": 60},
            momentum_params={
                "ret_5d_weight": 0.2,
                "ret_20d_weight": 0.5,
                "ret_60d_weight": 0.3,
                "relative_strength_weight": 0.5,
            },
            volume_params={
                "turnover_threshold": 5,
                "amount_multiplier": 3,
                "volume_ratio_multiplier": 3,
            },
            short_term_weights={
                "technical_trend": 0.30,
                "capital_strength": 0.30,
                "news_catalyst": 0.20,
                "sentiment_heat": 0.10,
                "risk_penalty": 0.10,
            },
            swing_weights={
                "technical_trend": 0.30,
                "industry_cycle": 0.25,
                "capital_strength": 0.20,
                "fundamental_quality": 0.15,
                "risk_penalty": 0.10,
            },
            stable_weights={
                "fundamental_quality": 0.35,
                "industry_cycle": 0.25,
                "valuation_safety": 0.20,
                "technical_trend": 0.10,
                "institutional_recognition": 0.10,
                "risk_penalty": 1.00,
            },
            filter_thresholds={
                "min_trend_score": 60,
                "min_capital_score": 45,
                "min_amount": 1.0e8,
                "max_price": 100,
            },
            risk_params={
                "stop_loss_pct": 0.08,
                "max_position_ratio": 0.20,
            },
        )


class ParameterManager:
    """Manage parameter versions and their performance records."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.logger = setup_logger("ParameterManager")

    def create_version(self, params: ParameterSet, description: str = "") -> int:
        """Create a new parameter version and return row id."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO parameter_versions (
                    version_name,
                    created_date,
                    parameters,
                    description,
                    status
                ) VALUES (?, ?, ?, ?, 'testing')
                """,
                (
                    params.version_name,
                    datetime.now().strftime("%Y-%m-%d"),
                    params.to_json(),
                    description,
                ),
            )
            version_id = int(cursor.lastrowid)

        self.logger.info("Created parameter version: id=%s, name=%s", version_id, params.version_name)
        return version_id

    def get_version(self, version_id: int) -> ParameterSet:
        """Fetch a parameter set by version id."""
        row = self.db.fetch_one(
            "SELECT id, version_name, parameters FROM parameter_versions WHERE id = ?",
            (version_id,),
        )
        if row is None:
            raise ValueError(f"Parameter version not found: {version_id}")
        return ParameterSet.from_json(row["parameters"], row["version_name"])

    def get_active_version(self) -> ParameterSet:
        """Fetch current active parameter set."""
        row = self.db.fetch_one(
            """
            SELECT id, version_name, parameters
            FROM parameter_versions
            WHERE status = 'active'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        )
        if row is None:
            raise ValueError("No active parameter version found")
        return ParameterSet.from_json(row["parameters"], row["version_name"])

    def list_versions(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List parameter versions, optionally filtered by status."""
        if status:
            return self.db.fetch_all(
                """
                SELECT id, version_name, created_date, description, status, performance_score, created_at
                FROM parameter_versions
                WHERE status = ?
                ORDER BY id DESC
                """,
                (status,),
            )

        return self.db.fetch_all(
            """
            SELECT id, version_name, created_date, description, status, performance_score, created_at
            FROM parameter_versions
            ORDER BY id DESC
            """
        )

    def activate_version(self, version_id: int) -> None:
        """Activate a version and archive all other active/testing versions."""
        target = self.db.fetch_one("SELECT id FROM parameter_versions WHERE id = ?", (version_id,))
        if target is None:
            raise ValueError(f"Parameter version not found: {version_id}")

        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE parameter_versions SET status = 'archived' WHERE id != ? AND status IN ('active', 'testing')",
                (version_id,),
            )
            conn.execute("UPDATE parameter_versions SET status = 'active' WHERE id = ?", (version_id,))

        self.logger.info("Activated parameter version: id=%s", version_id)

    def rollback_to_previous(self) -> Optional[int]:
        """Rollback active version to the most recent archived version."""
        previous = self.db.fetch_one(
            """
            SELECT id
            FROM parameter_versions
            WHERE status = 'archived'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        )
        if previous is None:
            return None
        version_id = int(previous["id"])
        self.activate_version(version_id)
        return version_id

    def save_to_yaml(self, params: ParameterSet, output_path: Path) -> Path:
        """Export a parameter set into YAML file."""
        payload = {
            "version_name": params.version_name,
            "trend_params": params.trend_params,
            "momentum_params": params.momentum_params,
            "volume_params": params.volume_params,
            "short_term_weights": params.short_term_weights,
            "swing_weights": params.swing_weights,
            "stable_weights": params.stable_weights,
            "filter_thresholds": params.filter_thresholds,
            "risk_params": params.risk_params,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)
        return output_path

    def load_from_yaml(self, input_path: Path, version_name: Optional[str] = None) -> ParameterSet:
        """Load parameter set from YAML file."""
        with input_path.open("r", encoding="utf-8") as f:
            payload = yaml.safe_load(f) or {}

        return ParameterSet(
            version_name=version_name or payload.get("version_name", f"yaml_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            trend_params=payload.get("trend_params", {}),
            momentum_params=payload.get("momentum_params", {}),
            volume_params=payload.get("volume_params", {}),
            short_term_weights=payload.get("short_term_weights", {}),
            swing_weights=payload.get("swing_weights", {}),
            stable_weights=payload.get("stable_weights", {}),
            filter_thresholds=payload.get("filter_thresholds", {}),
            risk_params=payload.get("risk_params", {}),
        )

    def record_performance(
        self,
        version_id: int,
        start_date: str,
        end_date: str,
        strategy_type: str,
        metrics: Dict[str, float],
    ) -> None:
        """Persist performance metrics for a version."""
        self.db.execute(
            """
            INSERT INTO parameter_performance (
                version_id,
                test_start_date,
                test_end_date,
                strategy_type,
                total_return,
                max_drawdown,
                sharpe_ratio,
                win_rate,
                profit_loss_ratio,
                trade_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                start_date,
                end_date,
                strategy_type,
                metrics.get("total_return"),
                metrics.get("max_drawdown"),
                metrics.get("sharpe_ratio"),
                metrics.get("win_rate"),
                metrics.get("profit_loss_ratio"),
                int(metrics.get("trade_count", 0)),
            ),
        )

    def get_performance_history(self, version_id: int) -> List[Dict[str, Any]]:
        """Get performance history rows for a version."""
        return self.db.fetch_all(
            """
            SELECT id, version_id, test_start_date, test_end_date, strategy_type,
                   total_return, max_drawdown, sharpe_ratio, win_rate,
                   profit_loss_ratio, trade_count, created_at
            FROM parameter_performance
            WHERE version_id = ?
            ORDER BY id DESC
            """,
            (version_id,),
        )
