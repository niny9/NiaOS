"""Generate markdown report for portfolio news."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class NewsReportGenerator:
    """Generate grouped stock news markdown and save to reports/."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.report_dir = project_root / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, news_list: List[Dict[str, Any]], report_date: str | None = None) -> Path:
        """Generate markdown report from structured news list and return file path."""
        report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        markdown = self._build_markdown(news_list=news_list, report_date=report_date)
        file_path = self.report_dir / f"news_report_{report_date}.md"
        file_path.write_text(markdown, encoding="utf-8")
        return file_path

    def _build_markdown(self, news_list: List[Dict[str, Any]], report_date: str) -> str:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in news_list:
            code = str(item.get("code") or "UNKNOWN")
            name = str(item.get("name") or "")
            key = f"{code} {name}".strip()
            grouped[key].append(item)

        lines = [f"# 持仓股票新闻汇总 {report_date}", ""]
        if not grouped:
            lines.append("暂无可用新闻。")
            return "\n".join(lines) + "\n"

        for stock_key in sorted(grouped.keys()):
            lines.append(f"## {stock_key}")
            lines.append("")
            stock_news = grouped[stock_key]
            for idx, row in enumerate(stock_news, start=1):
                title = str(row.get("title") or "无标题")
                publish_time = str(row.get("publish_time") or "未知时间")
                source = str(row.get("source") or "未知来源")
                url = str(row.get("url") or "")
                lines.append(f"### {idx}. {title}")
                lines.append(f"- 时间: {publish_time}")
                lines.append(f"- 来源: {source}")
                if url:
                    lines.append(f"- 链接: {url}")
                lines.append("")
        return "\n".join(lines) + "\n"
