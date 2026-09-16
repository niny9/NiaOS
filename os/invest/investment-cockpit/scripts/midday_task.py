#!/usr/bin/env python3
"""午间决策任务 - 每天12:30运行。"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import load_app_settings
from src.database.db_manager import DatabaseManager
from src.integrations.feishu_notifier import FeishuNotifier
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'midday_task.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """午间决策主任务"""
    logger.info("=" * 50)
    logger.info(f"开始执行午间决策任务 - {datetime.now()}")
    logger.info("=" * 50)

    try:
        settings = load_app_settings()
        db = DatabaseManager(settings.db_path, log_level=settings.log_level)
        notifier = FeishuNotifier(db=db, log_level=settings.log_level)
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 获取今日关注股票的实时表现
        logger.info("1. 分析今日关注股票表现...")
        signals = db.fetch_all(
            """
            WITH today AS (
                SELECT s.code, s.signal, COALESCE(w.name, '') AS name, s.score
                FROM daily_signals s
                LEFT JOIN watchlist w ON w.code = s.code
                WHERE s.date = ?
            ),
            latest2 AS (
                SELECT b.code, b.close,
                       ROW_NUMBER() OVER(PARTITION BY b.code ORDER BY b.date DESC) AS rn
                FROM stock_daily_bar b
                WHERE b.code IN (SELECT code FROM today)
            ),
            perf AS (
                SELECT code,
                       MAX(CASE WHEN rn=1 THEN close END) AS last_close,
                       MAX(CASE WHEN rn=2 THEN close END) AS prev_close
                FROM latest2
                GROUP BY code
            )
            SELECT t.code, t.name, t.signal, t.score,
                   CASE
                       WHEN p.prev_close IS NOT NULL AND p.prev_close > 0
                       THEN (p.last_close - p.prev_close) * 100.0 / p.prev_close
                       ELSE NULL
                   END AS pct_chg
            FROM today t
            LEFT JOIN perf p ON p.code = t.code
            ORDER BY t.score DESC
            """,
            (today,),
        )

        if signals:
            logger.info(f"   今日关注 {len(signals)} 只股票")

            # 2. 生成午间决策建议
            logger.info("\n📊 午间决策建议：")
            logger.info("=" * 50)

            strategy_map = {"short_term": "短线", "swing": "波段", "stable": "稳健"}
            for sig in signals[:5]:  # 前5只重点关注
                pct = sig.get("pct_chg")
                pct_text = "数据待更新" if pct is None else f"{float(pct):+.2f}%"
                logger.info(f"\n🎯 {sig['code']} {sig['name']}")
                logger.info(f"   策略: {strategy_map.get(sig['signal'], sig['signal'])}")
                logger.info(f"   评分: {sig['score']:.2f}")
                logger.info(f"   表现: {pct_text}")
                logger.info("   建议: 结合分时强弱，优先考虑强势股回调机会")

            logger.info("\n" + "=" * 50)
            logger.info("💡 操作提示：")
            logger.info("   - 上午强势股：关注回调买入机会")
            logger.info("   - 上午弱势股：观望为主，等待企稳信号")
            logger.info("   - 控制仓位：单只股票不超过总仓位20%")
            logger.info("=" * 50)
        else:
            logger.info("   暂无关注股票")

        # 2. 发送飞书午盘通知
        logger.info("2. 发送飞书午盘通知...")
        sent = notifier.send_midday_decision(report_date=today)
        logger.info("   飞书午盘通知发送结果: %s", sent)

        logger.info("\n午间决策任务执行完成！")

    except Exception as e:
        logger.error(f"午间决策任务执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
