"""Fetch and update stock daily bars into stock_daily_bar table."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List, Tuple

import pandas as pd

from src.data_ingestion.data_fetcher import DataFetcher
from src.database.db_manager import DatabaseManager
from src.utils.data_validator import DataValidator
from src.utils.date_utils import date_to_akshare


class StockPriceFetcher:
    """Fetch stock prices for one or multiple symbols."""

    def __init__(self, db: DatabaseManager, fetcher: DataFetcher) -> None:
        self.db = db
        self.fetcher = fetcher
        self.logger = fetcher.logger

    @staticmethod
    def _normalize_hist_df(raw: pd.DataFrame, code: str, name: str | None = None) -> pd.DataFrame:
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover",
        }
        df = raw.rename(columns=rename_map).copy()
        
        # Ensure date column
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        
        # Add code and name
        df["code"] = code
        df["name"] = name
        
        # Calculate pre_close
        df["pre_close"] = df["close"].shift(1)
        
        # Calculate missing fields if not present
        if "pct_chg" not in df.columns and "pre_close" in df.columns:
            df["pct_chg"] = ((df["close"] - df["pre_close"]) / df["pre_close"] * 100).round(2)
        
        # Calculate volume from amount if missing (amount / avg_price)
        if "volume" not in df.columns or df["volume"].isna().all():
            avg_price = (df["high"] + df["low"] + df["close"]) / 3
            df["volume"] = (df["amount"] / avg_price).fillna(0).round(0).astype('Int64')
        
        # Estimate turnover if missing (rough proxy based on amount)
        if "turnover" not in df.columns or df["turnover"].isna().all():
            df["turnover"] = (df["amount"] / 1e8).clip(0, 30).round(2)
        
        # Select and order columns
        keep = ["date", "code", "name", "open", "high", "low", "close", "pre_close", "pct_chg", "volume", "amount", "turnover"]
        return df[keep]

    def fetch_single(self, code: str, start_date: str, end_date: str, name: str | None = None) -> pd.DataFrame:
        """Fetch one stock daily bars."""
        raw = self.fetcher.get_stock_hist(symbol=code, start_date=date_to_akshare(start_date), end_date=date_to_akshare(end_date))
        if raw.empty:
            return raw
        df = self._normalize_hist_df(raw, code=code, name=name)
        report = DataValidator.build_quality_report(df, code=code)
        if not report["is_valid"]:
            self.logger.warning("Data quality issue for %s: %s", code, report["issues"])
        return df

    def _upsert_price_rows(self, df: pd.DataFrame) -> int:
        rows = df.to_dict("records")
        if not rows:
            return 0

        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        update_columns = [c for c in columns if c not in {"date", "code"}]
        update_clause = ", ".join([f"{c}=excluded.{c}" for c in update_columns])
        sql = (
            f"INSERT INTO stock_daily_bar ({', '.join(columns)}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT(date, code) DO UPDATE SET {update_clause}"
        )
        values = [tuple(row[col] for col in columns) for row in rows]

        with self.db.get_connection() as conn:
            conn.executemany(sql, values)
            conn.commit()
        return len(rows)

    def fetch_batch(self, codes: Iterable[Tuple[str, str]], start_date: str, end_date: str) -> Tuple[int, List[str]]:
        """Fetch multiple stocks.

        Args:
            codes: Iterable of (code, name).
            start_date: YYYY-MM-DD.
            end_date: YYYY-MM-DD.

        Returns:
            (written_rows, failed_codes)
        """
        written = 0
        failed: List[str] = []
        code_list = list(codes)
        max_workers = 6

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self.fetch_single, code=code, start_date=start_date, end_date=end_date, name=name): (idx, code)
                for idx, (code, name) in enumerate(code_list, 1)
            }

            for future in as_completed(future_map):
                idx, code = future_map[future]
                try:
                    df = future.result()
                    if df.empty:
                        self.logger.info("[%s] empty price data %s", idx, code)
                        continue
                    written += self._upsert_price_rows(df)
                    self.logger.info("[%s] wrote bars code=%s rows=%s", idx, code, len(df))
                except Exception as exc:  # noqa: BLE001
                    self.logger.exception("[%s] failed code=%s err=%s", idx, code, exc)
                    failed.append(code)

        return written, failed
