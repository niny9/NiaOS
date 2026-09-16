"""Fetch stock news and announcements."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import hashlib

import akshare as ak
import pandas as pd

from src.database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch and store stock news."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def _generate_event_id(self, code: str, title: str, date: str) -> str:
        """Generate unique event ID."""
        content = f"{code}_{title}_{date}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def fetch_stock_news(self, code: str, days: int = 7) -> pd.DataFrame:
        """Fetch recent news for a stock.
        
        Args:
            code: Stock code (e.g., "688981")
            days: Number of days to look back
            
        Returns:
            DataFrame with columns: code, title, content, publish_time, source, url
        """
        try:
            df = ak.stock_news_em(symbol=code)
            if df.empty:
                return pd.DataFrame()
            
            # Rename columns
            df = df.rename(columns={
                '关键词': 'keyword',
                '新闻标题': 'title',
                '新闻内容': 'content',
                '发布时间': 'publish_time',
                '文章来源': 'source',
                '新闻链接': 'url'
            })
            
            # Add code column
            df['code'] = code
            
            # Parse publish_time and filter by days
            df['publish_time'] = pd.to_datetime(df['publish_time'])
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df['publish_time'] >= cutoff]
            
            # Select and reorder columns
            df = df[['code', 'title', 'content', 'publish_time', 'source', 'url']]
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch news for {code}: {e}")
            return pd.DataFrame()

    def fetch_batch(self, codes: List[str], days: int = 7) -> pd.DataFrame:
        """Fetch news for multiple stocks.
        
        Args:
            codes: List of stock codes
            days: Number of days to look back
            
        Returns:
            Combined DataFrame
        """
        all_news = []
        
        for code in codes:
            logger.info(f"Fetching news for {code}")
            df = self.fetch_stock_news(code, days=days)
            if not df.empty:
                all_news.append(df)
        
        if not all_news:
            return pd.DataFrame()
        
        return pd.concat(all_news, ignore_index=True)

    def save_to_db(self, df: pd.DataFrame) -> int:
        """Save news to database.
        
        Returns:
            Number of records saved
        """
        if df.empty:
            return 0
        
        count = 0
        for _, row in df.iterrows():
            date_str = row['publish_time'].strftime('%Y-%m-%d')
            event_id = self._generate_event_id(row['code'], row['title'], date_str)
            
            self.db.upsert(
                'news_events',
                {
                    'event_id': event_id,
                    'date': date_str,
                    'source': row['source'],
                    'title': row['title'],
                    'content': row['content'][:1000] if len(row['content']) > 1000 else row['content'],
                    'event_type': 'stock_news',
                    'related_codes': row['code'],
                    'impact_type': None,
                    'impact_duration': None,
                    'confidence': None,
                    'evidence': row['url']
                },
                conflict_columns=['event_id']
            )
            count += 1
        
        return count

    def update_recent_news(self, days: int = 7) -> Dict[str, Any]:
        """Update news for all stocks in watchlist.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary dict
        """
        # Get active stocks from watchlist
        stocks = self.db.fetch_all("""
            SELECT DISTINCT code 
            FROM watchlist 
            WHERE is_active = 1
        """)
        
        codes = [s['code'] for s in stocks]
        logger.info(f"Updating news for {len(codes)} stocks")
        
        # Fetch news
        df = self.fetch_batch(codes, days=days)
        
        # Save to database
        saved = self.save_to_db(df)
        
        summary = {
            'stocks_checked': len(codes),
            'news_fetched': len(df),
            'news_saved': saved,
            'date_range': f"{days} days"
        }
        
        logger.info(f"News update complete: {summary}")
        return summary
