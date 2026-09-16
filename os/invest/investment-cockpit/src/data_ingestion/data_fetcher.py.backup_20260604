"""Unified AKShare data fetcher with retry and logging."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass
from typing import Any, Callable, Optional

import pandas as pd

from src.utils.logger import setup_logger
from src.data_ingestion.multi_source_fetcher import MultiSourceFetcher


@dataclass
class FetcherConfig:
    """Configuration for API fetch behavior."""

    retry_times: int = 2
    retry_interval_sec: float = 0.8
    request_interval_sec: float = 0.15


class DataFetcher:
    """Wrap AKShare interfaces with retry, throttle, and logging."""

    def __init__(self, log_level: str = "INFO", config: Optional[FetcherConfig] = None) -> None:
        """Initialize data fetcher.

        Args:
            log_level: Logger level.
            config: Optional fetcher config.
        """
        self.config = config or FetcherConfig()
        self.logger = setup_logger(self.__class__.__name__, log_level=log_level)
        self._ak = self._load_akshare()
        self.multi_source = MultiSourceFetcher(log_level=log_level)
        self.last_data_source = ""

    @staticmethod
    def _load_akshare() -> Any:
        """Load AKShare module.

        Raises:
            ImportError: If akshare is not installed.
        """
        try:
            import akshare as ak  # type: ignore
            # Disable proxy
            import os
            os.environ['NO_PROXY'] = '*'
            os.environ['no_proxy'] = '*'
        except ImportError as exc:
            raise ImportError("akshare is required. Run: pip install -r requirements.txt") from exc
        return ak

    def _call_with_retry(self, func: Callable[..., pd.DataFrame], **kwargs: Any) -> pd.DataFrame:
        """Call a dataframe function with retry and wait."""
        last_err: Optional[Exception] = None
        for attempt in range(1, self.config.retry_times + 1):
            try:
                df = func(**kwargs)
                time.sleep(self.config.request_interval_sec)
                if not isinstance(df, pd.DataFrame):
                    raise ValueError("AKShare response is not DataFrame")
                return df
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                self.logger.warning("Fetch failed attempt=%s/%s kwargs=%s err=%s", attempt, self.config.retry_times, kwargs, exc)
                if attempt < self.config.retry_times:
                    time.sleep(self.config.retry_interval_sec)

        raise RuntimeError(f"Fetch failed after retries: {kwargs}") from last_err

    def get_stock_code_name(self) -> pd.DataFrame:
        """Fetch A-share code-name list."""
        def _normalize_code_name(df: pd.DataFrame) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame(columns=["code", "name"])

            candidates = {
                "code": ["code", "代码", "证券代码", "symbol"],
                "name": ["name", "名称", "证券简称"],
            }

            code_col = next((col for col in candidates["code"] if col in df.columns), None)
            name_col = next((col for col in candidates["name"] if col in df.columns), None)
            if not code_col or not name_col:
                raise ValueError(f"无法从数据中识别 code/name 列, columns={list(df.columns)}")

            out = df[[code_col, name_col]].copy()
            out.columns = ["code", "name"]
            return out

        try:
            df = self._call_with_retry(self._ak.stock_info_a_code_name)
            self.last_data_source = "akshare"
            return _normalize_code_name(df)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("stock_code_name akshare failed, fallback to multi_source spot: %s", exc)
            result = self.multi_source.get_stock_spot()
            self.last_data_source = result.source
            self.logger.info("stock_code_name source=%s rows=%s", result.source, len(result.data))
            return _normalize_code_name(result.data)

    def get_stock_spot(self) -> pd.DataFrame:
        """Fetch A-share spot market snapshot."""
        if os.getenv("DATA_SOURCE_MULTI_ENABLED", "1") == "1":
            result = self.multi_source.get_stock_spot()
            self.last_data_source = result.source
            self.logger.info("stock_spot source=%s rows=%s", result.source, len(result.data))
            return result.data
        return self._call_with_retry(self._ak.stock_zh_a_spot_em)

    def get_stock_hist(self, symbol: str, start_date: str, end_date: str, adjust: str = "") -> pd.DataFrame:
        """Fetch A-share historical bars using Tencent API.

        Args:
            symbol: Stock code like 000001.
            start_date: YYYYMMDD.
            end_date: YYYYMMDD.
            adjust: Forward/backward adjust flag.
        """
        if os.getenv("DATA_SOURCE_MULTI_ENABLED", "1") == "1":
            result = self.multi_source.get_stock_prices([symbol], start_date, end_date)
            self.last_data_source = result.source
            self.logger.info("stock_hist source=%s symbol=%s rows=%s", result.source, symbol, len(result.data))
            return result.data

        # Backward-compatible AKShare-only path
        tx_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        return self._call_with_retry(self._ak.stock_zh_a_hist_tx, symbol=tx_symbol, start_date=start_date, end_date=end_date, adjust=adjust)

    def get_stock_detail(self, symbol: str) -> pd.DataFrame:
        """Fetch stock detail information for one symbol."""
        return self._call_with_retry(self._ak.stock_individual_info_em, symbol=symbol)

    def get_index_hist(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch index daily bars via Sina Finance (fallback from eastmoney)."""
        # Use Sina Finance API which is more stable
        df = self._call_with_retry(
            self._ak.stock_zh_index_daily,
            symbol=symbol,
        )
        
        # Filter by date range
        df['date'] = pd.to_datetime(df['date'])
        start = pd.to_datetime(start_date, format='%Y%m%d')
        end = pd.to_datetime(end_date, format='%Y%m%d')
        df = df[(df['date'] >= start) & (df['date'] <= end)]
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        return df
