"""Unified factor calculator and persistence."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.database.db_manager import DatabaseManager
from src.factors.fundamental_factors import calculate_fundamental_score
from src.factors.industry_factors import calculate_industry_score
from src.factors.momentum_factors import add_momentum_factors
from src.factors.news_factors import calculate_news_score
from src.optimization.parameter_manager import ParameterSet
from src.factors.trend_factors import add_trend_factors
from src.factors.volume_factors import add_volume_factors


class FactorCalculator:
    """Compute and write factor scores for watchlist stocks."""

    def __init__(self, db: DatabaseManager, params: ParameterSet | None = None) -> None:
        self.db = db
        self.params = params

    def load_price_data(self, start_date: str, end_date: str, codes: Iterable[str] | None = None) -> pd.DataFrame:
        """Load source price data for factor computation."""
        if codes:
            code_list = list(codes)
            placeholders = ",".join(["?"] * len(code_list))
            sql = (
                f"SELECT date, code, close, amount, volume, turnover FROM stock_daily_bar "
                f"WHERE date BETWEEN ? AND ? AND code IN ({placeholders}) ORDER BY code, date"
            )
            rows = self.db.fetch_all(sql, [start_date, end_date, *code_list])
        else:
            sql = (
                "SELECT date, code, close, amount, volume, turnover FROM stock_daily_bar "
                "WHERE date BETWEEN ? AND ? ORDER BY code, date"
            )
            rows = self.db.fetch_all(sql, [start_date, end_date])
        return pd.DataFrame(rows)

    def calculate(self, start_date: str, end_date: str, codes: Iterable[str] | None = None) -> pd.DataFrame:
        """Batch calculate all factors."""
        df = self.load_price_data(start_date, end_date, codes)
        if df.empty:
            return df

        trend_params = self.params.trend_params if self.params else None
        momentum_params = self.params.momentum_params if self.params else None
        volume_params = self.params.volume_params if self.params else None

        df = add_trend_factors(df, trend_params)
        df = add_momentum_factors(df, momentum_params)
        df = add_volume_factors(df, volume_params)

        # Row-wise factors requiring cross-table lookups.
        df["sentiment_score"] = df.apply(
            lambda r: calculate_news_score(str(r["code"]), str(r["date"]), self.db), axis=1
        )
        fundamental_cache = {
            code: calculate_fundamental_score(str(code), self.db)
            for code in df["code"].astype(str).drop_duplicates().tolist()
        }
        df["fundamental_score"] = df["code"].astype(str).map(fundamental_cache)
        df["industry_score"] = df.apply(
            lambda r: calculate_industry_score(str(r["code"]), str(r["date"]), self.db), axis=1
        )

        df["final_score"] = df[
            ["trend_score", "momentum_score", "volume_score", "fundamental_score", "sentiment_score", "industry_score"]
        ].mean(axis=1)

        cols = [
            "date",
            "code",
            "trend_score",
            "momentum_score",
            "volume_score",
            "fundamental_score",
            "sentiment_score",
            "industry_score",
            "final_score",
        ]
        return df[cols]

    def write_factor_scores(self, factors: pd.DataFrame) -> int:
        """Write factors into factor_scores table via upsert."""
        if factors.empty:
            return 0
        for row in factors.to_dict("records"):
            self.db.upsert(
                "factor_scores",
                {
                    "date": row["date"],
                    "code": row["code"],
                    "trend_score": float(row["trend_score"]) if pd.notna(row["trend_score"]) else None,
                    "momentum_score": float(row["momentum_score"]) if pd.notna(row["momentum_score"]) else None,
                    # Reuse reversal_score column as industry score (schema-compatible).
                    "reversal_score": float(row["industry_score"]) if pd.notna(row["industry_score"]) else None,
                    "volume_score": float(row["volume_score"]) if pd.notna(row["volume_score"]) else None,
                    "fundamental_score": float(row["fundamental_score"]) if pd.notna(row["fundamental_score"]) else None,
                    "sentiment_score": float(row["sentiment_score"]) if pd.notna(row["sentiment_score"]) else None,
                    "final_score": float(row["final_score"]) if pd.notna(row["final_score"]) else None,
                },
                conflict_columns=["date", "code"],
            )
        return len(factors)

    def run_incremental(self, start_date: str, end_date: str, codes: Iterable[str] | None = None) -> int:
        """Calculate and persist factor scores incrementally for date range."""
        factors = self.calculate(start_date, end_date, codes)
        return self.write_factor_scores(factors)
