"""Week-4 schema migration helpers."""

from __future__ import annotations

from typing import Dict, List

from src.database.db_manager import DatabaseManager


_REQUIRED_COLUMNS: Dict[str, Dict[str, str]] = {
    "real_trades": {
        "executed_by_model": "INTEGER NOT NULL DEFAULT 1",
        "deviation_reason": "TEXT",
        "status": "TEXT NOT NULL DEFAULT 'active'",
    },
    "model_portfolio": {
        "portfolio_type": "TEXT",
        "quantity": "REAL",
        "cost_price": "REAL",
        "market_price": "REAL",
        "market_value": "REAL",
        "position_ratio": "REAL",
        "buy_date": "TEXT",
        "buy_signal_id": "INTEGER",
        "status": "TEXT NOT NULL DEFAULT 'active'",
        "updated_at": "TEXT NOT NULL DEFAULT (datetime('now'))",
    },
    "review_log": {
        "signal_date": "TEXT",
        "code": "TEXT",
        "strategy_type": "TEXT",
        "signal_reason": "TEXT",
        "actual_return_1d": "REAL",
        "actual_return_5d": "REAL",
        "actual_return_20d": "REAL",
        "max_drawdown": "REAL",
        "executed": "INTEGER",
        "deviation_reason": "TEXT",
        "conclusion": "TEXT",
        "lesson": "TEXT",
    },
}


def ensure_week4_schema(db: DatabaseManager) -> None:
    """Ensure week-4 required tables/columns exist."""
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS model_trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL,
            portfolio_type TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            signal_id INTEGER,
            trade_cost REAL DEFAULT 0,
            pnl_after_cost REAL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS parameter_optimization_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            optimization_date TEXT NOT NULL,
            old_version_name TEXT NOT NULL,
            new_version_name TEXT NOT NULL,
            optimization_method TEXT NOT NULL,
            old_sharpe REAL,
            new_sharpe REAL,
            old_win_rate REAL,
            new_win_rate REAL,
            improvement REAL,
            switched TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(optimization_date, old_version_name, new_version_name, optimization_method)
        );
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS model_account (
            portfolio_type TEXT PRIMARY KEY,
            initial_capital REAL NOT NULL,
            cash REAL NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    for table, columns in _REQUIRED_COLUMNS.items():
        if not db.table_exists(table):
            continue
        existing_rows = db.fetch_all(f"PRAGMA table_info({table})")
        existing = {r["name"] for r in existing_rows}
        for col, ddl in columns.items():
            if col in existing:
                continue
            db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")

    db.execute("CREATE INDEX IF NOT EXISTS idx_real_trades_status_date ON real_trades(status, trade_date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_model_trades_ptype_date ON model_trades(portfolio_type, trade_date)")
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_param_opt_history_date ON parameter_optimization_history(optimization_date)"
    )
