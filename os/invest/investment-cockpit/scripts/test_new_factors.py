"""Quick validation for new factor modules and scoring integration."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.factors.factor_calculator import FactorCalculator
from src.factors.fundamental_factors import calculate_fundamental_score
from src.factors.industry_factors import calculate_industry_score
from src.factors.news_factors import calculate_news_score


def _in_range(v: float) -> bool:
    return 0.0 <= float(v) <= 100.0


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)

    watchlist = db.fetch_all("SELECT code FROM watchlist ORDER BY code LIMIT 3")
    if not watchlist:
        print("No watchlist data.")
        return

    latest = db.fetch_one("SELECT MAX(date) AS d FROM stock_daily_bar")
    date = str((latest or {}).get("d") or "")
    if not date:
        print("No stock_daily_bar data.")
        return

    print(f"Test date: {date}")
    print("\n=== Single Factor Tests ===")
    for item in watchlist:
        code = str(item["code"])
        news = calculate_news_score(code, date, db)
        fund = calculate_fundamental_score(code, db)
        ind = calculate_industry_score(code, date, db)
        print(f"{code}: news={news:.2f}, fundamental={fund:.2f}, industry={ind:.2f}")
        assert _in_range(news), f"news out of range: {code}"
        assert _in_range(fund), f"fund out of range: {code}"
        assert _in_range(ind), f"industry out of range: {code}"

    print("\n=== Calculator Integration Test ===")
    codes = [str(r["code"]) for r in watchlist]
    calc = FactorCalculator(db)
    out = calc.calculate(date, date, codes)
    if out.empty:
        print("No factor rows generated for test date.")
        return

    cols = ["trend_score", "momentum_score", "volume_score", "fundamental_score", "sentiment_score", "industry_score", "final_score"]
    print(out[["date", "code", *cols]].to_string(index=False))

    for c in cols:
        assert out[c].dropna().between(0, 100).all(), f"{c} has out-of-range values"

    # Compare against old baseline (roughly 50-55 defaults)
    baseline = pd.Series(51.67, index=out.index)
    diff = (out["final_score"] - baseline).abs().mean()
    print(f"\nMean abs diff vs old baseline(51.67): {diff:.2f}")
    print("PASS")


if __name__ == "__main__":
    main()
