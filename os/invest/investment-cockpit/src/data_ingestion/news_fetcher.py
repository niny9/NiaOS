"""Portfolio stock news fetcher."""

from __future__ import annotations

from typing import Any, Dict, List

import akshare as ak
import pandas as pd

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger


class NewsFetcher:
    """Fetch stock news from Eastmoney via AKShare."""

    def __init__(self, db: DatabaseManager, log_level: str = "INFO") -> None:
        self.db = db
        self.logger = setup_logger(self.__class__.__name__, log_level=log_level)

    def fetch_stock_news(self, code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch latest stock news and return structured rows."""
        try:
            df = ak.stock_news_em(symbol=code)
        except Exception as exc:
            self.logger.exception("Failed to fetch stock news for %s: %s", code, exc)
            return []

        if df is None or df.empty:
            return []

        normalized = self._normalize_news_df(df, code=code)
        if normalized.empty:
            return []

        rows = normalized.head(max(limit, 1)).to_dict(orient="records")
        return rows

    def fetch_portfolio_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch news for all active holdings."""
        positions = self.db.fetch_all(
            """
            SELECT DISTINCT code, name
            FROM real_positions
            WHERE status='active'
            ORDER BY code
            """
        )
        all_news: List[Dict[str, Any]] = []
        for position in positions:
            code = str(position.get("code") or "").strip()
            if not code:
                continue
            one_stock_news = self.fetch_stock_news(code=code, limit=limit)
            for item in one_stock_news:
                item["name"] = position.get("name") or item.get("name") or code
            all_news.extend(one_stock_news)
        return all_news

    def _normalize_news_df(self, df: pd.DataFrame, code: str) -> pd.DataFrame:
        """Normalize AKShare stock_news_em columns into stable schema."""
        renamed = df.rename(
            columns={
                "关键词": "keyword",
                "新闻标题": "title",
                "新闻内容": "content",
                "发布时间": "publish_time",
                "文章来源": "source",
                "新闻链接": "url",
            }
        ).copy()
        for col in ["title", "publish_time", "source", "url", "content", "keyword"]:
            if col not in renamed.columns:
                renamed[col] = ""
        renamed["code"] = code
        renamed["publish_time"] = renamed["publish_time"].astype(str)
        renamed["source"] = renamed["source"].fillna("").astype(str)
        renamed["title"] = renamed["title"].fillna("").astype(str)
        renamed["url"] = renamed["url"].fillna("").astype(str)
        renamed["content"] = renamed["content"].fillna("").astype(str)
        normalized = renamed[["code", "keyword", "title", "content", "publish_time", "source", "url"]]
        normalized = normalized.sort_values(by="publish_time", ascending=False)
        return normalized
