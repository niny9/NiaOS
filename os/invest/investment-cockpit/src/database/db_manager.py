"""SQLite database manager for core CRUD operations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from src.utils.logger import setup_logger


class DatabaseManager:
    """Manage SQLite database connection and basic operations."""

    def __init__(self, db_path: Path, log_level: str = "INFO") -> None:
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
            log_level: Logger level.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(self.__class__.__name__, log_level=log_level)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a SQLite connection with row factory.

        Yields:
            SQLite connection object.

        Raises:
            sqlite3.Error: If connection fails.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            self.logger.exception("Database operation failed: %s", exc)
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        """Execute a single SQL statement.

        Args:
            sql: SQL statement.
            params: Optional SQL parameters.
        """
        with self.get_connection() as conn:
            conn.execute(sql, params or [])

    def executemany(self, sql: str, params_seq: Iterable[Sequence[Any]]) -> None:
        """Execute a SQL statement for multiple parameter sets.

        Args:
            sql: SQL statement.
            params_seq: Iterable of parameter sequences.
        """
        with self.get_connection() as conn:
            conn.executemany(sql, params_seq)

    def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dict.

        Args:
            sql: Query SQL.
            params: Optional SQL parameters.

        Returns:
            Query result as list of dictionaries.
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params or [])
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch one row as dict.

        Args:
            sql: Query SQL.
            params: Optional SQL parameters.

        Returns:
            First row as dictionary or None.
        """
        with self.get_connection() as conn:
            cursor = conn.execute(sql, params or [])
            row = cursor.fetchone()
            return dict(row) if row is not None else None

    def insert_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "append") -> None:
        """Insert pandas DataFrame into a database table.

        Args:
            table_name: Target table name.
            df: DataFrame to insert.
            if_exists: Insert behavior, one of append/replace/fail.
        """
        if df.empty:
            self.logger.warning("Skip inserting empty DataFrame into table: %s", table_name)
            return

        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        self.logger.info("Inserted %s rows into %s", len(df), table_name)

    def upsert(self, table_name: str, data: Dict[str, Any], conflict_columns: Sequence[str]) -> None:
        """Perform SQLite upsert for a single row.

        Args:
            table_name: Target table name.
            data: Column-value mapping.
            conflict_columns: Columns defining conflict key.
        """
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_sql = ", ".join(columns)
        conflict_sql = ", ".join(conflict_columns)

        update_columns = [col for col in columns if col not in conflict_columns]
        update_sql = ", ".join([f"{col}=excluded.{col}" for col in update_columns])

        sql = (
            f"INSERT INTO {table_name} ({col_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_sql}) DO UPDATE SET {update_sql};"
        )
        values = tuple(data[col] for col in columns)

        self.execute(sql, values)

    def table_exists(self, table_name: str) -> bool:
        """Check whether a table exists.

        Args:
            table_name: Target table name.

        Returns:
            True if table exists, otherwise False.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        row = self.fetch_one(sql, (table_name,))
        return row is not None

    def list_tables(self) -> List[str]:
        """List all user tables in database.

        Returns:
            List of table names.
        """
        sql = (
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        rows = self.fetch_all(sql)
        return [row["name"] for row in rows]
