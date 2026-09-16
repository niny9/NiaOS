"""Watchlist pool CRUD and query interfaces."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult


class PoolManager:
    """Manage watchlist pools and stock statuses."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def add_stock(
        self,
        code: str,
        name: str,
        industry_chain_l1: str,
        industry_chain_l2: str,
        pool_status: str = "观察池",
        note: str = "",
    ) -> None:
        """Add or upsert one stock into watchlist."""
        today = date.today().isoformat()
        self.db.upsert(
            "watchlist",
            {
                "code": code,
                "name": name,
                "industry_chain_l1": industry_chain_l1,
                "industry_chain_l2": industry_chain_l2,
                "pool_status": pool_status,
                "add_date": today,
                "note": note,
                "updated_at": today,
            },
            conflict_columns=["code"],
        )
        self.sync_to_feishu()

    def update_status(self, code: str, pool_status: str, note: str = "") -> None:
        """Update stock pool status."""
        sql = """
        UPDATE watchlist
        SET pool_status=?, note=CASE WHEN ?='' THEN note ELSE ? END, updated_at=datetime('now')
        WHERE code=?
        """
        self.db.execute(sql, (pool_status, note, note, code))
        self.sync_to_feishu()

    def remove_stock(self, code: str) -> None:
        """Delete a stock from watchlist."""
        self.db.execute("DELETE FROM watchlist WHERE code=?", (code,))
        self.sync_to_feishu()

    def get_by_chain(self, industry_chain_l1: str, industry_chain_l2: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query stocks by industry chain."""
        if industry_chain_l2:
            return self.db.fetch_all(
                "SELECT * FROM watchlist WHERE industry_chain_l1=? AND industry_chain_l2=? ORDER BY code",
                (industry_chain_l1, industry_chain_l2),
            )
        return self.db.fetch_all(
            "SELECT * FROM watchlist WHERE industry_chain_l1=? ORDER BY industry_chain_l2, code",
            (industry_chain_l1,),
        )

    def get_by_status(self, pool_status: str) -> List[Dict[str, Any]]:
        """Query stocks by status."""
        return self.db.fetch_all("SELECT * FROM watchlist WHERE pool_status=? ORDER BY updated_at DESC", (pool_status,))

    def list_all(self) -> List[Dict[str, Any]]:
        """List all watchlist stocks."""
        return self.db.fetch_all("SELECT * FROM watchlist ORDER BY industry_chain_l1, industry_chain_l2, code")

    def sync_to_feishu(self) -> SyncResult:
        """Sync watchlist rows to Feishu bitable table watchlist."""
        service = FeishuSyncService(self.db, load_app_settings())
        rows = []
        for w in self.list_all():
            rows.append(
                {
                    "股票代码": w["code"],
                    "股票名称": w["name"],
                    "一级分类": w["industry_chain_l1"],
                    "二级分类": w.get("industry_chain_l2") or "",
                    "池状态": w["pool_status"],
                    "加入日期": _to_feishu_ts(w.get("add_date")),
                    "备注": w.get("note") or "",
                    "唯一键": f"watch:{w['code']}",
                }
            )
        return service.sync_rows("watchlist", rows)


def _to_feishu_ts(value: Any) -> Optional[int]:
    if not value:
        return None
    return int(datetime.strptime(str(value)[:10], "%Y-%m-%d").timestamp() * 1000)
