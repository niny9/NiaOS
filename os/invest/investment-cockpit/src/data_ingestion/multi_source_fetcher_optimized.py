"""
多数据源行情获取器
支持从多个数据源获取A股实时行情数据，并自动进行数据源切换和容错
"""

import pandas as pd
import akshare as ak
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 延迟导入可选依赖
try:
    import efinance as ef
    EFINANCE_AVAILABLE = True
except ImportError:
    EFINANCE_AVAILABLE = False
    logger.warning("efinance not installed, install with: pip install efinance")

try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    BAOSTOCK_AVAILABLE = False
    logger.warning("baostock not installed, install with: pip install baostock")


class MultiSourceFetcher:
    """多数据源行情获取器"""

    def __init__(self):
        # 数据源优先级：efinance > baostock > akshare > sina > tencent
        self.sources = []
        if EFINANCE_AVAILABLE:
            self.sources.append('efinance')
        if BAOSTOCK_AVAILABLE:
            self.sources.append('baostock')
        self.sources.extend(['akshare', 'sina', 'tencent'])

        self.current_source_index = 0
        self.bs_login = False  # baostock登录状态

    def __del__(self):
        """析构函数，确保baostock登出"""
        if BAOSTOCK_AVAILABLE and self.bs_login:
            try:
                bs.logout()
            except:
                pass

    def get_available_sources(self) -> List[str]:
        """获取可用的数据源列表"""
        return self.sources.copy()

    def set_source_priority(self, sources: List[str]):
        """设置数据源优先级"""
        self.sources = sources
        self.current_source_index = 0
