#!/usr/bin/env python3
"""Idempotently connect two existing skill entrypoints, preserving originals."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

START = "<!-- invest-os-routing:start -->"
END = "<!-- invest-os-routing:end -->"
BLOCK = """<!-- invest-os-routing:start -->
## Invest OS 综合任务路由

此 Skill 是统一 Invest OS 工作流的既有能力模块。完整投资早报、跨持仓/量化/财富目标的综合任务，先使用 `$invest-os`（`{entry}`）。原有单项系统检查、量化计算或五类对账操作仍由本 Skill 负责。

若调用方已传 `orchestration_context=invest-os.stage`，只执行分配阶段并返回带 run_id 的证据产物，不再次调用总流程。综合任务中的账户/政策检查、条件交易预案和最终简报由 Wealth OS 模块收口；旧示例仓位、止损比例和缓存不能当用户授权。

路由到总流程不增加外部消息、Base 写回、模拟成交、自动任务或交易权限；仅执行本轮具体授权的操作。缺数据保留 degraded/blocked，不能将安装或文件存在视作计算完成。
<!-- invest-os-routing:end -->
"""


def transform(text, entry):
    if START in text and END not in text or END in text and START not in text:
        raise ValueError("incomplete existing route marker")
    clean = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n*", "", text, flags=re.S)
    block = BLOCK.format(entry=entry)
    if clean.startswith("---\n"):
        closing = clean.find("\n---", 4)
        if closing < 0:
            raise ValueError("invalid skill frontmatter")
        offset = closing + len("\n---")
        return clean[:offset] + "\n\n" + block + "\n" + clean[offset:].lstrip("\n")
    return block + "\n" + clean.lstrip("\n")


def connect(codex_root, agent_root, backup_dir=None, apply=False):
    entry = (codex_root / "invest-os/SKILL.md").resolve()
    if not entry.is_file():
        raise ValueError("install invest-os before connecting existing skills")
    targets = [codex_root / "finance-quant-closed-loop/SKILL.md", agent_root / "investment-workflow/skill.md"]
    if apply and backup_dir is None:
        raise ValueError("--backup-dir is required with --apply")
    prepared, results = [], []
    for path in targets:
        if not path.is_file():
            results.append({"skill": path.parent.name, "status": "missing"})
            continue
        before = path.read_text(encoding="utf-8")
        after = transform(before, str(entry))
        sha = hashlib.sha256(before.encode()).hexdigest()
        prepared.append((path, before, after, sha))
        results.append({"skill": path.parent.name, "status": "unchanged" if before == after else ("connected" if apply else "planned")})
    for path, before, after, sha in prepared:
        if not apply or before == after:
            continue
        if path.read_text(encoding="utf-8") != before:
            raise ValueError("skill changed during connection; retry after inspection")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (path.parent.name + "-" + sha[:16] + ".md")
        if backup.exists() and backup.read_text(encoding="utf-8") != before:
            raise ValueError("backup collision")
        backup.write_text(before, encoding="utf-8")
        temporary = path.with_name(path.name + ".invest-os-tmp")
        with temporary.open("x", encoding="utf-8") as f:
            f.write(after)
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
        if path.read_text(encoding="utf-8") != after:
            raise ValueError("connection readback mismatch")
    return {"applied": apply, "results": results, "scheduler_changed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-skills", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home()/".codex"))/"skills")
    parser.add_argument("--agent-skills", type=Path, default=Path.home()/".agents/skills")
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(connect(args.codex_skills, args.agent_skills, args.backup_dir, args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
