"""Smoke test for multi-source fetcher."""

from __future__ import annotations

import argparse

from src.data_ingestion.multi_source_fetcher import MultiSourceFetcher


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", default="600000,000001", help="Comma-separated stock codes")
    parser.add_argument("--start", default="20260101", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="20260527", help="End date YYYYMMDD")
    args = parser.parse_args()

    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    fetcher = MultiSourceFetcher(log_level="INFO")

    print("== Test spot sources ==")
    for source_name, fn in fetcher.spot_sources:
        try:
            df = fn(codes)
            print(f"[spot] {source_name}: rows={len(df)} cols={list(df.columns)[:8]}")
        except Exception as exc:  # noqa: BLE001
            print(f"[spot] {source_name}: FAILED {exc}")

    print("\n== Test hist fallback ==")
    try:
        result = fetcher.get_stock_prices(codes, args.start, args.end)
        print(f"[hist] chosen={result.source} rows={len(result.data)} cols={list(result.data.columns)}")
    except Exception as exc:  # noqa: BLE001
        print(f"[hist] fallback FAILED {exc}")

    print("\n== Test source switch (force akshare->fallback) ==")
    original_sources = fetcher.sources
    fetcher.sources = [("broken", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("forced failure")))] + original_sources
    try:
        result = fetcher.get_stock_prices(codes, args.start, args.end)
        print(f"[switch] chosen={result.source} rows={len(result.data)}")
    except Exception as exc:  # noqa: BLE001
        print(f"[switch] FAILED {exc}")


if __name__ == "__main__":
    main()
