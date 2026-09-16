"""Initialize AI watchlist core stocks into watchlist table with duplicate-skip logic."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager

AI_STOCKS = [
    # 算力基础设施
    {"code": "002415", "name": "海康威视", "category1": "算力基础设施", "category2": "服务器", "pool_status": "核心池"},
    {"code": "600845", "name": "宝信软件", "category1": "算力基础设施", "category2": "IDC", "pool_status": "核心池"},
    # 半导体
    {"code": "002049", "name": "紫光国微", "category1": "半导体", "category2": "AI芯片", "pool_status": "核心池"},
    # 光通信
    {"code": "300308", "name": "中际旭创", "category1": "光通信", "category2": "光模块", "pool_status": "核心池"},
    # 软件
    {"code": "002230", "name": "科大讯飞", "category1": "软件", "category2": "大模型平台", "pool_status": "核心池"},
    {"code": "688111", "name": "金山办公", "category1": "软件", "category2": "AI开发工具", "pool_status": "核心池"},
    # AI应用
    {"code": "300496", "name": "中科创达", "category1": "AI应用", "category2": "智能驾驶", "pool_status": "核心池"},
    # 智能硬件
    {"code": "300750", "name": "宁德时代", "category1": "智能硬件", "category2": "智能终端", "pool_status": "核心池"},
    {"code": "002475", "name": "立讯精密", "category1": "智能硬件", "category2": "智能终端", "pool_status": "观察池"},
    # ETF
    {"code": "515790", "name": "光伏ETF", "category1": "智能硬件", "category2": "工业自动化", "pool_status": "观察池"},
    {"code": "562500", "name": "机器人ETF", "category1": "智能硬件", "category2": "机器人", "pool_status": "核心池"},
    {"code": "159227", "name": "航空航天ETF", "category1": "智能硬件", "category2": "工业自动化", "pool_status": "观察池"},
]


def init_ai_watchlist(db: DatabaseManager) -> dict[str, int]:
    """Insert AI stocks into watchlist; skip records that already exist by code."""
    today = date.today().isoformat()
    inserted = 0
    skipped = 0

    insert_sql = """
    INSERT INTO watchlist (
        code, name, industry_chain_l1, industry_chain_l2,
        pool_status, add_date, note, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    for stock in AI_STOCKS:
        exists = db.fetch_one("SELECT 1 FROM watchlist WHERE code = ? LIMIT 1", (stock["code"],))
        if exists:
            skipped += 1
            continue

        db.execute(
            insert_sql,
            (
                stock["code"],
                stock["name"],
                stock["category1"],
                stock["category2"],
                stock["pool_status"],
                today,
                "AI产业链核心池初始化",
                today,
            ),
        )
        inserted += 1

    return {"total": len(AI_STOCKS), "inserted": inserted, "skipped": skipped}


def main() -> None:
    settings = load_app_settings()
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    stats = init_ai_watchlist(db)
    total_watchlist = db.fetch_one("SELECT COUNT(*) AS c FROM watchlist")

    print("AI watchlist initialization done")
    print(f"- total_input: {stats['total']}")
    print(f"- inserted: {stats['inserted']}")
    print(f"- skipped: {stats['skipped']}")
    print(f"- watchlist_count: {total_watchlist['c'] if total_watchlist else 0}")


if __name__ == "__main__":
    main()
