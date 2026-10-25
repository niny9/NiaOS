#!/usr/bin/env python3
"""Read-only structural/freshness gate for simple CNY investment snapshots."""
import argparse
import json
import math
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return Decimal(str(value))


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return result


def validate(data, now, max_age_hours):
    errors = []
    result = {"schema_version": "wealth.validation.v1", "ok": False,
              "executable": False, "scope": "simple_cny_snapshot_only", "errors": errors}
    age_limit = number(max_age_hours)
    if age_limit is None or age_limit <= 0:
        errors.append("max_age_hours must be finite and positive")
        return result
    try:
        checked_at = timestamp(now)
    except (ValueError, TypeError) as exc:
        errors.append(f"now: {exc}")
        return result
    result.update(checked_at=now, max_age_hours=max_age_hours)
    if not isinstance(data, dict):
        errors.append("snapshot must be an object")
        return result

    def required_text(obj, field, prefix):
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}{field}: missing nonempty string")

    def age(value, label):
        try:
            dt = timestamp(value)
            hours = (checked_at - dt).total_seconds() / 3600
            if hours < 0:
                errors.append(f"{label}: future timestamp")
            elif hours > float(age_limit):
                errors.append(f"{label}: stale")
            return dt
        except (ValueError, TypeError):
            errors.append(f"{label}: invalid/missing timezone-aware timestamp")
            return None

    if data.get("schema_version") != "wealth.snapshot.v1":
        errors.append("unsupported schema_version")
    for key in ("snapshot_id", "source_ref"):
        required_text(data, key, "")
    for key in ("confirmed_by_user", "accounts_complete"):
        if data.get(key) is not True:
            errors.append(f"{key}: must be explicitly true")
    if data.get("pending_activity") is not False:
        errors.append("pending_activity: must be explicitly false; otherwise reconcile separately")
    if data.get("base_currency") != "CNY":
        errors.append("base_currency: only CNY is supported")
    snapshot_at = age(data.get("as_of"), "as_of")
    positions = data.get("positions")
    if not isinstance(positions, list):
        errors.append("positions must be an array")
        return result
    if not positions and data.get("empty_positions_confirmed") is not True:
        errors.append("empty positions are not confirmed empty holdings")
    total = Decimal("0")
    seen = set()
    all_values_known = True
    for index, row in enumerate(positions):
        prefix = f"positions[{index}]."
        if not isinstance(row, dict):
            errors.append(prefix + "must be an object")
            all_values_known = False
            continue
        for field in ("account_alias", "symbol", "venue", "source_ref"):
            required_text(row, field, prefix)
        if not isinstance(row.get("share_class"), str):
            errors.append(prefix + "share_class must be a string (empty for stocks)")
        key = tuple(row.get(field) for field in ("account_alias", "symbol", "venue", "share_class"))
        if all(isinstance(x, str) for x in key):
            if key in seen:
                errors.append(prefix + "duplicate account/security/share-class key")
            seen.add(key)
        if row.get("asset_type") not in ("stock", "etf", "fund"):
            errors.append(prefix + "unsupported asset_type")
        if row.get("currency") != "CNY":
            errors.append(prefix + "non-CNY or unknown currency")
        if row.get("quality") != "verified":
            errors.append(prefix + "quality is not verified")
        price_at = age(row.get("price_as_of"), prefix + "price_as_of")
        if price_at and snapshot_at and price_at > snapshot_at:
            errors.append(prefix + "price is later than snapshot as_of")
        qty = number(row.get("quantity"))
        available = number(row.get("available_quantity"))
        price = number(row.get("unit_price"))
        if qty is None or qty < 0:
            errors.append(prefix + "quantity must be finite and nonnegative")
        if available is None or available < 0 or (qty is not None and available > qty):
            errors.append(prefix + "available_quantity must be between zero and quantity")
        if price is None or price <= 0:
            errors.append(prefix + "unit_price must be finite and positive")
        cost = row.get("cost_total_cny")
        if cost is not None and (number(cost) is None or number(cost) < 0):
            errors.append(prefix + "cost_total_cny must be null or nonnegative")
        if qty is not None and qty >= 0 and price is not None and price > 0:
            total += qty * price
        else:
            all_values_known = False
    cash = number(data.get("cash_cny"))
    reported = number(data.get("reported_investable_assets_cny"))
    if cash is None or cash < 0:
        errors.append("cash_cny must be finite and nonnegative")
    if reported is None or reported < 0:
        errors.append("reported_investable_assets_cny must be finite and nonnegative")
    if all_values_known and cash is not None and cash >= 0 and reported is not None and reported >= 0:
        difference = total + cash - reported
        result["reconciliation_difference_cny"] = float(difference)
        if abs(difference) > Decimal("1"):
            errors.append("valuation plus cash does not reconcile within CNY 1")
    result["ok"] = not errors
    if result["ok"]:
        result["investable_assets_cny"] = float(total + cash)
    result["limitations"] = ["Source authenticity and market/product rules require separate verification.",
                             "Passing does not authorize or execute trades."]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--now", required=True, help="ISO timestamp including timezone")
    parser.add_argument("--max-age-hours", type=float, required=True)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        report = validate(data, args.now, args.max_age_hours)
    except (OSError, ValueError) as exc:
        report = {"ok": False, "executable": False, "errors": [str(exc)]}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
