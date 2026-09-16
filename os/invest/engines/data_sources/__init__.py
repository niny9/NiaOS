"""
数据源模块
整合多种数据源，提供统一的数据获取接口
"""
import os
import logging

# 配置代理白名单，避免东方财富等网站被阻塞
os.environ['NO_PROXY'] = 'eastmoney.com,*.eastmoney.com,sina.com.cn,*.sina.com.cn,cninfo.com.cn,*.cninfo.com.cn'
os.environ['no_proxy'] = 'localhost,127.0.0.1,eastmoney.com,sina.com.cn,cninfo.com.cn'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("数据源模块初始化完成，代理配置已设置")

from .financial_report_fetcher import FinancialReportFetcher
from .announcement_fetcher import AnnouncementFetcher
from .research_report_fetcher import ResearchReportFetcher
from .earnings_call_fetcher import EarningsCallFetcher
from .fallback_fetcher import FallbackFetcher
from .data_acquisition_workflow import DataAcquisitionWorkflow
from .baostock_fetcher import BaostockFetcher
from .realtime_quote_fetcher import RealtimeQuoteFetcher, AshareFetcher

__all__ = [
    'FinancialReportFetcher',
    'AnnouncementFetcher',
    'ResearchReportFetcher',
    'EarningsCallFetcher',
    'FallbackFetcher',
    'DataAcquisitionWorkflow',
    'BaostockFetcher',
    'RealtimeQuoteFetcher',
    'AshareFetcher'
]
