"""填充信号表现追踪数据到飞书表格"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.data_ingestion.data_fetcher import DataFetcher
from src.integrations.performance_sync import PerformanceSyncService
from scripts.update_signal_performance import (
    create_new_signal_tracking,
    update_signal_performance,
    update_daily_strategy_performance
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """填充追踪数据并同步到飞书"""
    logger.info("="*60)
    logger.info("开始填充信号表现追踪数据")
    logger.info("="*60)
    
    settings = load_app_settings()
    db = DatabaseManager(settings.db_path)
    fetcher = DataFetcher(log_level=settings.log_level)
    
    # 1. 检查 daily_signals 表是否有数据
    signals_count = db.fetch_one("SELECT COUNT(*) as cnt FROM daily_signals")['cnt']
    logger.info(f"daily_signals 表中有 {signals_count} 条记录")
    
    if signals_count == 0:
        logger.warning("daily_signals 表为空，需要先运行 daily_task.py 生成信号")
        return
    
    # 2. 创建追踪记录
    logger.info("\n步骤 1: 创建信号追踪记录...")
    try:
        create_new_signal_tracking(db)
        logger.info("✓ 信号追踪记录创建完成")
    except Exception as e:
        logger.error(f"创建追踪记录失败: {e}", exc_info=True)
    
    # 3. 更新表现数据
    logger.info("\n步骤 2: 更新信号表现...")
    try:
        update_signal_performance(db, fetcher)
        logger.info("✓ 信号表现更新完成")
    except Exception as e:
        logger.error(f"更新表现失败: {e}", exc_info=True)
    
    # 4. 更新策略统计
    logger.info("\n步骤 3: 更新策略统计...")
    try:
        update_daily_strategy_performance(db)
        logger.info("✓ 策略统计更新完成")
    except Exception as e:
        logger.error(f"更新统计失败: {e}", exc_info=True)
    
    # 5. 检查数据
    tracking_count = db.fetch_one("SELECT COUNT(*) as cnt FROM signal_performance_tracking")['cnt']
    perf_count = db.fetch_one("SELECT COUNT(*) as cnt FROM daily_strategy_performance")['cnt']
    
    logger.info(f"\n数据统计:")
    logger.info(f"  - signal_performance_tracking: {tracking_count} 条")
    logger.info(f"  - daily_strategy_performance: {perf_count} 条")
    
    # 6. 同步到飞书
    logger.info("\n步骤 4: 同步到飞书...")
    try:
        perf_sync = PerformanceSyncService(db, settings)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 同步信号表现追踪
        result1 = perf_sync.sync_signal_performance(date=today)
        logger.info(f"  - 信号表现追踪: 创建={result1.created}, 更新={result1.updated}, 跳过={result1.skipped}")
        
        # 同步每日策略表现
        result2 = perf_sync.sync_daily_strategy_performance(date=today)
        logger.info(f"  - 每日策略表现: 创建={result2.created}, 更新={result2.updated}, 跳过={result2.skipped}")
        
        logger.info("✓ 飞书同步完成")
    except Exception as e:
        logger.error(f"飞书同步失败: {e}", exc_info=True)
    
    logger.info("\n" + "="*60)
    logger.info("数据填充完成！")
    logger.info("="*60)
    logger.info(f"\n访问飞书查看: https://feishu.cn/base/{settings.feishu_bitable_app_token}")
    
    db.close()


if __name__ == "__main__":
    main()
