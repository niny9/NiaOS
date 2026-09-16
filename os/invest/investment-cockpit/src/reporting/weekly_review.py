"""Weekly review report generator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService, SyncResult
from src.portfolio.model_portfolio import ModelPortfolioManager
from src.portfolio.real_portfolio import RealPortfolioManager
from src.reporting.review_analyzer import ReviewAnalyzer


@dataclass
class WeeklyReviewArtifacts:
    """Weekly review output metadata."""

    file_path: Path
    markdown: str
    logged_rows: int


class WeeklyReviewGenerator:
    """Build weekly review markdown and export to Obsidian."""

    def __init__(self, db: DatabaseManager, project_root: Path) -> None:
        self.db = db
        self.project_root = project_root
        self.model = ModelPortfolioManager(db)
        self.real = RealPortfolioManager(db)
        self.analyzer = ReviewAnalyzer(db)
        self.out_dir = project_root / "obsidian" / "05_交易复盘"

    def generate(self, start_date: str, end_date: str, week_label: str) -> WeeklyReviewArtifacts:
        """Generate and persist one weekly review report."""
        model_stats = {p: self.model.get_stats(p) for p in ["short_term", "swing", "stable"]}
        real_pnl = self.real.calculate_pnl()

        rec_rows = self.analyzer.analyze_recommendation_returns(start_date, end_date)
        deviation = self.analyzer.analyze_execution_deviation(start_date, end_date)
        executed_codes = {t["code"] for t in self.db.fetch_all(
            "SELECT code FROM real_trades WHERE trade_date BETWEEN ? AND ? AND side='buy' AND status='active'",
            (start_date, end_date),
        )}
        for r in rec_rows:
            r["executed"] = r["code"] in executed_codes
        deviation_map = {
            t["code"]: (t.get("deviation_reason") or "")
            for t in self.db.fetch_all(
                "SELECT code, deviation_reason FROM real_trades WHERE trade_date BETWEEN ? AND ?",
                (start_date, end_date),
            )
        }
        attribution = self.analyzer.attribution_analysis(rec_rows)
        suggestions = self.analyzer.improvement_suggestions(attribution)
        logged = self.analyzer.persist_review_log(end_date, rec_rows, deviation_map)
        md = self._build_markdown(
            week_label=week_label,
            start_date=start_date,
            end_date=end_date,
            model_stats=model_stats,
            real_pnl=real_pnl,
            deviation=deviation,
            attribution=attribution,
            suggestions=suggestions,
        )

        self.out_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.out_dir / f"{week_label}_周度复盘.md"
        file_path.write_text(md, encoding="utf-8")
        return WeeklyReviewArtifacts(file_path=file_path, markdown=md, logged_rows=logged)

    def export_to_feishu(self, start_date: str, end_date: str, week_label: str) -> SyncResult:
        """Export one weekly review summary row to Feishu."""
        service = FeishuSyncService(self.db, load_app_settings())
        model_stats = {p: self.model.get_stats(p) for p in ["short_term", "swing", "stable"]}
        real_pnl = self.real.calculate_pnl()
        deviation = self.analyzer.analyze_execution_deviation(start_date, end_date)
        suggestions = self.analyzer.improvement_suggestions(
            self.analyzer.attribution_analysis(self.analyzer.analyze_recommendation_returns(start_date, end_date))
        )
        row = {
            "周次": week_label,
            "开始日期": _to_feishu_ts(start_date),
            "结束日期": _to_feishu_ts(end_date),
            "短线组合收益": model_stats["short_term"].total_return,
            "波段组合收益": model_stats["swing"].total_return,
            "稳健组合收益": model_stats["stable"].total_return,
            "真实组合收益": real_pnl["total_pnl_ratio"],
            "推荐数量": deviation["recommended"],
            "执行数量": deviation["executed"],
            "执行率": deviation["execution_rate"],
            "主要收获": "；".join(suggestions[:3]),
            "唯一键": f"weekly:{week_label}",
        }
        return service.sync_rows("weekly_review", [row])

    def _build_markdown(
        self,
        week_label: str,
        start_date: str,
        end_date: str,
        model_stats: Dict[str, object],
        real_pnl: Dict[str, object],
        deviation: Dict[str, object],
        attribution: Dict[str, int],
        suggestions: List[str],
    ) -> str:
        market = self._market_overview(start_date, end_date)
        lines = [
            f"# 周度复盘｜{week_label}（{start_date}至{end_date}）",
            "",
            "## 1. 本周市场回顾",
            f"- 上证指数：{market}",
            "- 市场特征：震荡结构（基于指数区间变化）",
            "",
            "## 2. 模型组合表现",
        ]
        mapping = {"short_term": "短线组合", "swing": "波段组合", "stable": "稳健组合"}
        for key in ["short_term", "swing", "stable"]:
            stat = model_stats[key]
            lines.extend([
                f"### {mapping[key]}",
                f"- 累计收益：{stat.total_return:.2%}",
                f"- 最大回撤：-{stat.max_drawdown:.2%}",
                f"- 胜率：{stat.win_rate:.2%}",
                f"- 盈亏比：{stat.profit_loss_ratio:.2f}",
                f"- 交易次数：{stat.trade_count}次",
                "",
            ])

        lines.extend([
            "## 3. 真实组合表现",
            f"- 本周收益（按当前持仓估算）：{real_pnl['total_pnl_ratio']:.2%}",
            f"- 持仓数量：{len(real_pnl['positions'])}只",
            "",
            "## 4. 推荐执行情况",
            f"- 本周推荐：{deviation['recommended']}只",
            f"- 实际执行：{deviation['executed']}只",
            f"- 执行率：{deviation['execution_rate']:.2%}",
            "",
            "## 5. 偏离分析",
            "### 模型推荐但未执行",
            "| 股票 | 策略 | 推荐日期 | 未执行原因 |",
            "|---|---|---|---|",
        ])
        for u in deviation["unexecuted"][:10]:
            lines.append(f"| {u['code']} | {u['signal']} | {u['date']} | 未记录 |")

        lines.extend([
            "",
            "### 未推荐但人工买入",
            "| 股票 | 买入日期 | 买入原因 |",
            "|---|---|---|",
        ])
        for m in deviation["manual_buys"][:10]:
            lines.append(f"| {m['code']} | {m['trade_date']} | {m.get('deviation_reason') or '人工判断'} |")

        lines.extend([
            "",
            "## 6. 策略有效性分析",
            f"- 模型对：{attribution['模型对']}，模型错：{attribution['模型错']}",
            f"- 人对：{attribution['人对']}，人错：{attribution['人错']}",
            f"- 市场变了：{attribution['市场变了']}",
            "",
            "## 7. 下周改进建议",
        ])
        for i, s in enumerate(suggestions, start=1):
            lines.append(f"{i}. {s}")

        lines.extend(["", "## 数据质量报告", *self._data_quality_lines(start_date, end_date)])
        return "\\n".join(lines) + "\\n"

    def _market_overview(self, start_date: str, end_date: str) -> str:
        s = self.db.fetch_one("SELECT close FROM stock_daily_bar WHERE code='INDEX:000001' AND date=?", (start_date,))
        e = self.db.fetch_one("SELECT close FROM stock_daily_bar WHERE code='INDEX:000001' AND date=?", (end_date,))
        if not s or not e or s.get("close") is None or e.get("close") is None:
            return "指数数据缺失"
        start_close = float(s["close"])
        end_close = float(e["close"])
        pct = (end_close / start_close - 1.0) * 100
        return f"{start_close:.2f} → {end_close:.2f} ({pct:+.2f}%)"

    def _data_quality_lines(self, start_date: str, end_date: str) -> List[str]:
        suspended = self.db.fetch_one(
            "SELECT COUNT(1) AS cnt FROM stock_basic WHERE is_active=0"
        )
        missing_price = self.db.fetch_one(
            """
            SELECT COUNT(1) AS cnt FROM daily_signals s
            LEFT JOIN stock_daily_bar b ON s.code=b.code AND b.date=s.date
            WHERE s.date BETWEEN ? AND ? AND b.close IS NULL
            """,
            (start_date, end_date),
        )
        return [
            f"- 退市/停牌标记数量：{int((suspended or {}).get('cnt', 0))}",
            f"- 推荐信号缺失行情数量：{int((missing_price or {}).get('cnt', 0))}",
        ]


def _to_feishu_ts(date_str: str) -> int:
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
