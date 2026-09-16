"""Database schema definitions for the investment cockpit."""

from __future__ import annotations

from typing import Dict


def get_table_schemas() -> Dict[str, str]:
    """Return SQL DDL statements for all core tables.

    Returns:
        Mapping from table name to CREATE TABLE SQL statement.
    """
    return {
        "stock_basic": """
            CREATE TABLE IF NOT EXISTS stock_basic (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT,
                industry TEXT,
                list_date TEXT,
                delist_date TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """,
        "stock_daily_bar": """
            CREATE TABLE IF NOT EXISTS stock_daily_bar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                pre_close REAL,
                pct_chg REAL,
                volume REAL,
                amount REAL,
                turnover REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(date, code)
            );
        """,
        "watchlist": """
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                industry_chain_l1 TEXT NOT NULL,
                industry_chain_l2 TEXT,
                pool_status TEXT NOT NULL,
                add_date TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(code)
            );
        """,
        "real_positions": """
            CREATE TABLE IF NOT EXISTS real_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                cost_price REAL NOT NULL,
                market_price REAL,
                market_value REAL,
                position_ratio REAL,
                buy_date TEXT,
                buy_reason TEXT,
                holding_type TEXT,
                stop_loss REAL,
                target_price REAL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(account_type, code)
            );
        """,
        "real_trades": """
            CREATE TABLE IF NOT EXISTS real_trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT NOT NULL,
                account_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                amount REAL,
                fee REAL DEFAULT 0,
                strategy_tag TEXT,
                note TEXT,
                executed_by_model INTEGER NOT NULL DEFAULT 1,
                deviation_reason TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """,
        "news_events": """
            CREATE TABLE IF NOT EXISTS news_events (
                event_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                source TEXT,
                title TEXT NOT NULL,
                content TEXT,
                event_type TEXT,
                related_chain TEXT,
                related_codes TEXT,
                impact_type TEXT,
                impact_duration TEXT,
                confidence REAL,
                evidence TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """,
        "factor_scores": """
            CREATE TABLE IF NOT EXISTS factor_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                trend_score REAL,
                momentum_score REAL,
                reversal_score REAL,
                volume_score REAL,
                fundamental_score REAL,
                sentiment_score REAL,
                risk_score REAL,
                final_score REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(date, code)
            );
        """,
        "daily_signals": """
            CREATE TABLE IF NOT EXISTS daily_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                signal TEXT NOT NULL,
                score REAL,
                rank_in_pool INTEGER,
                reason TEXT,
                action_plan TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(date, code, signal)
            );
        """,
        "model_portfolio": """
            CREATE TABLE IF NOT EXISTS model_portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity REAL NOT NULL,
                cost_price REAL NOT NULL,
                market_price REAL,
                market_value REAL,
                position_ratio REAL,
                buy_date TEXT,
                buy_signal_id INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(portfolio_type, code)
            );
        """,
        "review_log": """
            CREATE TABLE IF NOT EXISTS review_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_date TEXT NOT NULL,
                review_date TEXT NOT NULL,
                code TEXT NOT NULL,
                strategy_type TEXT,
                signal_reason TEXT,
                actual_return_1d REAL,
                actual_return_5d REAL,
                actual_return_20d REAL,
                max_drawdown REAL,
                executed INTEGER,
                deviation_reason TEXT,
                conclusion TEXT,
                lesson TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """,
        "parameter_versions": """
            CREATE TABLE IF NOT EXISTS parameter_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_name TEXT NOT NULL UNIQUE,
                created_date TEXT NOT NULL,
                parameters TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                performance_score REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """,
        "parameter_performance": """
            CREATE TABLE IF NOT EXISTS parameter_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version_id INTEGER NOT NULL,
                test_start_date TEXT NOT NULL,
                test_end_date TEXT NOT NULL,
                strategy_type TEXT NOT NULL,
                total_return REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                win_rate REAL,
                profit_loss_ratio REAL,
                trade_count INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (version_id) REFERENCES parameter_versions(id)
            );
        """,
        "optimization_history": """
            CREATE TABLE IF NOT EXISTS optimization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_date TEXT NOT NULL,
                strategy_type TEXT NOT NULL,
                method TEXT NOT NULL,
                param_space TEXT NOT NULL,
                best_version_id INTEGER,
                best_score REAL,
                iterations INTEGER,
                duration_seconds REAL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (best_version_id) REFERENCES parameter_versions(id)
            );
        """,
        "parameter_optimization_history": """
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
        """,
    }


def get_index_statements() -> Dict[str, str]:
    """Return index creation SQL statements.

    Returns:
        Mapping from index name to CREATE INDEX SQL statement.
    """
    return {
        "idx_stock_daily_bar_code_date": (
            "CREATE INDEX IF NOT EXISTS idx_stock_daily_bar_code_date "
            "ON stock_daily_bar(code, date);"
        ),
        "idx_watchlist_pool_status": (
            "CREATE INDEX IF NOT EXISTS idx_watchlist_pool_status "
            "ON watchlist(pool_status);"
        ),
        "idx_real_trades_date_code": (
            "CREATE INDEX IF NOT EXISTS idx_real_trades_date_code "
            "ON real_trades(trade_date, code);"
        ),
        "idx_news_events_date": (
            "CREATE INDEX IF NOT EXISTS idx_news_events_date "
            "ON news_events(date);"
        ),
        "idx_factor_scores_date_code": (
            "CREATE INDEX IF NOT EXISTS idx_factor_scores_date_code "
            "ON factor_scores(date, code);"
        ),
        "idx_daily_signals_date": (
            "CREATE INDEX IF NOT EXISTS idx_daily_signals_date "
            "ON daily_signals(date);"
        ),
        "idx_model_portfolio_type_status": (
            "CREATE INDEX IF NOT EXISTS idx_model_portfolio_type_status "
            "ON model_portfolio(portfolio_type, status);"
        ),
        "idx_review_log_signal_date": (
            "CREATE INDEX IF NOT EXISTS idx_review_log_signal_date "
            "ON review_log(signal_date, review_date);"
        ),
        "idx_parameter_versions_status": (
            "CREATE INDEX IF NOT EXISTS idx_parameter_versions_status "
            "ON parameter_versions(status, created_at);"
        ),
        "idx_parameter_performance_version": (
            "CREATE INDEX IF NOT EXISTS idx_parameter_performance_version "
            "ON parameter_performance(version_id, created_at);"
        ),
        "idx_optimization_history_date": (
            "CREATE INDEX IF NOT EXISTS idx_optimization_history_date "
            "ON optimization_history(optimization_date);"
        ),
        "idx_param_opt_history_date": (
            "CREATE INDEX IF NOT EXISTS idx_param_opt_history_date "
            "ON parameter_optimization_history(optimization_date);"
        ),
    }
