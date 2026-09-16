"""Daily markdown report builder."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd

from src.database.db_manager import DatabaseManager
from src.risk.risk_checker import RiskResult
from src.scoring.strategy_scorer import StrategyScores


class DailyReportBuilder:
    """Build daily investment markdown report with fixed template."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def _latest_index_rows(self) -> Dict[str, Dict[str, float]]:
        index_codes = {
            "INDEX:sh000001": "上证指数",
            "INDEX:sz399001": "深证成指",
            "INDEX:sz399006": "创业板指",
        }
        rows = self.db.fetch_all(
            """
            SELECT b.code, b.close, b.pct_chg
            FROM stock_daily_bar b
            JOIN (
                SELECT code, MAX(date) AS max_date FROM stock_daily_bar
                WHERE code IN ('INDEX:sh000001','INDEX:sz399001','INDEX:sz399006')
                GROUP BY code
            ) m ON m.code = b.code AND m.max_date = b.date
            """
        )
        out: Dict[str, Dict[str, float]] = {}
        for row in rows:
            code = row["code"]
            out[index_codes[code]] = {"close": float(row.get("close") or 0.0), "pct_chg": float(row.get("pct_chg") or 0.0)}
        return out

    def _ai_chain_rank(self) -> List[Dict[str, str]]:
        rows = self.db.fetch_all(
            """
            SELECT w.industry_chain_l2 AS chain, AVG(b.pct_chg) AS avg_chg
            FROM watchlist w
            JOIN (
                SELECT code, pct_chg
                FROM stock_daily_bar
                WHERE date=(SELECT MAX(date) FROM stock_daily_bar)
            ) b ON b.code = w.code
            GROUP BY w.industry_chain_l2
            ORDER BY avg_chg DESC
            LIMIT 10
            """
        )
        out: List[Dict[str, str]] = []
        for i, row in enumerate(rows, start=1):
            out.append(
                {
                    "rank": str(i),
                    "chain": row.get("chain") or "未分类",
                    "perf": f"{float(row.get('avg_chg') or 0.0):+.2f}%",
                    "reason": "资金流入" if float(row.get("avg_chg") or 0.0) >= 0 else "资金分歧",
                }
            )
        return out

    @staticmethod
    def _render_short(df: pd.DataFrame) -> str:
        if df.empty:
            return "| 股票 | 分数 | 逻辑 | 买入触发 | 止损 | 风险 |\n|---|---:|---|---|---|---|\n"
        lines = ["| 股票 | 分数 | 逻辑 | 买入触发 | 止损 | 风险 |", "|---|---:|---|---|---|---|"]
        for row in df.head(5).to_dict("records"):
            lines.append(
                f"| {row['code']} | {row['short_term_score']:.1f} | {row['reason']} | {row['buy_trigger']} | {row['stop_loss_rule']} | {row.get('risk_level','低')} |"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_swing(df: pd.DataFrame) -> str:
        if df.empty:
            return "| 股票 | 分数 | 当前区间 | 理想买点 | 减仓条件 | 风险 |\n|---|---:|---|---|---|---|\n"
        lines = ["| 股票 | 分数 | 当前区间 | 理想买点 | 减仓条件 | 风险 |", "|---|---:|---|---|---|---|"]
        for row in df.head(5).to_dict("records"):
            lines.append(
                f"| {row['code']} | {row['swing_score']:.1f} | {row['current_range']} | {row['ideal_buy_point']} | {row['reduce_condition']} | {row.get('risk_level','低')} |"
            )
        return "\n".join(lines) + "\n"

    @staticmethod
    def _render_stable(df: pd.DataFrame) -> str:
        if df.empty:
            return "| 股票 | 分数 | 长期逻辑 | 估值位置 | 证伪条件 | 风险 |\n|---|---:|---|---|---|---|\n"
        lines = ["| 股票 | 分数 | 长期逻辑 | 估值位置 | 证伪条件 | 风险 |", "|---|---:|---|---|---|---|"]
        for row in df.head(5).to_dict("records"):
            lines.append(
                f"| {row['code']} | {row['stable_score']:.1f} | {row['long_term_logic']} | {row['valuation_position']} | {row['falsification_condition']} | {row.get('risk_level','低')} |"
            )
        return "\n".join(lines) + "\n"

    def build(self, report_date: str, scores: StrategyScores, risk_result: RiskResult) -> str:
        """Build markdown report strictly following PRD section template."""
        idx = self._latest_index_rows()
        chain_rank = self._ai_chain_rank()

        ai_perf = 0.0
        if chain_rank:
            ai_perf = sum(float(item["perf"].replace("%", "")) for item in chain_rank[:5]) / min(5, len(chain_rank))

        position_rows = self.db.fetch_all("SELECT code, name, position_ratio FROM real_positions WHERE status='active'")

        report = [f"# AI产业链投资日报｜{report_date}", "", "## 1. 今日市场温度"]
        report.append(f"- 上证指数：{idx.get('上证指数',{}).get('close',0):.2f} ({idx.get('上证指数',{}).get('pct_chg',0):+.2f}%)")
        report.append(f"- 深证成指：{idx.get('深证成指',{}).get('close',0):.2f} ({idx.get('深证成指',{}).get('pct_chg',0):+.2f}%)")
        report.append(f"- 创业板指：{idx.get('创业板指',{}).get('close',0):.2f} ({idx.get('创业板指',{}).get('pct_chg',0):+.2f}%)")
        report.append(f"- AI产业链整体表现：{ai_perf:+.2f}%")
        report.append(f"- 今日市场风险等级：{risk_result.level}")

        report.extend(["", "## 2. AI产业链强弱排序", "| 排名 | 细分方向 | 今日表现 | 变化原因 |", "|---|---|---|---|"])
        if chain_rank:
            for item in chain_rank:
                report.append(f"| {item['rank']} | {item['chain']} | {item['perf']} | {item['reason']} |")
        else:
            report.append("| 1 | 待实现 | 0.00% | 待实现 |")

        report.extend(["", "## 3. 重要新闻/公告/催化"])
        news_section = self._generate_news_section(report_date)
        report.extend(news_section)
        report.extend(["", "## 4. 股票池变化", "### 新增", "无", "", "### 剔除", "无"])

        report.extend(["", "## 5. 短线候选 5 只", self._render_short(scores.short_term).rstrip()])
        report.extend(["", "## 6. 波段候选 5 只", self._render_swing(scores.swing).rstrip()])
        report.extend(["", "## 7. 稳健候选 5 只", self._render_stable(scores.stable).rstrip()])

        report.extend(["", "## 8. 真实持仓检查"])
        if not position_rows:
            report.append("当前无持仓")
        else:
            for row in position_rows:
                report.append(f"- {row['code']} {row['name']} 仓位{float(row.get('position_ratio') or 0.0):.1%}")
            if risk_result.alerts:
                report.append("- 风险提示：")
                for alert in risk_result.alerts[:10]:
                    report.append(f"  - [{alert.get('level','中')}] {alert.get('message','')}")

        report.extend(["", "## 9. 模型组合表现", "待实现（Week-4阶段）", "", "## 10. 明日重点观察", "- 关注短线候选的突破情况"])
        return "\n".join(report) + "\n"

    def _generate_news_section(self, trade_date: str) -> list:
        """Generate news section for candidates."""
        section = []
        
        # Get candidate codes
        signals = self.db.fetch_all("""
            SELECT DISTINCT code 
            FROM daily_signals 
            WHERE date = ?
        """, [trade_date])
        
        if not signals:
            section.append("无候选股票相关新闻")
            return section
        
        codes = [s['code'] for s in signals]
        
        # Get recent news for candidates
        news_list = []
        for code in codes:
            news = self.db.fetch_all("""
                SELECT title, date, source, related_codes
                FROM news_events
                WHERE related_codes = ?
                AND date >= date(?, '-7 days')
                ORDER BY date DESC
                LIMIT 3
            """, [code, trade_date])
            news_list.extend(news)
        
        if not news_list:
            section.append("近7日无重要新闻")
            return section
        
        # Group by date
        from collections import defaultdict
        by_date = defaultdict(list)
        for n in news_list:
            by_date[n['date']].append(n)
        
        # Format output
        for date in sorted(by_date.keys(), reverse=True):
            section.append(f"### {date}")
            for n in by_date[date][:5]:  # Max 5 per day
                section.append(f"- **{n['related_codes']}** {n['title']} ({n['source']})")
            section.append("")
        
        return section
