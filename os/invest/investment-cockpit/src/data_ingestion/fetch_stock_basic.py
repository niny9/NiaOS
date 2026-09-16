"""Fetch and update stock basic information into stock_basic table."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager


class StockBasicFetcher:
    """Fetch stock basic data and upsert to database."""

    def __init__(self, db: DatabaseManager, fetcher: DataFetcher) -> None:
        self.db = db
        self.fetcher = fetcher
        self.logger = fetcher.logger

    @staticmethod
    def _extract_list_date(detail_df: pd.DataFrame) -> str | None:
        if detail_df.empty:
            return None
        cols = set(detail_df.columns)
        if not {"item", "value"}.issubset(cols):
            return None
        rows = detail_df[detail_df["item"].astype(str).str.contains("上市", na=False)]
        if rows.empty:
            return None
        raw = str(rows.iloc[0]["value"])
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        return None

    def fetch_dataframe(self, incremental: bool = True) -> pd.DataFrame:
        """Fetch stock basic dataframe from AKShare.

        Args:
            incremental: If true, fetch detailed fields only for new codes.
        """
        try:
            code_name = self.fetcher.get_stock_code_name()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "get_stock_code_name failed, fallback to multi_source spot for code-name: %s",
                exc,
            )
            spot_for_code_name = self.fetcher.multi_source.get_stock_spot().data
            field_map = {"代码": "code", "名称": "name"}
            code_name = spot_for_code_name.rename(
                columns={k: v for k, v in field_map.items() if k in spot_for_code_name.columns}
            )
            if not {"code", "name"}.issubset(code_name.columns):
                self.logger.warning("Fallback spot missing code/name columns")
                return pd.DataFrame()
            code_name = code_name[[c for c in ["code", "name"] if c in code_name.columns]].copy()
            code_name = code_name.drop_duplicates(subset=["code", "name"])

        if code_name.empty:
            return pd.DataFrame()

        code_name = code_name.rename(columns={"code": "code", "name": "name"})
        code_name = code_name[["code", "name"]].copy()

        try:
            # Force multi-source path so source failures can fallback to sample data.
            spot = self.fetcher.multi_source.get_stock_spot().data
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("multi_source spot failed, fallback to DataFetcher.get_stock_spot: %s", exc)
            spot = self.fetcher.get_stock_spot()
        field_map: Dict[str, str] = {
            "代码": "code",
            "名称": "name",
            "所属行业": "industry",
        }
        for k, v in field_map.items():
            if k in spot.columns:
                spot = spot.rename(columns={k: v})
        spot_use = spot[[c for c in ["code", "name", "industry"] if c in spot.columns]].copy()
        if "industry" not in spot_use.columns:
            spot_use["industry"] = ""

        merged = code_name.merge(spot_use, on=["code", "name"], how="left")
        if "industry" not in merged.columns:
            merged["industry"] = ""
        merged["industry"] = merged["industry"].fillna("")
        merged["market"] = merged["code"].astype(str).str[:1].map({"6": "SH", "0": "SZ", "3": "SZ", "8": "BJ", "4": "BJ"}).fillna("UNKNOWN")
        merged["is_active"] = 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        merged["updated_at"] = now

        existing_codes: set[str] = set()
        if incremental:
            rows = self.db.fetch_all("SELECT code FROM stock_basic")
            existing_codes = {str(r["code"]) for r in rows}

        list_dates: List[str | None] = []
        for _, row in merged.iterrows():
            code = str(row["code"])
            if incremental and code in existing_codes:
                list_dates.append(None)
                continue
            try:
                detail = self.fetcher.get_stock_detail(code)
                list_dates.append(self._extract_list_date(detail))
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed stock detail for %s: %s", code, exc)
                list_dates.append(None)

        merged["list_date"] = list_dates
        merged["delist_date"] = None
        merged["created_at"] = now
        return merged[["code", "name", "market", "industry", "list_date", "delist_date", "is_active", "created_at", "updated_at"]]

    def update_to_db(self, incremental: bool = True) -> int:
        """Upsert stock basic rows into database."""
        df = self.fetch_dataframe(incremental=incremental)
        if df.empty:
            self.logger.warning("No stock basic data fetched")
            return 0

        for row in df.to_dict("records"):
            self.db.upsert("stock_basic", row, conflict_columns=["code"])

        self.logger.info("Upserted stock_basic rows: %s", len(df))
        return len(df)
