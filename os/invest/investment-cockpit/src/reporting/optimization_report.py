"""Optimization report generator for weekly parameter iteration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.database.db_manager import DatabaseManager


class OptimizationReportGenerator:
    """Build markdown reports for parameter optimization history."""

    def __init__(self, db: DatabaseManager, project_root: Path) -> None:
        self.db = db
        self.project_root = project_root
        self.output_dir = project_root / "obsidian" / "03_参数优化"

    def generate(self, report_date: str | None = None) -> tuple[Path, str]:
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        current = self.db.fetch_one(
            """
            SELECT id, version_name, description, created_date, status, performance_score, created_at
            FROM parameter_versions
            WHERE status='active'
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        )
        latest_opt = self.db.fetch_one(
            """
            SELECT id, optimization_date, strategy_type, method, best_version_id, best_score, iterations, duration_seconds, created_at
            FROM optimization_history
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """
        )
        recent_versions = self.db.fetch_all(
            """
            SELECT id, version_name, created_date, status, performance_score, created_at
            FROM parameter_versions
            ORDER BY created_at DESC, id DESC
            LIMIT 12
            """
        )
        perf_rows = self.db.fetch_all(
            """
            SELECT pv.version_name, pp.sharpe_ratio, pp.win_rate, pp.profit_loss_ratio, pp.total_return, pp.test_start_date, pp.test_end_date, pp.created_at
            FROM parameter_performance pp
            JOIN parameter_versions pv ON pv.id = pp.version_id
            ORDER BY pp.created_at DESC, pp.id DESC
            LIMIT 20
            """
        )

        markdown = self._build_markdown(report_date, current, latest_opt, recent_versions, perf_rows)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / f"{report_date}_参数优化报告.md"
        output.write_text(markdown, encoding="utf-8")
        return output, markdown

    def _build_markdown(
        self,
        report_date: str,
        current: dict[str, Any] | None,
        latest_opt: dict[str, Any] | None,
        recent_versions: list[dict[str, Any]],
        perf_rows: list[dict[str, Any]],
    ) -> str:
        lines: list[str] = [
            f"# 参数优化报告 - {report_date}",
            "",
            "## 当前参数版本信息",
        ]

        if current:
            lines.extend(
                [
                    f"- 版本ID: {current['id']}",
                    f"- 版本名: {current['version_name']}",
                    f"- 状态: {current['status']}",
                    f"- 创建日期: {current['created_date']}",
                    f"- 描述: {current.get('description') or 'N/A'}",
                    f"- 绩效分数: {self._fmt(current.get('performance_score'))}",
                ]
            )
        else:
            lines.append("- 暂无激活参数版本")

        lines.extend(["", "## 最近一次优化结果"])
        if latest_opt:
            lines.extend(
                [
                    f"- 优化日期: {latest_opt['optimization_date']}",
                    f"- 方法: {latest_opt['method']}",
                    f"- 策略: {latest_opt['strategy_type']}",
                    f"- 最优版本ID: {latest_opt.get('best_version_id')}",
                    f"- 最优分数: {self._fmt(latest_opt.get('best_score'))}",
                    f"- 迭代次数: {latest_opt.get('iterations')}",
                    f"- 耗时(秒): {self._fmt(latest_opt.get('duration_seconds'))}",
                ]
            )
        else:
            lines.append("- 暂无优化历史")

        lines.extend(["", "## 参数变化历史", "", "| 时间 | 版本 | 状态 | 分数 |", "|---|---|---|---|"])
        for row in recent_versions:
            lines.append(
                f"| {row.get('created_date') or ''} | {row.get('version_name') or ''} | {row.get('status') or ''} | {self._fmt(row.get('performance_score'))} |"
            )

        lines.extend(["", "## 性能对比", "", "| 版本 | 窗口 | Sharpe | 胜率 | 盈亏比 | 收益率 |", "|---|---|---:|---:|---:|---:|"])
        for row in perf_rows[:10]:
            window = f"{row.get('test_start_date')}~{row.get('test_end_date')}"
            lines.append(
                f"| {row.get('version_name')} | {window} | {self._fmt(row.get('sharpe_ratio'))} | {self._fmt_pct(row.get('win_rate'))} | {self._fmt(row.get('profit_loss_ratio'))} | {self._fmt_pct(row.get('total_return'))} |"
            )

        lines.extend(["", "## 参数变化趋势（文本）", "", "```text"])
        for row in recent_versions[:8][::-1]:
            score = self._to_float(row.get("performance_score"))
            bar_len = max(0, min(40, int((score + 1.0) * 10)))
            lines.append(f"{row.get('version_name', ''):20} {'#' * bar_len} {self._fmt(score)}")
        lines.extend(["```", "", "## 下次优化建议"])

        latest_sharpe = self._latest_sharpe(perf_rows)
        if latest_sharpe < 0.5:
            lines.append("- 当前最新Sharpe低于0.5，建议本周增加搜索迭代次数并扩大参数空间。")
        else:
            lines.append("- 当前性能稳定，建议维持当前参数并关注行业轮动带来的结构性变化。")
        lines.append("- 建议固定在每周日22:00运行优化任务并输出本报告。")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _to_float(v: Any) -> float:
        try:
            if v is None:
                return 0.0
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def _latest_sharpe(self, rows: list[dict[str, Any]]) -> float:
        for row in rows:
            if row.get("sharpe_ratio") is not None:
                return self._to_float(row.get("sharpe_ratio"))
        return 0.0

    def _fmt(self, v: Any) -> str:
        return f"{self._to_float(v):.4f}"

    def _fmt_pct(self, v: Any) -> str:
        return f"{self._to_float(v) * 100:.2f}%"

