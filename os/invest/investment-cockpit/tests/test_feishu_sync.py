"""Unit tests for Feishu sync integration utilities."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.config.settings import AppSettings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService
from src.scoring.strategy_scorer import _map_signal_row


class FeishuSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        self.db = DatabaseManager(db_path)
        self.settings = AppSettings(env="test", db_path=db_path, log_level="INFO")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_sync_state_table_created(self) -> None:
        FeishuSyncService(self.db, self.settings)
        self.assertTrue(self.db.table_exists("feishu_sync_state"))

    def test_hash_row_stable(self) -> None:
        row = {"a": 1, "b": "x"}
        h1 = FeishuSyncService._hash_row(row)
        h2 = FeishuSyncService._hash_row({"b": "x", "a": 1})
        self.assertEqual(h1, h2)

    def test_signal_map(self) -> None:
        out = _map_signal_row({
            "date": "2026-05-25",
            "code": "600000",
            "name": "测试",
            "signal": "short_term",
            "score": 88.5,
            "reason": "趋势向上",
            "action_plan": "分批买入",
        })
        self.assertEqual(out["策略类型"], "短线")
        self.assertEqual(out["股票代码"], "600000")
        self.assertEqual(out["综合得分"], 88.5)


if __name__ == "__main__":
    unittest.main()
