"""Daily data update pipeline for week-2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.data_ingestion.data_fetcher import DataFetcher
from src.data_ingestion.fetch_index import IndexFetcher
from src.data_ingestion.fetch_prices import StockPriceFetcher
from src.data_ingestion.fetch_stock_basic import StockBasicFetcher
from src.database.db_manager import DatabaseManager
from src.factors.factor_calculator import FactorCalculator
from src.universe.ai_chain_pool import init_ai_chain_pool
from src.utils.date_utils import latest_n_trading_days
from src.utils.logger import setup_logger


def run_update(days: int = 90) -> None:
    """Run full daily update process.

    Steps:
    1. update stock_basic
    2. initialize/update watchlist seed
    3. update watchlist prices
    4. update major index prices
    5. compute factors and write
    6. write update log json
    """
    settings = load_app_settings()
    logger = setup_logger("update_data", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    fetcher = DataFetcher(log_level=settings.log_level)

    dates = latest_n_trading_days(days)
    start_date, end_date = dates[0], dates[-1]

    logger.info("Update started range=%s~%s", start_date, end_date)

    basic_rows = 0
    seed_rows = 0
    price_rows = 0
    index_rows = 0
    factor_rows = 0
    failed_stock_codes: list[str] = []
    failed_indexes: list[str] = []

    try:
        basic_fetcher = StockBasicFetcher(db, fetcher)
        basic_rows = basic_fetcher.update_to_db(incremental=True)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Step1 stock_basic failed: %s", exc)

    try:
        seed_rows = init_ai_chain_pool(db)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Step2 init watchlist failed: %s", exc)

    watchlist = db.fetch_all("SELECT code, name FROM watchlist WHERE pool_status IN ('核心池','观察池','事件池','波段池')")
    try:
        price_fetcher = StockPriceFetcher(db, fetcher)
        price_rows, failed_stock_codes = price_fetcher.fetch_batch(
            [(r["code"], r["name"]) for r in watchlist], start_date, end_date
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Step3 stock prices failed: %s", exc)

    try:
        index_fetcher = IndexFetcher(db, fetcher)
        index_rows, failed_indexes = index_fetcher.fetch_and_update(start_date, end_date)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Step4 index prices failed: %s", exc)

    try:
        factor_calculator = FactorCalculator(db)
        factor_rows = factor_calculator.run_incremental(start_date, end_date, codes=[r["code"] for r in watchlist])
    except Exception as exc:  # noqa: BLE001
        logger.exception("Step5 factor calc failed: %s", exc)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "range": {"start_date": start_date, "end_date": end_date},
        "stock_basic_rows": basic_rows,
        "watchlist_seed_rows": seed_rows,
        "price_rows": price_rows,
        "index_rows": index_rows,
        "factor_rows": factor_rows,
        "failed_stock_codes": failed_stock_codes,
        "failed_indexes": failed_indexes,
    }
    out = PROJECT_ROOT / "logs" / f"update_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Update finished summary=%s", summary)


if __name__ == "__main__":
    run_update()
