#!/usr/bin/env python3
"""Single-pool hypothetical planning, not household forecasts or investment advice."""
import argparse
import json
import math


def calculate(principal, target, months, annual_return, monthly_contribution):
    for label, value in (("principal", principal), ("target", target),
                         ("annual_return", annual_return), ("monthly_contribution", monthly_contribution)):
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError(f"{label} must be a finite number")
    if isinstance(months, bool) or not isinstance(months, int) or months <= 0:
        raise ValueError("months must be a positive integer")
    if principal < 0 or target <= 0 or monthly_contribution < 0:
        raise ValueError("principal/contribution must be nonnegative and target positive")
    if annual_return <= -1:
        raise ValueError("annual_return must be greater than -1")
    log_month = math.log1p(annual_return) / 12
    monthly_return = math.expm1(log_month)
    try:
        growth = math.exp(log_month * months)
        annuity = months if annual_return == 0 else math.expm1(log_month * months) / monthly_return
        projected = principal * growth + monthly_contribution * annuity
        required = max(0.0, (target - principal * growth) / annuity)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("scenario outside supported numerical range") from exc
    if not all(math.isfinite(x) for x in (growth, annuity, projected, required)):
        raise ValueError("scenario outside supported numerical range")
    return {
        "schema_version": "wealth.goal-scenario.v1", "scenario_only": True,
        "principal_cny": principal, "target_cny": target, "months": months,
        "annual_effective_return_assumption": annual_return,
        "monthly_net_contribution_cny": monthly_contribution,
        "projected_value_cny": round(projected, 2),
        "gap_at_horizon_cny": round(target - projected, 2),
        "required_monthly_contribution_cny": round(required, 2),
        "assumptions": ["One asset pool only", "End-of-month equal contributions",
                        "Fixed nominal effective annual return; not guaranteed",
                        "Fees/taxes must be reflected in the supplied net return",
                        "Property and liabilities must be modeled separately"]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--principal", type=float, required=True)
    parser.add_argument("--target", type=float, required=True)
    parser.add_argument("--months", type=int, required=True)
    parser.add_argument("--annual-return", type=float, required=True, help="Effective annual return as decimal")
    parser.add_argument("--monthly-contribution", type=float, required=True)
    args = parser.parse_args()
    try:
        report = calculate(args.principal, args.target, args.months, args.annual_return, args.monthly_contribution)
    except ValueError as exc:
        print(json.dumps({"error": str(exc), "scenario_only": True}, ensure_ascii=False))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
