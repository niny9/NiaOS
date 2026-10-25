#!/usr/bin/env python3
"""Invest OS repository entrypoint for the installed agent workflow helper."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    script = Path(__file__).resolve().parents[1] / "skills/invest-os/scripts/invest_workflow.py"
    runpy.run_path(str(script), run_name="__main__")
