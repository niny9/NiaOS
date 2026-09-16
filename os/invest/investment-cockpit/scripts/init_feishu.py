"""Initialize Feishu bitable schema and sync seed data from SQLite."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_client import FeishuApiError
from src.integrations.feishu_sync import FeishuSyncService
from src.portfolio.real_portfolio import RealPortfolioManager
from src.portfolio.trade_sync import TradeSyncService
from src.scoring.strategy_scorer import StrategyScorer
from src.universe.pool_manager import PoolManager


def update_env_file(key: str, value: str) -> None:
    """Update key in .env while preserving other lines."""
    env_path = PROJECT_ROOT / ".env"
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    target_prefix = f"{key}="
    replaced = False
    output: list[str] = []
    for line in lines:
        if line.startswith(target_prefix):
            output.append(f"{key}={value}")
            replaced = True
            continue
        output.append(line)

    if not replaced:
        output.append(f"{key}={value}")

    env_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def _classify_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, requests.Timeout):
        return "网络超时", "请检查网络连通性后重试。"
    if isinstance(exc, requests.ConnectionError):
        return "网络连接失败", "请检查本机网络、代理或 DNS 设置。"
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status in (401, 403):
            return f"权限错误(HTTP {status})", "请确认 FEISHU_APP_ID/FEISHU_APP_SECRET 有效且应用具备多维表格权限。"
        if status == 429:
            return "请求频率限制(HTTP 429)", "请稍后重试，或降低初始化频率。"
        return f"HTTP错误({status})", "请查看飞书开放平台接口日志。"
    if isinstance(exc, FeishuApiError):
        code = exc.code
        if code in (99991663, 1254290):
            return f"飞书配额/限流错误(code={code})", "请检查配额和频率限制后重试。"
        if code in (99991661, 99991668, 91403):
            return f"飞书权限错误(code={code})", "请在飞书开放平台为应用开通多维表格相关权限并重新授权。"
        return f"飞书业务错误(code={code})", "请根据错误码和 msg 排查接口参数与权限。"
    return "未知错误", "请检查配置与日志后重试。"


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, settings.log_level)
    service = FeishuSyncService(db, settings)

    if not service.enabled:
        raise RuntimeError("Feishu 未配置，请设置 FEISHU_APP_ID / FEISHU_APP_SECRET")

    try:
        bitable_url = f"https://feishu.cn/base/{settings.feishu_bitable_app_token}" if settings.feishu_bitable_app_token else ""
        if not settings.feishu_bitable_app_token:
            print("[1/4] 未检测到 FEISHU_BITABLE_APP_TOKEN，正在创建新的多维表格...")
            app_token, bitable_url = service.create_new_bitable("AI产业链投资驾驶舱")
            update_env_file("FEISHU_BITABLE_APP_TOKEN", app_token)
            print("[2/4] 已创建多维表格并写回 .env：FEISHU_BITABLE_APP_TOKEN")
        else:
            print("[1/4] 检测到 FEISHU_BITABLE_APP_TOKEN，复用已有多维表格并校验表结构...")

        table_map = service.ensure_remote_schema()
        print("[3/4] 表结构已就绪，正在同步初始化数据...")

        latest = db.fetch_one("SELECT MAX(date) AS d FROM daily_signals")
        signal_date = (latest or {}).get("d")

        summary = {
            "table_mapping": table_map,
            "positions": RealPortfolioManager(db).sync_to_feishu().__dict__,
            "trades": TradeSyncService(db).sync_to_feishu().__dict__,
            "watchlist": PoolManager(db).sync_to_feishu().__dict__,
            "signals": StrategyScorer(db).export_to_feishu(trade_date=signal_date).__dict__ if signal_date else {},
            "bitable_url": bitable_url,
        }

        print("[4/4] 初始化完成。")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"Feishu Bitable URL: {bitable_url}")
        print("FEISHU_BITABLE_APP_TOKEN 已自动写入 .env（若之前为空）。")
    except Exception as exc:
        category, suggestion = _classify_error(exc)
        raise RuntimeError(f"飞书初始化失败：{category}\n详情：{exc}\n建议：{suggestion}") from exc


if __name__ == "__main__":
    main()
