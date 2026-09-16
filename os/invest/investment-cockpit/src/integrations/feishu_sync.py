"""High-level sync service for SQLite -> Feishu Bitable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Any, Dict, Iterable, List, Tuple

from src.config.settings import AppSettings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_bitable import FeishuBitable
from src.integrations.feishu_client import FeishuClient


@dataclass
class SyncResult:
    table: str
    created: int
    updated: int
    skipped: int


class FeishuSyncService:
    """Sync rows from local sqlite tables to Feishu with incremental logic."""

    def __init__(self, db: DatabaseManager, settings: AppSettings) -> None:
        self.db = db
        self.settings = settings
        self._enabled = bool(settings.feishu_app_id and settings.feishu_app_secret)
        self._table_ids: Dict[str, str] = {}
        self._bitable: FeishuBitable | None = None
        self._ensure_local_state_table()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def ensure_remote_schema(self) -> Dict[str, str]:
        if not self.enabled:
            return {}
        if not self.settings.feishu_bitable_app_token:
            raise ValueError("FEISHU_BITABLE_APP_TOKEN is empty. Please create a bitable first.")
        self._table_ids = self._get_bitable().ensure_schema()
        return self._table_ids

    def sync_rows(self, logical_table: str, rows: Iterable[Dict[str, Any]], key_field: str = "唯一键") -> SyncResult:
        if not self.enabled:
            return SyncResult(table=logical_table, created=0, updated=0, skipped=0)

        if not self._table_ids:
            self.ensure_remote_schema()
        table_id = self._table_ids[logical_table]

        created = 0
        updated = 0
        skipped = 0
        create_batch: List[Dict[str, Any]] = []

        for row in rows:
            unique_key = str(row.get(key_field) or "").strip()
            if not unique_key:
                skipped += 1
                continue
            row_hash = self._hash_row(row)
            state = self.db.fetch_one(
                "SELECT row_hash, feishu_record_id FROM feishu_sync_state WHERE logical_table=? AND unique_key=?",
                (logical_table, unique_key),
            )
            if state and state.get("row_hash") == row_hash:
                skipped += 1
                continue

            if state and state.get("feishu_record_id"):
                self._get_bitable().update_record(table_id, state["feishu_record_id"], row)
                self._upsert_state(logical_table, unique_key, row_hash, state["feishu_record_id"])
                updated += 1
                continue

            create_batch.append(row)
            self._upsert_state(logical_table, unique_key, row_hash, "")

        if create_batch:
            created = self._get_bitable().batch_create_records(table_id, create_batch)
        return SyncResult(table=logical_table, created=created, updated=updated, skipped=skipped)

    def create_new_bitable(self, name: str) -> Tuple[str, str]:
        """Create a new bitable doc and return app_token, url."""
        if not self.enabled:
            raise ValueError("Feishu is not configured")
        app_token = self._get_client().create_bitable(name=name)
        url = f"https://feishu.cn/base/{app_token}"
        self.settings.feishu_bitable_app_token = app_token
        if self._bitable:
            self._bitable.set_app_token(app_token)
        return app_token, url

    def _get_client(self) -> FeishuClient:
        return FeishuClient(self.settings.feishu_app_id, self.settings.feishu_app_secret)

    def _get_bitable(self) -> FeishuBitable:
        if not self._bitable:
            self._bitable = FeishuBitable(self._get_client(), self.settings.feishu_bitable_app_token)
        return self._bitable

    def _ensure_local_state_table(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS feishu_sync_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logical_table TEXT NOT NULL,
                unique_key TEXT NOT NULL,
                row_hash TEXT NOT NULL,
                feishu_record_id TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(logical_table, unique_key)
            )
            """
        )

    def _upsert_state(self, logical_table: str, unique_key: str, row_hash: str, record_id: str) -> None:
        self.db.upsert(
            "feishu_sync_state",
            {
                "logical_table": logical_table,
                "unique_key": unique_key,
                "row_hash": row_hash,
                "feishu_record_id": record_id,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            conflict_columns=["logical_table", "unique_key"],
        )

    @staticmethod
    def _hash_row(row: Dict[str, Any]) -> str:
        packed = "|".join(f"{k}={row.get(k)}" for k in sorted(row.keys()))
        return hashlib.sha1(packed.encode("utf-8")).hexdigest()
