"""Synthetic test fixtures only; no real accounts, quotes or trades."""
import copy
import importlib.util
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "skills"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


holdings = module("holdings", ROOT / "nia-wealth-holdings/scripts/validate_snapshot.py")
goals = module("goals", ROOT / "nia-wealth-goals/scripts/goal_math.py")


class SnapshotGate(unittest.TestCase):
    def setUp(self):
        self.data = {
            "schema_version": "wealth.snapshot.v1", "snapshot_id": "synthetic-test-only",
            "as_of": "2026-10-23T15:10:00+08:00", "source_ref": "synthetic-fixture",
            "confirmed_by_user": True, "accounts_complete": True, "pending_activity": False,
            "base_currency": "CNY", "cash_cny": 1000, "reported_investable_assets_cny": 2000,
            "positions": [{"account_alias": "TEST", "symbol": "TEST_ONLY", "venue": "TEST",
                           "share_class": "", "asset_type": "stock", "currency": "CNY",
                           "quantity": 100, "available_quantity": 100, "unit_price": 10,
                           "price_as_of": "2026-10-23T15:00:00+08:00", "source_ref": "synthetic-fixture",
                           "quality": "verified", "cost_total_cny": None}]}

    def check(self, data=None):
        return holdings.validate(self.data if data is None else data, "2026-10-23T16:00:00+08:00", 2)

    def test_reconciled_snapshot_is_not_trade_permission(self):
        original = copy.deepcopy(self.data)
        result = self.check()
        self.assertTrue(result["ok"])
        self.assertFalse(result["executable"])
        self.assertEqual(result["investable_assets_cny"], 2000)
        self.assertEqual(original, self.data)

    def test_unknown_is_not_zero_or_empty(self):
        self.data["positions"] = []
        self.data["reported_investable_assets_cny"] = 1000
        self.assertFalse(self.check()["ok"])
        self.data["empty_positions_confirmed"] = True
        self.assertTrue(self.check()["ok"])
        self.data["cash_cny"] = None
        self.assertFalse(self.check()["ok"])

    def test_explicit_confirmation_and_complete_accounts(self):
        for key in ("confirmed_by_user", "accounts_complete"):
            with self.subTest(key=key):
                value = copy.deepcopy(self.data)
                value[key] = 1
                self.assertFalse(self.check(value)["ok"])
        self.data["pending_activity"] = None
        self.assertFalse(self.check()["ok"])

    def test_duplicate_same_account_but_distinct_accounts_allowed(self):
        self.data["positions"].append(copy.deepcopy(self.data["positions"][0]))
        self.data["reported_investable_assets_cny"] = 3000
        self.assertFalse(self.check()["ok"])
        self.data["positions"][1]["account_alias"] = "OTHER_TEST"
        self.assertTrue(self.check()["ok"])

    def test_price_quality_and_time(self):
        for update in ({"quality": "estimate"}, {"price_as_of": "2026-10-20T15:00:00+08:00"},
                       {"price_as_of": "2026-10-24T15:00:00+08:00"},
                       {"price_as_of": "2026-10-23T15:00:00"},
                       {"price_as_of": "2026-10-23T15:30:00+08:00"}):
            with self.subTest(update=update):
                data = copy.deepcopy(self.data)
                data["positions"][0].update(update)
                self.assertFalse(self.check(data)["ok"])

    def test_stale_snapshot_even_with_fresh_price(self):
        self.data["as_of"] = "2026-10-20T15:00:00+08:00"
        self.assertFalse(self.check()["ok"])

    def test_numeric_integrity_and_availability(self):
        for update in ({"quantity": True}, {"quantity": -1}, {"unit_price": math.nan},
                       {"unit_price": 0}, {"available_quantity": 101},
                       {"available_quantity": None}, {"currency": "USD"}, {"symbol": 1}):
            with self.subTest(update=update):
                data = copy.deepcopy(self.data)
                data["positions"][0].update(update)
                self.assertFalse(self.check(data)["ok"])

    def test_mismatch_and_malformed_input(self):
        self.data["reported_investable_assets_cny"] = 9999
        self.assertFalse(self.check()["ok"])
        for data in ([], None, {"positions": [None]}):
            self.assertFalse(holdings.validate(data, "2026-10-23T16:00:00+08:00", 2)["ok"])
        self.assertFalse(holdings.validate({}, "invalid", 2)["ok"])
        self.assertFalse(holdings.validate({}, "2026-10-23T16:00:00+08:00", math.inf)["ok"])


class GoalMath(unittest.TestCase):
    def test_zero_return_monthly_savings(self):
        result = goals.calculate(1200, 2400, 12, 0, 100)
        self.assertEqual(result["projected_value_cny"], 2400)
        self.assertEqual(result["required_monthly_contribution_cny"], 100)

    def test_effective_annual_return(self):
        result = goals.calculate(1000, 1100, 12, .1, 0)
        self.assertAlmostEqual(result["projected_value_cny"], 1100)
        self.assertEqual(result["required_monthly_contribution_cny"], 0)

    def test_month_end_contribution_timing(self):
        annual = 1.01 ** 12 - 1
        result = goals.calculate(1000, 2000, 1, annual, 100)
        self.assertEqual(result["projected_value_cny"], 1110)

    def test_negative_and_near_zero_return(self):
        self.assertEqual(goals.calculate(1000, 1000, 12, -.1, 0)["projected_value_cny"], 900)
        self.assertAlmostEqual(goals.calculate(1200, 2400, 12, 1e-15, 100)["projected_value_cny"], 2400)

    def test_invalid_inputs_never_produce_forecast(self):
        for args in ((None, 1000, 12, 0, 0), (1000, 2000, 0, 0, 0),
                     (1000, 2000, 12, -1, 0), (1000, 2000, 12, math.nan, 0),
                     (True, 2000, 12, 0, 0), (1000, 2000, 12, 0, -1),
                     (1000, 2000, 100000, 1e308, 0)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    goals.calculate(*args)


if __name__ == "__main__":
    unittest.main()
