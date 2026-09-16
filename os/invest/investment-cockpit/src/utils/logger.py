"""Logging utilities for the investment cockpit project."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str, log_level: str = "INFO", log_dir: Optional[Path] = None) -> logging.Logger:
    """Create and configure a logger with console and optional file handlers.

    Args:
        name: Logger name.
        log_level: Logging level as string.
        log_dir: Optional directory for log files.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
