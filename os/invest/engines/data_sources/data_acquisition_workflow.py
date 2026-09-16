"""
数据获取工作流
统一的数据获取入口，整合所有数据源
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .financial_report_fetcher import FinancialReportFetcher
from .announcement_fetcher import AnnouncementFetcher
from .research_report_fetcher import ResearchReportFetcher
from .earnings_call_fetcher import EarningsCallFetcher
from .fallback_fetcher import FallbackFetcher

logger = logging.getLogger(__name__)


class DataAcquisitionWorkflow:
    """
    统一数据获取工作流
    整合所有数据源，提供一站式数据获取
    """

    def __init__(self):
        self.financial_fetcher = FinancialReportFetcher()
        self.announcement_fetcher = AnnouncementFetcher()
        self.research_fetcher = ResearchReportFetcher()
        self.call_fetcher = EarningsCallFetcher()
        self.fallback_fetcher = FallbackFetcher()

    def acquire_full_company_data(
        self,
        symbol: str,
        quarter: str
    ) -> Dict[str, Any]:
        """
        获取公司完整数据

        Args:
            symbol: 股票代码
            quarter: 季度（如 2024Q3）

        Returns:
            包含所有数据的字典
        """
        logger.info(f"开始获取 {symbol} {quarter} 的完整数据")

        result = {
            'symbol': symbol,
            'quarter': quarter,
            'acquired_at': datetime.now().isoformat(),
            'data': {},
            'status': {}
        }

        # 1. 基础行情数据
        logger.info("1/5 获取行情数据...")
        prices = self.fallback_fetcher.fetch_with_fallback(symbol, 'prices')
        result['data']['prices'] = prices
        result['status']['prices'] = 'success' if prices else 'failed'

        # 2. 财务报表
        logger.info("2/5 获取财务报表...")
        financial = self.financial_fetcher.fetch_quarterly_report(symbol, quarter)
        result['data']['financial'] = financial
        result['status']['financial'] = 'success' if financial else 'failed'

        # 3. 公司公告
        logger.info("3/5 获取公司公告...")
        announcements = self.announcement_fetcher.fetch_announcements(symbol)
        result['data']['announcements'] = announcements
        result['status']['announcements'] = 'success' if announcements else 'failed'

        # 4. 券商研报
        logger.info("4/5 获取券商研报...")
        research = self.research_fetcher.fetch_research_reports(symbol, days=90)
        result['data']['research'] = research
        result['status']['research'] = 'success' if research else 'failed'

        # 5. 电话会议
        logger.info("5/5 获取电话会议记录...")
        earnings_call = self.call_fetcher.fetch_earnings_call_transcript(symbol, quarter)
        result['data']['earnings_call'] = earnings_call
        result['status']['earnings_call'] = 'success' if earnings_call else 'failed'

        # 统计成功率
        success_count = sum(1 for v in result['status'].values() if v == 'success')
        total_count = len(result['status'])
        result['success_rate'] = f"{success_count}/{total_count}"

        logger.info(f"数据获取完成，成功率: {result['success_rate']}")

        return result

    def acquire_essential_data(
        self,
        symbol: str,
        quarter: str
    ) -> Dict[str, Any]:
        """
        获取核心数据（仅财报和行情）

        适用于快速分析场景
        """
        logger.info(f"获取 {symbol} {quarter} 核心数据")

        result = {
            'symbol': symbol,
            'quarter': quarter,
            'acquired_at': datetime.now().isoformat(),
            'data': {}
        }

        # 财务数据
        financial = self.financial_fetcher.fetch_quarterly_report(symbol, quarter)
        result['data']['financial'] = financial

        # 行情数据
        prices = self.fallback_fetcher.fetch_with_fallback(symbol, 'prices')
        result['data']['prices'] = prices

        return result


if __name__ == "__main__":
    # 测试完整数据获取
    workflow = DataAcquisitionWorkflow()

    print("=" * 60)
    print("测试完整数据获取工作流")
    print("=" * 60)

    result = workflow.acquire_full_company_data("600519", "2024Q2")

    print(f"\n获取结果:")
    print(f"  股票: {result['symbol']}")
    print(f"  季度: {result['quarter']}")
    print(f"  成功率: {result['success_rate']}")
    print(f"\n详细状态:")
    for key, status in result['status'].items():
        icon = "✅" if status == 'success' else "❌"
        print(f"  {icon} {key:15s} -> {status}")
