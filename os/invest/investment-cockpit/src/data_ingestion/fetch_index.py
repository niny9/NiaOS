"""Fetch and store major index daily bars."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager
from src.utils.date_utils import date_to_akshare


MAJOR_INDEX: Dict[str, str] = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000688": "科创50",
    "sz399989": "中证医疗",
    "sz399975": "中证证券公司",
}


class IndexFetcher:
    """Fetch index bars and write into stock_daily_bar using prefixed code."""

    def __init__(self, db: DatabaseManager, fetcher: DataFetcher) -> None:
        self.db = db
        self.fetcher = fetcher
        self.logger = fetcher.logger

    @staticmethod
    def _normalize(raw: pd.DataFrame, index_code: str, name: str) -> pd.DataFrame:
        # Sina Finance API returns: date, open, high, low, close, volume
        df = raw.copy()
        
        # Ensure date is string format
        if 'date' in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        
        # Add metadata
        df["code"] = f"INDEX:{index_code}"
        df["name"] = name
        
        # Calculate derived fields
        df["pre_close"] = df["close"].shift(1)
        df["pct_chg"] = ((df["close"] - df["pre_close"]) / df["pre_close"] * 100).round(2)
        
        # Set missing fields
        if "amount" not in df.columns:
            df["amount"] = None
        df["turnover"] = None
        
        # Select and order columns
        return df[["date", "code", "name", "open", "high", "low", "close", "pre_close", "pct_chg", "volume", "amount", "turnover"]]

    def fetch_and_update(self, start_date: str, end_date: str) -> Tuple[int, list[str]]:
        """Fetch major index bars and upsert into DB."""
        written = 0
        failed: list[str] = []
        for idx_code, idx_name in MAJOR_INDEX.items():
            try:
                raw = self.fetcher.get_index_hist(
                    symbol=idx_code,
                    start_date=date_to_akshare(start_date),
                    end_date=date_to_akshare(end_date),
                )
                if raw.empty:
                    continue
                df = self._normalize(raw, index_code=idx_code, name=idx_name)
                for row in df.to_dict("records"):
                    self.db.upsert("stock_daily_bar", row, conflict_columns=["date", "code"])
                    written += 1
            except Exception as exc:  # noqa: BLE001
                self.logger.exception("Index fetch failed %s %s", idx_code, exc)
                failed.append(idx_code)
        self.logger.info("Index update done rows=%s failed=%s", written, len(failed))
        return written, failed
