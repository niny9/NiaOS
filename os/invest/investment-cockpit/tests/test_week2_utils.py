"""Unit tests for week-2 utility modules."""

from __future__ import annotations

import unittest

import pandas as pd

from src.utils.data_validator import DataValidator
from src.utils.date_utils import generate_date_range, is_trading_day, latest_n_trading_days


class TestDateUtils(unittest.TestCase):
    """Test date utility functions."""

    def test_is_trading_day(self) -> None:
        self.assertTrue(is_trading_day("2026-05-25"))
        self.assertFalse(is_trading_day("2026-05-24"))

    def test_generate_date_range(self) -> None:
        days = generate_date_range("2026-05-22", "2026-05-25", trading_days_only=True)
        self.assertEqual(days, ["2026-05-22", "2026-05-25"])

    def test_latest_n_trading_days(self) -> None:
        days = latest_n_trading_days(3, end_date="2026-05-25")
        self.assertEqual(len(days), 3)


class TestDataValidator(unittest.TestCase):
    """Test data validator."""

    def test_validate_price_dataframe(self) -> None:
        df = pd.DataFrame(
            {
                "date": ["2026-05-20"],
                "code": ["000001"],
                "open": [10.0],
                "high": [11.0],
                "low": [9.8],
                "close": [10.5],
                "volume": [1000],
                "amount": [10000],
                "turnover": [1.2],
            }
        )
        report = DataValidator.validate_price_dataframe(df)
        self.assertTrue(report["is_valid"])


if __name__ == "__main__":
    unittest.main()
