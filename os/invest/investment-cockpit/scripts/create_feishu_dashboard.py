#!/usr/bin/env python3
"""Create Feishu dashboard config and try to create it via API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_client import FeishuApiError, FeishuClient
from src.integrations.feishu_sync import FeishuSyncService
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger


def _dashboard_payload(app_token: str) -> dict:
    # NOTE: Widget schema may vary by Feishu tenant/version; keep payload explicit and auditable.
    return {
        "name": "Investment Cockpit Dashboard",
        "description": "自动生成：推荐信号、因子、胜率、参数优化、持仓盈亏",
        "widgets": [
            {
                "name": "推荐股票表现趋势图",
                "type": "line",
                "table": "daily_signals",
                "x": "日期",
                "y": "平均涨跌幅",
                "group_by": "策略类型",
            },
            {
                "name": "因子分数分布图",
                "type": "bar",
                "table": "daily_signals",
                "metrics": ["趋势因子分数", "动量因子分数", "成交量因子分数", "新闻因子分数", "基本面因子分数", "行业因子分数"],
            },
            {
                "name": "策略胜率统计",
                "type": "pie",
                "table": "daily_signals",
                "group_by": "涨跌标签",
            },
            {
                "name": "参数优化历史",
                "type": "line",
                "table": "parameter_optimization_history",
                "x": "优化日期",
                "y": ["旧Sharpe", "新Sharpe"],
            },
            {
                "name": "持仓盈亏分布",
                "type": "bar",
                "table": "real_positions",
                "x": "股票代码",
                "y": "盈亏金额",
            },
        ],
        "meta": {
            "app_token": app_token,
            "generated_at": datetime.now().isoformat(),
        },
    }


def run() -> dict:
    settings = load_app_settings()
    logger = setup_logger("create_feishu_dashboard", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    ensure_week4_schema(db)

    service = FeishuSyncService(db, settings)
    table_mapping = {}
    schema_error = None
    try:
        table_mapping = service.ensure_remote_schema()
    except Exception as exc:  # pylint: disable=broad-except
        schema_error = str(exc)
        logger.warning("Failed to ensure Feishu schema before dashboard creation: %s", exc)

    app_token = (settings.feishu_bitable_app_token or "").strip()
    payload = _dashboard_payload(app_token)
    payload["table_mapping"] = table_mapping

    out_dir = PROJECT_ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"feishu_dashboard_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {"saved_config": str(out_path), "api_created": False, "api_response": None, "schema_error": schema_error}

    if not (settings.feishu_app_id and settings.feishu_app_secret and app_token):
        logger.warning("Skip dashboard API create: missing FEISHU_APP_ID/SECRET/BITABLE_APP_TOKEN")
        return result

    client = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    api_path = f"/open-apis/bitable/v1/apps/{app_token}/dashboards"
    try:
        api_resp = client.request("POST", api_path, json=payload)
        result["api_created"] = True
        result["api_response"] = api_resp
        logger.info("Dashboard created via API path=%s", api_path)
    except FeishuApiError as exc:
        logger.warning(
            "Dashboard API create failed, keep JSON for manual import. code=%s msg=%s path=%s",
            exc.code,
            exc.feishu_msg,
            api_path,
        )
        result["api_response"] = {"code": exc.code, "msg": exc.feishu_msg}
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Dashboard API create failed, keep JSON for manual import: %s", exc)
        result["api_response"] = {"error": str(exc)}

    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
