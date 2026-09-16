#!/usr/bin/env python3
"""
周度参数优化任务
每周运行一次，使用最近3个月数据进行参数优化
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_sync import FeishuSyncService
from src.optimization.parameter_manager import ParameterManager, ParameterSet
from src.optimization.optimizer import ParameterOptimizer
from src.optimization.regime_detector import MarketRegime, RegimeDetector
from src.integrations.feishu_notifier import FeishuNotifier
from src.reporting.optimization_report import OptimizationReportGenerator
from src.scripts_support.week4_schema import ensure_week4_schema
from src.utils.logger import setup_logger

logger = setup_logger("WeeklyOptimization")


def define_search_space(current_params: ParameterSet, regime: MarketRegime) -> Dict[str, tuple[int, int]]:
    """定义参数搜索空间。"""
    base_space: Dict[str, tuple[int, int]] = {
        "trend_params.ma_short": (
            max(2, int(current_params.trend_params["ma_short"] * 0.8)),
            max(3, int(current_params.trend_params["ma_short"] * 1.2)),
        ),
        "trend_params.ma_mid": (
            max(5, int(current_params.trend_params["ma_mid"] * 0.8)),
            max(6, int(current_params.trend_params["ma_mid"] * 1.2)),
        ),
    }

    if regime == MarketRegime.BULL:
        base_space["trend_params.ma_short"] = (3, 10)
    elif regime == MarketRegime.BEAR:
        base_space["trend_params.ma_short"] = (10, 20)

    return base_space


def run_weekly_optimization() -> None:
    """运行周度优化。"""
    logger.info("=" * 60)
    logger.info("开始周度参数优化")
    logger.info("=" * 60)

    settings = load_app_settings()
    db = DatabaseManager(settings.db_path, log_level=settings.log_level)
    ensure_week4_schema(db)
    param_manager = ParameterManager(db)
    optimizer = ParameterOptimizer(db)
    regime_detector = RegimeDetector(db)
    notifier = FeishuNotifier(db, log_level=settings.log_level)
    report_generator = OptimizationReportGenerator(db=db, project_root=PROJECT_ROOT)

    logger.info("步骤1: 检测市场制度")
    regime_info = regime_detector.detect_current_regime()
    logger.info("当前市场制度: %s", regime_info.regime.value)
    logger.info("趋势: %.2f%%, 波动率: %.2f%%", regime_info.trend * 100, regime_info.volatility * 100)

    logger.info("步骤2: 获取当前参数")
    try:
        current_params = param_manager.get_active_version()
    except ValueError as exc:
        if "No active parameter version found" not in str(exc):
            raise
        logger.warning("未找到活跃参数版本，初始化默认参数版本")
        default_params = ParameterSet.get_default()
        version_id = param_manager.create_version(
            default_params,
            "Auto-initialized default parameter version",
        )
        param_manager.activate_version(version_id)
        current_params = param_manager.get_active_version()
    logger.info("当前版本: %s", current_params.version_name)

    logger.info("步骤3: 定义参数搜索空间")
    param_space = define_search_space(current_params, regime_info.regime)
    logger.info("搜索空间: %s", param_space)

    logger.info("步骤4: 运行参数优化")
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    best_params, best_score = optimizer.random_search(
        param_space=param_space,
        n_iterations=30,
        start_date=start_date,
        end_date=end_date,
        strategy_type="all",
        objective="sharpe_ratio",
    )
    logger.info("优化完成，最优分数: %.4f", best_score)

    logger.info("步骤5: 对比当前参数性能")
    current_score = optimizer._evaluate_params(
        current_params,
        start_date,
        end_date,
        "all",
        "sharpe_ratio",
    )
    logger.info("当前参数分数: %.4f", current_score)
    logger.info("优化后分数: %.4f", best_score)
    logger.info("提升幅度: %.4f", best_score - current_score)
    current_win_rate = optimizer._evaluate_params(current_params, start_date, end_date, "all", "win_rate")
    best_win_rate = optimizer._evaluate_params(best_params, start_date, end_date, "all", "win_rate")

    logger.info("步骤6: 决策是否切换参数")
    improvement = best_score - current_score
    threshold = 0.2

    if improvement > threshold:
        logger.info("提升幅度 %.4f > %.4f，切换参数", improvement, threshold)
        best_row = db.fetch_one(
            "SELECT id FROM parameter_versions WHERE version_name = ?",
            (best_params.version_name,),
        )
        if best_row is None:
            version_id = param_manager.create_version(
                best_params,
                f"Weekly optimization - {regime_info.regime.value} market",
            )
        else:
            version_id = int(best_row["id"])
        param_manager.activate_version(version_id)

        message = f"""📊 参数优化完成 - 已切换

🎯 市场制度: {regime_info.description}
📈 当前分数: {current_score:.4f}
✨ 优化后分数: {best_score:.4f}
📊 提升幅度: {improvement:.4f}

✅ 已切换到新参数版本
版本ID: {version_id}
版本名称: {best_params.version_name}

🔗 查看详情: 运行 /view-portfolio
"""
        notifier.send_text(message)
        switched = "是"
        switch_reason = f"提升幅度 {improvement:.4f} > 阈值 {threshold:.4f}"
    else:
        logger.info("提升幅度 %.4f < %.4f，保持当前参数", improvement, threshold)
        message = f"""📊 参数优化完成 - 保持不变

🎯 市场制度: {regime_info.description}
📈 当前分数: {current_score:.4f}
✨ 优化后分数: {best_score:.4f}
📊 提升幅度: {improvement:.4f}

⏸️ 提升不显著，保持当前参数
当前版本: {current_params.version_name}
"""
        notifier.send_text(message)
        switched = "否"
        switch_reason = f"提升幅度 {improvement:.4f} <= 阈值 {threshold:.4f}"

    db.upsert(
        "parameter_optimization_history",
        {
            "optimization_date": end_date,
            "old_version_name": current_params.version_name,
            "new_version_name": best_params.version_name,
            "optimization_method": "随机",
            "old_sharpe": float(current_score),
            "new_sharpe": float(best_score),
            "old_win_rate": float(current_win_rate),
            "new_win_rate": float(best_win_rate),
            "improvement": float(improvement),
            "switched": switched,
            "reason": switch_reason,
        },
        conflict_columns=["optimization_date", "old_version_name", "new_version_name", "optimization_method"],
    )

    try:
        feishu_service = FeishuSyncService(db, settings)
        feishu_service.ensure_remote_schema()
        feishu_service.sync_rows(
            "parameter_optimization_history",
            [
                {
                    "优化日期": int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000),
                    "旧参数版本": current_params.version_name,
                    "新参数版本": best_params.version_name,
                    "优化方法": "随机",
                    "旧Sharpe": float(current_score),
                    "新Sharpe": float(best_score),
                    "旧胜率": float(current_win_rate),
                    "新胜率": float(best_win_rate),
                    "改进幅度": float(improvement),
                    "是否切换": switched,
                    "切换原因": switch_reason,
                    "唯一键": f"opt:{end_date}:{current_params.version_name}:{best_params.version_name}:随机",
                }
            ],
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("同步参数优化历史到飞书失败，但本地记录已落库: %s", exc)

    report_path, report_md = report_generator.generate(report_date=end_date)
    notifier.send_optimization_report(
        report_date=end_date,
        report_path=str(report_path),
        summary="\n".join(report_md.splitlines()[0:8]),
    )
    logger.info("优化报告已生成: %s", report_path)

    logger.info("=" * 60)
    logger.info("周度参数优化完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_weekly_optimization()
