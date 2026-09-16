"""Unified strategy scoring manager."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult
from src.optimization.parameter_manager import ParameterSet
from src.scoring.score_short_term import ShortTermScorer
from src.scoring.score_stable import StableScorer
from src.scoring.score_swing import SwingScorer


@dataclass
class StrategyScores:
    """Container for all strategy outputs."""

    short_term: pd.DataFrame
    swing: pd.DataFrame
    stable: pd.DataFrame


class StrategyScorer:
    """Coordinate three strategy scorers and persist daily signals."""

    def __init__(self, db: DatabaseManager, params: ParameterSet | None = None) -> None:
        self.db = db
        self.params = params
        self.short_term_scorer = ShortTermScorer(weights=(params.short_term_weights if params else None))
        self.swing_scorer = SwingScorer(weights=(params.swing_weights if params else None))
        self.stable_scorer = StableScorer(weights=(params.stable_weights if params else None))
        self._cache: Dict[str, StrategyScores] = {}

    def _load_latest_factor_snapshot(self, trade_date: str | None = None) -> pd.DataFrame:
        base_sql = """
        SELECT f.date, f.code, w.name, w.industry_chain_l1, w.industry_chain_l2,
               f.trend_score, f.momentum_score, f.reversal_score, f.volume_score,
               f.fundamental_score, f.sentiment_score, f.risk_score,
               b.close, b.amount, b.turnover
        FROM factor_scores f
        JOIN watchlist w ON w.code = f.code
        LEFT JOIN stock_daily_bar b ON b.date = f.date AND b.code = f.code
        WHERE f.date = COALESCE(?, (SELECT MAX(date) FROM factor_scores))
        """
        rows = self.db.fetch_all(base_sql, [trade_date])
        df = pd.DataFrame(rows)
        if df.empty:
            return df

        ma_rows = self.db.fetch_all(
            """
            WITH latest AS (
                SELECT code, date, close,
                       ROW_NUMBER() OVER(PARTITION BY code ORDER BY date DESC) AS rn
                FROM stock_daily_bar WHERE code IN (SELECT code FROM watchlist)
            )
            SELECT code,
                   AVG(CASE WHEN rn <= 5 THEN close END) AS ma5,
                   AVG(CASE WHEN rn <= 20 THEN close END) AS ma20
            FROM latest
            GROUP BY code
            """
        )
        ma_df = pd.DataFrame(ma_rows)
        if not ma_df.empty:
            df = df.merge(ma_df, on="code", how="left")
        return df

    def score_all(self, trade_date: str | None = None, top_n: int = 5) -> StrategyScores:
        """Score short/swing/stable strategies using latest snapshot."""
        cache_key = trade_date or "latest"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = self._load_latest_factor_snapshot(trade_date)
        if data.empty:
            empty = pd.DataFrame()
            result = StrategyScores(short_term=empty, swing=empty, stable=empty)
            self._cache[cache_key] = result
            return result

        short_df = self.short_term_scorer.score(
            data,
            top_n=top_n,
            thresholds=(self.params.filter_thresholds if self.params else None),
        )
        swing_df = self.swing_scorer.score(data, top_n=top_n)
        stable_df = self.stable_scorer.score(data, top_n=top_n)

        result = StrategyScores(short_term=short_df, swing=swing_df, stable=stable_df)
        self._cache[cache_key] = result
        return result

    def _calculate_trade_points(
        self, code: str, strategy_type: str, score: float, current_price: float
    ) -> Dict[str, float]:
        """Calculate entry, target, stop loss prices and position sizing.

        Args:
            code: Stock code
            strategy_type: 'short_term', 'swing', or 'stable'
            score: Strategy score (0-100)
            current_price: Current market price

        Returns:
            Dict with entry_price, target_price, stop_loss_price, position_size,
            expected_return, risk_reward_ratio
        """
        # Entry price: use current price as reference
        entry_price = current_price

        # Target price based on strategy type and score
        # Higher score = higher target return
        if strategy_type == "short_term":
            # Short-term: 5-15% target based on score
            target_return = 0.05 + (score / 100) * 0.10
            stop_loss_pct = 0.05  # 5% stop loss
        elif strategy_type == "swing":
            # Swing: 10-25% target based on score
            target_return = 0.10 + (score / 100) * 0.15
            stop_loss_pct = 0.08  # 8% stop loss
        else:  # stable
            # Stable: 15-40% target based on score
            target_return = 0.15 + (score / 100) * 0.25
            stop_loss_pct = 0.10  # 10% stop loss

        target_price = entry_price * (1 + target_return)
        stop_loss_price = entry_price * (1 - stop_loss_pct)

        # Position size based on score (higher score = larger position)
        # Range: 5% to 20% of portfolio
        position_size = 0.05 + (score / 100) * 0.15

        # Expected return and risk/reward ratio
        expected_return = target_return
        risk_reward_ratio = target_return / stop_loss_pct

        return {
            "entry_price": round(entry_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss_price": round(stop_loss_price, 2),
            "position_size": round(position_size, 4),
            "expected_return": round(expected_return, 4),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
        }

    def write_daily_signals(self, scores: StrategyScores, trade_date: str | None = None) -> int:
        """Write merged strategy top picks into daily_signals table."""
        date_value = trade_date or datetime.now().strftime("%Y-%m-%d")
        frames = []
        for signal, frame, score_col in [
            ("short_term", scores.short_term, "short_term_score"),
            ("swing", scores.swing, "swing_score"),
            ("stable", scores.stable, "stable_score"),
        ]:
            if frame.empty:
                continue
            tmp = frame[["code", "name", "rank", "reason", score_col]].copy()
            # Add close price if available
            if "close" in frame.columns:
                tmp["close"] = frame["close"]
            tmp["signal"] = signal
            tmp = tmp.rename(columns={"rank": "rank_in_pool", score_col: "score"})
            frames.append(tmp)

        if not frames:
            return 0

        merged = pd.concat(frames, ignore_index=True).sort_values("score", ascending=False)
        # Deduplicate: each stock appears in only one strategy (highest score wins).
        merged = merged.drop_duplicates(subset=["code"], keep="first")

        count = 0
        for row in merged.to_dict("records"):
            action_plan = f"策略={row['signal']}；{row['reason']}"

            # Calculate trade points if we have current price
            trade_points = {}
            if "close" in row and row["close"] and row["close"] > 0:
                trade_points = self._calculate_trade_points(
                    row["code"], row["signal"], row["score"], row["close"]
                )

            self.db.upsert(
                "daily_signals",
                {
                    "date": date_value,
                    "code": row["code"],
                    "signal": row["signal"],
                    "score": float(row["score"]),
                    "rank_in_pool": int(row["rank_in_pool"]),
                    "reason": row["reason"],
                    "action_plan": action_plan,
                    **trade_points,  # Add entry_price, target_price, etc.
                },
                conflict_columns=["date", "code", "signal"],  # 每只股票每天只能有一个策略
            )
            count += 1
        return count

    def export_to_feishu(self, trade_date: Optional[str] = None) -> SyncResult:
        """Export daily_signals of one date to Feishu bitable table daily_signals."""
        service = FeishuSyncService(self.db, load_app_settings())
        date_value = trade_date or datetime.now().strftime("%Y-%m-%d")
        rows = self.db.fetch_all(
            """
            SELECT
                s.date, s.code, w.name, s.signal, s.score, s.reason, s.action_plan,
                s.entry_price, s.target_price, s.stop_loss_price, 
                s.position_size, s.expected_return, s.risk_reward_ratio,
                f.trend_score, f.momentum_score, f.volume_score,
                f.sentiment_score AS news_score,
                f.fundamental_score, f.reversal_score AS industry_score
            FROM daily_signals s
            LEFT JOIN watchlist w ON w.code=s.code
            LEFT JOIN factor_scores f ON f.date=s.date AND f.code=s.code
            WHERE s.date=?
            ORDER BY s.score DESC
            """,
            (date_value,),
        )
        payload = [_map_signal_row(r) for r in rows]
        return service.sync_rows("daily_signals", payload)


def _to_feishu_ts(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)


def _map_signal_row(r: Dict[str, Any]) -> Dict[str, Any]:
    mapping = {"short_term": "短线", "swing": "波段", "stable": "稳健"}
    return {
        "日期": _to_feishu_ts(r["date"]),
        "股票代码": r["code"],
        "股票名称": r.get("name") or "",
        "策略类型": mapping.get(r["signal"], "短线"),
        "综合得分": float(r.get("score") or 0),
        "推荐理由": r.get("reason") or "",
        "趋势因子分数": float(r.get("trend_score") or 0),
        "动量因子分数": float(r.get("momentum_score") or 0),
        "成交量因子分数": float(r.get("volume_score") or 0),
        "新闻因子分数": float(r.get("news_score") or 0),
        "基本面因子分数": float(r.get("fundamental_score") or 0),
        "行业因子分数": float(r.get("industry_score") or 0),
        "买入触发": r.get("action_plan") or "",
        "入场价": float(r.get("entry_price") or 0) if r.get("entry_price") else None,
        "目标价": float(r.get("target_price") or 0) if r.get("target_price") else None,
        "止损位": float(r.get("stop_loss_price") or 0) if r.get("stop_loss_price") else None,
        "仓位比例": float(r.get("position_size") or 0) if r.get("position_size") else None,
        "预期收益": float(r.get("expected_return") or 0) if r.get("expected_return") else None,
        "风险收益比": float(r.get("risk_reward_ratio") or 0) if r.get("risk_reward_ratio") else None,
        "风险等级": "中",
        "唯一键": f"signal:{r['date']}:{r['code']}:{r['signal']}",
    }
