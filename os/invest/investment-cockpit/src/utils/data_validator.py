"""Data quality checks and validation reports."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd


class DataValidator:
    """Validate stock and factor data quality."""

    @staticmethod
    def validate_price_dataframe(df: pd.DataFrame) -> Dict[str, object]:
        """Validate historical price dataframe.

        Returns a report dict with ``is_valid`` and issue lists.
        """
        issues: List[str] = []
        required_cols = ["date", "code", "open", "high", "low", "close", "volume", "amount"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            issues.append(f"missing_columns:{','.join(missing)}")

        if df.empty:
            issues.append("empty_dataframe")

        numeric_cols = [c for c in ["open", "high", "low", "close", "volume", "amount", "turnover"] if c in df.columns]
        for col in numeric_cols:
            if (df[col] < 0).any():
                issues.append(f"negative_value:{col}")

        if {"high", "low"}.issubset(df.columns):
            if (df["high"] < df["low"]).any():
                issues.append("high_lower_than_low")

        if {"open", "close", "high", "low"}.issubset(df.columns):
            if ((df["open"] > df["high"]) | (df["open"] < df["low"]) | (df["close"] > df["high"]) | (df["close"] < df["low"])).any():
                issues.append("price_outside_range")

        return {"is_valid": len(issues) == 0, "issues": issues, "rows": len(df)}

    @staticmethod
    def detect_outliers(df: pd.DataFrame, col: str, z_threshold: float = 4.0) -> pd.DataFrame:
        """Detect outliers via z-score on a column."""
        if col not in df.columns or df.empty:
            return df.iloc[0:0]
        s = df[col].astype(float)
        std = s.std(ddof=0)
        if std == 0 or pd.isna(std):
            return df.iloc[0:0]
        z = (s - s.mean()) / std
        return df[z.abs() >= z_threshold]

    @staticmethod
    def build_quality_report(df: pd.DataFrame, code: str = "") -> Dict[str, object]:
        """Build data quality report for one dataset."""
        base = DataValidator.validate_price_dataframe(df)
        outlier_count = len(DataValidator.detect_outliers(df, "pct_chg")) if "pct_chg" in df.columns else 0
        report: Dict[str, object] = {
            "code": code,
            "rows": base["rows"],
            "is_valid": base["is_valid"],
            "issues": base["issues"],
            "pct_chg_outliers": outlier_count,
        }
        return report
