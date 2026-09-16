"""Export reports to Obsidian vault."""

from __future__ import annotations

from pathlib import Path


class ObsidianExporter:
    """Persist report markdown into Obsidian folders and update overview."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.daily_dir = self.project_root / "obsidian" / "01_每日简报"
        self.overview_file = self.project_root / "obsidian" / "00_总览" / "日报总览.md"

    def export(self, report_date: str, markdown: str) -> Path:
        """Write daily report and append one-line index into overview file."""
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.overview_file.parent.mkdir(parents=True, exist_ok=True)

        filename = f"{report_date}_AI产业链投资日报.md"
        output = self.daily_dir / filename
        output.write_text(markdown, encoding="utf-8")

        if not self.overview_file.exists():
            self.overview_file.write_text("# 日报总览\n\n", encoding="utf-8")

        line = f"- [[01_每日简报/{filename}|{report_date} AI产业链投资日报]]\n"
        content = self.overview_file.read_text(encoding="utf-8")
        if line not in content:
            self.overview_file.write_text(content + line, encoding="utf-8")
        return output
