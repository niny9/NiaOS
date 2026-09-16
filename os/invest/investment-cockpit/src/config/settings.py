"""Configuration loading and management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import os

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "src" / "config"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "database" / "investment.db"


@dataclass
class AppSettings:
    """Application settings container."""

    env: str
    db_path: Path
    log_level: str
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_bitable_app_token: str = ""
    feishu_webhook_url: str = ""
    feishu_bot_webhook: str = "https://open.feishu.cn/open-apis/bot/v2/hook/42dc5011-e3ba-451e-9671-b660df521552"
    data_source_priority: str = "akshare,sina,tencent,netease"
    tushare_token: str = ""
    data_source_multi_enabled: bool = True


class ConfigLoader:
    """YAML configuration loader with basic validation."""

    def __init__(self, config_dir: Path = CONFIG_DIR) -> None:
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing YAML config files.
        """
        self.config_dir = config_dir

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML file from config directory.

        Args:
            filename: YAML file name.

        Returns:
            Parsed YAML as dictionary.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If YAML content is empty.
        """
        file_path = self.config_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            raise ValueError(f"Config file is empty: {file_path}")

        return data

    def load_universe(self) -> Dict[str, Any]:
        """Load stock universe configuration."""
        return self.load_yaml("universe.yaml")

    def load_factor_config(self) -> Dict[str, Any]:
        """Load factor configuration."""
        return self.load_yaml("factor_config.yaml")

    def load_risk_config(self) -> Dict[str, Any]:
        """Load risk configuration."""
        return self.load_yaml("risk_config.yaml")


def load_app_settings() -> AppSettings:
    """Load app settings from environment variables and defaults.

    Returns:
        AppSettings instance.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    env = os.getenv("ENV", "dev")
    db_path_raw = os.getenv("DB_PATH", str(DEFAULT_DB_PATH))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    feishu_app_id = os.getenv("FEISHU_APP_ID", "")
    feishu_app_secret = os.getenv("FEISHU_APP_SECRET", "")
    feishu_bitable_app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
    feishu_webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "")
    feishu_bot_webhook = os.getenv(
        "FEISHU_BOT_WEBHOOK",
        "https://open.feishu.cn/open-apis/bot/v2/hook/42dc5011-e3ba-451e-9671-b660df521552",
    )
    data_source_priority = os.getenv("DATA_SOURCE_PRIORITY", "akshare,sina,tencent,netease")
    tushare_token = os.getenv("TUSHARE_TOKEN", "")
    data_source_multi_enabled = os.getenv("DATA_SOURCE_MULTI_ENABLED", "1") == "1"

    db_path = Path(db_path_raw)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path

    return AppSettings(
        env=env,
        db_path=db_path,
        log_level=log_level,
        feishu_app_id=feishu_app_id,
        feishu_app_secret=feishu_app_secret,
        feishu_bitable_app_token=feishu_bitable_app_token,
        feishu_webhook_url=feishu_webhook_url,
        feishu_bot_webhook=feishu_bot_webhook,
        data_source_priority=data_source_priority,
        tushare_token=tushare_token,
        data_source_multi_enabled=data_source_multi_enabled,
    )
