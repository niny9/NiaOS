"""Date utilities for trading-day aware workflows."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List


def to_date(value: str | date | datetime) -> date:
    """Convert a value into ``date``.

    Args:
        value: Date-like value.

    Returns:
        Converted date object.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(value, "%Y-%m-%d").date()


def is_trading_day(value: str | date | datetime) -> bool:
    """Check whether a date is a simple trading day (Mon-Fri)."""
    d = to_date(value)
    return d.weekday() < 5


def generate_date_range(start_date: str, end_date: str, trading_days_only: bool = False) -> List[str]:
    """Generate date strings between two dates.

    Args:
        start_date: Start date, YYYY-MM-DD.
        end_date: End date, YYYY-MM-DD.
        trading_days_only: Whether to keep only weekdays.

    Returns:
        List of date strings.
    """
    start = to_date(start_date)
    end = to_date(end_date)
    days: List[str] = []
    cur = start
    while cur <= end:
        if not trading_days_only or is_trading_day(cur):
            days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


def latest_n_trading_days(n: int, end_date: str | None = None) -> List[str]:
    """Get the latest N weekday trading days.

    Args:
        n: Number of trading days.
        end_date: End anchor date, YYYY-MM-DD; default today.
    """
    anchor = to_date(end_date) if end_date else datetime.today().date()
    out: List[str] = []
    cur = anchor
    while len(out) < n:
        if is_trading_day(cur):
            out.append(cur.isoformat())
        cur -= timedelta(days=1)
    out.reverse()
    return out


def date_to_akshare(value: str) -> str:
    """Convert YYYY-MM-DD date string to YYYYMMDD for AKShare."""
    return value.replace("-", "")
