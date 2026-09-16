"""Feishu group webhook notifier."""

from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Any, Dict, List
from urllib import error, request

from src.database.db_manager import DatabaseManager
from src.utils.logger import setup_logger


class FeishuNotifier:
    """Send text notifications to Feishu group via webhook."""

    def __init__(self, db: DatabaseManager, log_level: str = "INFO") -> None:
        self.db = db
        self.logger = setup_logger(self.__class__.__name__, log_level=log_level)
        self.webhook_url = os.getenv("FEISHU_WEBHOOK_INVESTMENT", "https://open.feishu.cn/open-apis/bot/v2/hook/42dc5011-e3ba-451e-9671-b660df521552").strip()

    def send_text(self, text: str) -> bool:
        """Send plain text message to Feishu group webhook."""
        if not self.webhook_url:
            self.logger.warning("Skip Feishu notification: FEISHU_WEBHOOK is empty")
            return False

        payload = {
            "msg_type": "text",
            "content": {"text": text},
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                status = getattr(resp, "status", 200)
                ok = 200 <= status < 300
                if not ok:
                    self.logger.error("Feishu webhook returned non-2xx status: %s", status)
                return ok
        except (error.URLError, TimeoutError, OSError) as exc:
            self.logger.exception("Failed to send Feishu notification: %s", exc)
            return False

    def send_daily_report(self, report_date: str | None = None) -> bool:
        """Build and send daily investment brief.

        Sections:
        1) 持仓概况
        2) 今日表现
        3) 风险提示
        """
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        positions = self._fetch_active_positions()
        if not positions:
            return self.send_text(f"📊 投资简报 {report_date}\n\n当前无持仓数据")

        total_cost = sum(float(p.get("cost") or 0.0) for p in positions)
        total_market = sum(float(p.get("market_value") or 0.0) for p in positions)
        total_profit = total_market - total_cost
        total_profit_pct = (total_profit / total_cost * 100.0) if total_cost > 0 else 0.0

        best = max(positions, key=lambda x: float(x.get("profit_pct") or 0.0))
        worst = min(positions, key=lambda x: float(x.get("profit_pct") or 0.0))
        risk_lines = self._build_risk_lines(positions)

        lines = [
            f"📊 投资简报 {report_date}",
            "",
            "📈 持仓概况",
            f"持仓: {len(positions)}只",
            f"总市值: ¥{total_market:,.2f}",
            f"总盈亏: ¥{total_profit:,.2f} ({total_profit_pct:+.2f}%)",
            "",
            "🎯 今日表现",
            f"最佳: {best.get('code', '')} {best.get('name', '')} ({float(best.get('profit_pct') or 0.0):+.2f}%)",
            f"最弱: {worst.get('code', '')} {worst.get('name', '')} ({float(worst.get('profit_pct') or 0.0):+.2f}%)",
            "",
            "⚠️ 风险提示",
        ]
        lines.extend(risk_lines)
        return self.send_text("\n".join(lines))

    def send_morning_signals(self, report_date: str | None = None, top_n: int = 3) -> bool:
        """Send grouped strategy recommendations for morning session."""
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        rows = self.db.fetch_all(
            """
            SELECT s.signal, s.code, COALESCE(w.name, '') AS name, s.score, s.reason,
                   s.entry_price, s.target_price, s.stop_loss_price, s.expected_return,
                   ROW_NUMBER() OVER (PARTITION BY s.signal ORDER BY s.score DESC) AS rank_no
            FROM daily_signals s
            LEFT JOIN watchlist w ON w.code = s.code
            WHERE s.date = ?
            ORDER BY s.signal, s.score DESC
            """,
            (report_date,),
        )
        if not rows:
            return self.send_text(f"📊 今日推荐 {report_date}\n\n暂无推荐股票")

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            signal = str(row.get("signal") or "")
            grouped.setdefault(signal, [])
            if len(grouped[signal]) < top_n:
                grouped[signal].append(row)

        signal_names = {"short_term": "短线策略", "swing": "波段策略", "stable": "稳健策略"}
        lines = [f"📊 今日推荐 {report_date}", ""]
        for signal in ("short_term", "swing", "stable"):
            picks = grouped.get(signal, [])
            if not picks:
                continue
            lines.append(f"{self._signal_emoji(signal)} {signal_names.get(signal, signal)} (Top {len(picks)})")
            for idx, pick in enumerate(picks, 1):
                lines.append(
                    f"{idx}. {pick.get('code', '')} {pick.get('name', '')} 评分:{float(pick.get('score') or 0.0):.1f}"
                )
                reason = str(pick.get("reason") or "暂无")
                lines.append(f"   理由：{reason}")
                # Add buy/sell points if available
                if pick.get('entry_price'):
                    entry = float(pick.get('entry_price'))
                    target = float(pick.get('target_price') or 0)
                    stop = float(pick.get('stop_loss_price') or 0)
                    exp_return = float(pick.get('expected_return') or 0) * 100
                    lines.append(f"   入场:{entry:.2f} 目标:{target:.2f} 止损:{stop:.2f} 预期:{exp_return:.1f}%")
            lines.append("")

        lines.extend(
            [
                "💡 操作提示：",
                "- 关注开盘表现",
                "- 控制仓位",
            ]
        )
        return self.send_text("\n".join(lines))

    def send_midday_decision(self, report_date: str | None = None) -> bool:
        """Send midday decision notification based on today's recommended stocks."""
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        rows = self.db.fetch_all(
            """
            WITH today AS (
                SELECT s.code, s.signal, COALESCE(w.name, '') AS name, s.score
                FROM daily_signals s
                LEFT JOIN watchlist w ON w.code = s.code
                WHERE s.date = ?
            ),
            latest2 AS (
                SELECT b.code, b.close,
                       ROW_NUMBER() OVER(PARTITION BY b.code ORDER BY b.date DESC) AS rn
                FROM stock_daily_bar b
                WHERE b.code IN (SELECT code FROM today)
            ),
            perf AS (
                SELECT code,
                       MAX(CASE WHEN rn=1 THEN close END) AS last_close,
                       MAX(CASE WHEN rn=2 THEN close END) AS prev_close
                FROM latest2
                GROUP BY code
            )
            SELECT t.code, t.name, t.signal, t.score, p.last_close, p.prev_close,
                   CASE
                       WHEN p.prev_close IS NOT NULL AND p.prev_close > 0
                       THEN (p.last_close - p.prev_close) * 100.0 / p.prev_close
                       ELSE NULL
                   END AS pct_chg
            FROM today t
            LEFT JOIN perf p ON p.code = t.code
            ORDER BY t.score DESC
            """,
            (report_date,),
        )
        if not rows:
            return self.send_text(f"📊 午盘决策 {report_date} 12:30\n\n暂无今日推荐股票")

        strong = 0
        weak = 0
        flat = 0
        lines = [f"📊 午盘决策 {report_date} 12:30", "", "🎯 今日推荐表现"]
        for row in rows[:10]:
            pct = row.get("pct_chg")
            if pct is None:
                marker = "⚪"
                perf_text = "数据待更新"
            else:
                pct_val = float(pct)
                if pct_val >= 1.5:
                    marker = "✅"
                    strong += 1
                elif pct_val <= -1.0:
                    marker = "⚠️"
                    weak += 1
                else:
                    marker = "▫️"
                    flat += 1
                perf_text = f"{pct_val:+.2f}%"
            lines.append(f"{marker} {row.get('code', '')} {row.get('name', '')} {perf_text} ({self._signal_cn(row.get('signal'))})")

        lines.extend(
            [
                "",
                "💡 下午操作建议：",
                f"- 强势股({strong}只)：关注回调买入",
                f"- 弱势股({weak}只)：观望为主",
                f"- 震荡股({flat}只)：等待方向确认",
                "- 控制仓位：单只不超过20%",
            ]
        )
        return self.send_text("\n".join(lines))

    def send_midday_advice(self, report_date: str | None = None) -> bool:
        """Backward-compatible alias for midday decision notification."""
        return self.send_midday_decision(report_date=report_date)

    def send_bitable_sync_summary(
        self,
        report_date: str,
        table_stats: list[dict[str, Any]],
        base_url: str = "",
    ) -> bool:
        """Send Feishu bitable sync completion summary."""
        lines = [f"📊 飞书多维表格已更新 {report_date}", ""]
        for item in table_stats:
            table_name = str(item.get("table_name") or item.get("table") or "未知表")
            records = int(item.get("records") or 0)
            lines.append(f"✅ {table_name}: {records}条记录")

        if base_url:
            lines.extend(["", f"🔗 查看: {base_url}"])
        return self.send_text("\n".join(lines))

    def send_parameter_monitor_alert(self, report: dict[str, Any]) -> bool:
        """Send alert for parameter performance degradation."""
        metrics = report.get("metrics", {})
        degrade = report.get("degradation", {})
        lines = [
            "⚠️ 参数性能预警",
            "",
            f"版本: {report.get('version_name', 'unknown')} (ID: {report.get('version_id', 'N/A')})",
            f"30日Sharpe: {float(metrics.get('rolling_30d_sharpe') or 0.0):.4f}",
            f"30日胜率: {float(metrics.get('rolling_30d_win_rate') or 0.0) * 100:.2f}%",
            f"30日盈亏比: {float(metrics.get('rolling_30d_profit_loss_ratio') or 0.0):.4f}",
            f"连续低于阈值次数: {int(degrade.get('consecutive_below_threshold') or 0)}",
            "",
            "建议: 立即运行周度优化或手动检查参数有效性。",
        ]
        return self.send_text("\n".join(lines))

    def send_optimization_report(self, report_date: str, report_path: str, summary: str = "") -> bool:
        """Send weekly optimization report summary notification."""
        lines = [
            f"📈 周度参数优化报告 {report_date}",
            "",
            f"报告文件: {report_path}",
        ]
        if summary.strip():
            lines.extend(["", "摘要:", summary.strip()])
        return self.send_text("\n".join(lines))

    def send_weekly_report(
        self,
        week_label: str,
        start_date: str,
        end_date: str,
        report_path: str,
        metrics: dict[str, Any],
    ) -> bool:
        """Send weekly report summary with key metrics and report path."""
        lines = [
            f"🗂️ 投资周报 {week_label}",
            f"区间: {start_date} ~ {end_date}",
            "",
            "关键指标：",
            f"- 策略推荐数: {int(metrics.get('signal_count', 0))}",
            f"- 策略胜率: {float(metrics.get('signal_win_rate', 0.0)) * 100:.1f}%",
            f"- 交易次数: {int(metrics.get('trade_count', 0))} (买{int(metrics.get('buy_count', 0))}/卖{int(metrics.get('sell_count', 0))})",
            f"- 本周收益率: {float(metrics.get('weekly_return_pct', 0.0)):+.2f}%",
            f"- 累计收益率: {float(metrics.get('cumulative_return_pct', 0.0)):+.2f}%",
            f"- 执行率: {float(metrics.get('execution_rate', 0.0)) * 100:.1f}%",
            "",
            f"📄 报告: {report_path}",
        ]
        return self.send_text("\n".join(lines))

    def _fetch_active_positions(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                code,
                name,
                quantity,
                cost_price,
                market_price,
                (quantity * cost_price) AS cost,
                (quantity * market_price) AS market_value,
                (quantity * market_price - quantity * cost_price) AS profit,
                CASE
                    WHEN quantity * cost_price > 0 THEN
                        (quantity * market_price - quantity * cost_price) * 100.0 / (quantity * cost_price)
                    ELSE 0
                END AS profit_pct
            FROM real_positions
            WHERE status = 'active'
            ORDER BY code
        """
        return self.db.fetch_all(sql)

    @staticmethod
    def _build_risk_lines(positions: List[Dict[str, Any]]) -> List[str]:
        stop_loss = [p for p in positions if float(p.get("profit_pct") or 0.0) <= -15.0]
        warning = [p for p in positions if -15.0 < float(p.get("profit_pct") or 0.0) <= -10.0]

        lines: List[str] = []
        if not stop_loss and not warning:
            return ["当前无明显止损/预警仓位"]

        if stop_loss:
            lines.append(f"建议止损: {len(stop_loss)}只")
            for row in stop_loss:
                lines.append(
                    f"- {row.get('code', '')} {row.get('name', '')} ({float(row.get('profit_pct') or 0.0):+.2f}%)"
                )
        if warning:
            lines.append(f"重点关注: {len(warning)}只")
            for row in warning:
                lines.append(
                    f"- {row.get('code', '')} {row.get('name', '')} ({float(row.get('profit_pct') or 0.0):+.2f}%)"
                )
        return lines

    @staticmethod
    def _signal_cn(signal: Any) -> str:
        mapping = {"short_term": "短线", "swing": "波段", "stable": "稳健"}
        return mapping.get(str(signal), str(signal))

    @staticmethod
    def _signal_emoji(signal: str) -> str:
        mapping = {"short_term": "🔥", "swing": "📈", "stable": "💎"}
        return mapping.get(signal, "📌")
