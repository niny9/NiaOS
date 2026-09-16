"""Weekly review analyzer for recommendation effectiveness."""

from __future__ import annotations

from typing import Any, Dict, List

from src.database.db_manager import DatabaseManager


class ReviewAnalyzer:
    """Analyze signal performance, execution deviation and attribution."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def analyze_recommendation_returns(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Compute 1d/5d/20d returns for recommendations in date range."""
        signals = self.db.fetch_all(
            "SELECT id, date, code, reason, signal FROM daily_signals WHERE date BETWEEN ? AND ?",
            (start_date, end_date),
        )
        rows: List[Dict[str, Any]] = []
        for s in signals:
            returns = self._future_returns(s["code"], s["date"])
            rows.append({
                "signal_id": s["id"],
                "signal_date": s["date"],
                "code": s["code"],
                "strategy_type": s["signal"],
                "signal_reason": s.get("reason") or "",
                **returns,
            })
        return rows

    def analyze_execution_deviation(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Analyze executed vs non-executed recommendations and manual buys."""
        rec = self.db.fetch_all("SELECT id, date, code, signal FROM daily_signals WHERE date BETWEEN ? AND ?", (start_date, end_date))
        trades = self.db.fetch_all(
            "SELECT trade_date, code, side, executed_by_model, deviation_reason FROM real_trades WHERE trade_date BETWEEN ? AND ? AND status='active'",
            (start_date, end_date),
        )
        trade_codes = {t["code"] for t in trades if t["side"] == "buy"}
        rec_codes = {r["code"] for r in rec}
        executed = sum(1 for r in rec if r["code"] in trade_codes)
        unexecuted = [r for r in rec if r["code"] not in trade_codes]
        manual = [t for t in trades if t["code"] not in rec_codes and t["side"] == "buy"]
        return {
            "recommended": len(rec),
            "executed": executed,
            "execution_rate": (executed / len(rec)) if rec else 0.0,
            "unexecuted": unexecuted,
            "manual_buys": manual,
        }

    def attribution_analysis(self, rows: List[Dict[str, Any]]) -> Dict[str, int]:
        """Build attribution buckets from realized 5d return and execution status."""
        bucket = {"模型对": 0, "模型错": 0, "人对": 0, "人错": 0, "市场变了": 0}
        for r in rows:
            ret5 = float(r.get("actual_return_5d") or 0)
            executed = bool(r.get("executed"))
            if executed and ret5 > 0:
                bucket["模型对"] += 1
            elif executed and ret5 <= 0:
                bucket["模型错"] += 1
            elif (not executed) and ret5 > 0:
                bucket["人错"] += 1
            elif (not executed) and ret5 <= 0:
                bucket["人对"] += 1
            if abs(ret5) > 0.12:
                bucket["市场变了"] += 1
        return bucket

    def improvement_suggestions(self, attribution: Dict[str, int]) -> List[str]:
        """Generate actionable suggestions from attribution stats."""
        suggestions: List[str] = []
        if attribution["人错"] > attribution["人对"]:
            suggestions.append("减少主观跳过模型信号，优先执行高分信号")
        if attribution["模型错"] > attribution["模型对"]:
            suggestions.append("下调失效因子权重，增加行业景气度过滤")
        if attribution["市场变了"] >= 2:
            suggestions.append("提高波动期风控阈值，降低单票仓位上限")
        if not suggestions:
            suggestions.append("当前策略与执行偏差可控，维持并持续跟踪")
        return suggestions

    def persist_review_log(self, review_date: str, rows: List[Dict[str, Any]], deviation_map: Dict[str, str]) -> int:
        """Persist per-signal weekly review rows into review_log table."""
        count = 0
        for row in rows:
            conclusion = "成功" if float(row.get("actual_return_5d") or 0) > 0 else "失败"
            lesson = "保持" if conclusion == "成功" else "复盘失败因子"
            self.db.execute(
                """
                INSERT INTO review_log (
                    signal_date, review_date, code, strategy_type, signal_reason,
                    actual_return_1d, actual_return_5d, actual_return_20d, max_drawdown,
                    executed, deviation_reason, conclusion, lesson
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["signal_date"],
                    review_date,
                    row["code"],
                    row["strategy_type"],
                    row["signal_reason"],
                    row.get("actual_return_1d"),
                    row.get("actual_return_5d"),
                    row.get("actual_return_20d"),
                    row.get("max_drawdown"),
                    1 if row.get("executed") else 0,
                    deviation_map.get(row["code"]),
                    conclusion,
                    lesson,
                ),
            )
            count += 1
        return count

    def _future_returns(self, code: str, signal_date: str) -> Dict[str, float]:
        bars = self.db.fetch_all(
            "SELECT date, close FROM stock_daily_bar WHERE code=? AND date>=? ORDER BY date LIMIT 25",
            (code, signal_date),
        )
        if len(bars) < 2 or bars[0].get("close") is None:
            return {"actual_return_1d": 0.0, "actual_return_5d": 0.0, "actual_return_20d": 0.0, "max_drawdown": 0.0}
        c0 = float(bars[0]["close"])

        def ret_at(i: int) -> float:
            if len(bars) <= i or bars[i].get("close") is None:
                return 0.0
            return float(bars[i]["close"]) / c0 - 1.0

        closes = [float(b["close"]) for b in bars if b.get("close") is not None]
        peak = closes[0]
        max_dd = 0.0
        for c in closes:
            peak = max(peak, c)
            dd = (peak - c) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        return {
            "actual_return_1d": ret_at(1),
            "actual_return_5d": ret_at(5),
            "actual_return_20d": ret_at(20),
            "max_drawdown": max_dd,
        }
