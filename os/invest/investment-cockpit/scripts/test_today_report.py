"""Manual integration test: run today's full reporting workflow."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import socket
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.sync_feishu_bitable import run_sync
from scripts.update_data import run_update
from src.config.settings import load_app_settings
from src.data_ingestion.news_fetcher import NewsFetcher
from src.database.db_manager import DatabaseManager
from src.reporting.news_report import NewsReportGenerator
from src.reporting.report_generator import ReportGenerator
from src.utils.logger import setup_logger


def _can_resolve_market_hosts() -> bool:
    for host in ["query.sse.com.cn", "push2his.eastmoney.com"]:
        try:
            socket.gethostbyname(host)
        except OSError:
            return False
    return True


def _print_step(step_no: int, title: str) -> None:
    print(f"\\n[步骤 {step_no}] {title}")


def _print_result(message: str) -> None:
    print(f"[结果] {message}")


def run_test_today_report(days: int = 90) -> dict:
    settings = load_app_settings()
    logger = setup_logger("test_today_report", log_level=settings.log_level, log_dir=PROJECT_ROOT / "logs")
    db = DatabaseManager(db_path=settings.db_path, log_level=settings.log_level)

    report_date = datetime.now().strftime("%Y-%m-%d")
    started_at = datetime.now()

    print("=" * 70)
    print("今日报告集成测试开始")
    print(f"报告日期: {report_date}")
    print(f"开始时间: {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    logger.info("Manual today-report test started report_date=%s", report_date)

    _print_step(1, "检查行情数据源连通性")
    can_update = _can_resolve_market_hosts()
    if can_update:
        _print_result("行情源可访问，将执行数据更新")
    else:
        _print_result("行情源不可访问，将跳过数据更新")

    _print_step(2, "更新行情与基础数据")
    data_updated = False
    if can_update:
        run_update(days=days)
        data_updated = True
        _print_result(f"数据更新完成，更新窗口: 最近 {days} 天")
    else:
        logger.warning("Skip update_data because market data hosts are not reachable in current environment")
        _print_result("已跳过数据更新")

    _print_step(3, "生成主报告（日报、信号、建议）")
    artifacts = ReportGenerator(db=db, project_root=PROJECT_ROOT).generate(report_date=report_date, top_n=5)
    _print_result(
        f"主报告生成完成，信号数: {artifacts.signal_count}，风险等级: {artifacts.risk_level}"
    )
    _print_result(f"日报文件: {artifacts.report_file}")

    _print_step(4, "抓取组合相关新闻并生成新闻报告")
    news_fetcher = NewsFetcher(db=db, log_level=settings.log_level)
    portfolio_news = news_fetcher.fetch_portfolio_news(limit=10)
    news_report_file = NewsReportGenerator(project_root=PROJECT_ROOT).generate(
        news_list=portfolio_news,
        report_date=report_date,
    )
    _print_result(f"新闻抓取完成，新闻条数: {len(portfolio_news)}")
    _print_result(f"新闻报告文件: {news_report_file}")

    _print_step(5, "同步飞书多维表格")
    sync_summary = run_sync(report_date=report_date)
    synced_count = sync_summary.get("synced_record_count", "unknown") if isinstance(sync_summary, dict) else "unknown"
    _print_result(f"飞书同步完成，同步记录数: {synced_count}")

    finished_at = datetime.now()
    summary = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "report_date": report_date,
        "data_updated": data_updated,
        "signal_count": artifacts.signal_count,
        "risk_level": artifacts.risk_level,
        "daily_report_file": str(artifacts.report_file),
        "news_count": len(portfolio_news),
        "news_report_file": str(news_report_file),
        "feishu_sync": sync_summary,
    }

    out = PROJECT_ROOT / "logs" / f"test_today_report_{finished_at.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("Manual today-report test finished summary=%s", summary)

    print("\\n" + "=" * 70)
    print("今日报告集成测试完成")
    print(f"结束时间: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {summary['duration_seconds']} 秒")
    print("=" * 70)
    print("生成文件路径:")
    print(f"- 日报: {artifacts.report_file}")
    print(f"- 新闻报告: {news_report_file}")
    print(f"- 测试汇总: {out}")

    return summary


if __name__ == "__main__":
    run_test_today_report()
