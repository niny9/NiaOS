"""
降级获取器
多数据源降级机制，确保数据获取的可靠性
"""
import logging
from typing import Optional, Any, Dict, Callable, List

logger = logging.getLogger(__name__)


class FallbackFetcher:
    """
    多源降级获取器
    优先级：AKShare → Mootdx → 本地缓存 → 手动输入
    """

    def __init__(self):
        # 更新优先级：Baostock优先（免费稳定）→ AKShare → Mootdx → 本地 → 手动
        self.sources = ['baostock', 'akshare', 'easyquotation', 'ashare', 'mootdx', 'local', 'manual']
        self.fetch_methods: Dict[str, Dict[str, Callable]] = self._init_methods()

    def _init_methods(self) -> Dict[str, Dict[str, Callable]]:
        """初始化各数据类型的获取方法"""
        return {
            'prices': {
                'baostock': self._fetch_prices_baostock,
                'akshare': self._fetch_prices_akshare,
                'easyquotation': self._fetch_prices_easyquotation,
                'ashare': self._fetch_prices_ashare,
                'mootdx': self._fetch_prices_mootdx,
                'local': self._fetch_prices_local,
                'manual': self._fetch_prices_manual
            },
            'financial': {
                'baostock': self._fetch_financial_baostock,
                'akshare': self._fetch_financial_akshare,
                'local': self._fetch_financial_local,
                'manual': self._fetch_financial_manual
            },
            'announcements': {
                'akshare': self._fetch_announcements_akshare,
                'local': self._fetch_announcements_local
            }
        }

    def fetch_with_fallback(
        self,
        symbol: str,
        data_type: str,
        **kwargs: Any
    ) -> Optional[Dict[str, Any]]:
        """
        使用降级机制获取数据

        Args:
            symbol: 股票代码
            data_type: 数据类型 (prices/financial/announcements)
            **kwargs: 其他参数

        Returns:
            数据字典，如果所有源都失败则返回None
        """
        if data_type not in self.fetch_methods:
            logger.error(f"不支持的数据类型: {data_type}")
            return None

        methods = self.fetch_methods[data_type]
        sources_to_try = [s for s in self.sources if s in methods]

        for source in sources_to_try:
            try:
                logger.info(f"尝试从 {source} 获取 {data_type} 数据: {symbol}")
                method = methods[source]
                data = method(symbol, **kwargs)

                if data is not None:
                    logger.info(f"✅ 从 {source} 成功获取数据")
                    data['_source'] = source
                    return data
                else:
                    logger.warning(f"⚠️ {source} 返回空数据")

            except Exception as e:
                logger.error(f"❌ {source} 获取失败: {e}")
                continue

        logger.error(f"所有数据源都失败: {symbol} {data_type}")
        return None

    # ============ 行情数据获取方法 ============

    def _fetch_prices_baostock(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从Baostock获取历史行情（推荐！）"""
        try:
            from .baostock_fetcher import BaostockFetcher

            fetcher = BaostockFetcher()
            df = fetcher.fetch_history_k_data(symbol, start_date="2023-01-01")

            if df is None or df.empty:
                return None

            return {
                'symbol': symbol,
                'data': df.to_dict('records'),
                'latest': df.iloc[-1].to_dict(),
                'count': len(df),
                'source': 'baostock'
            }

        except Exception as e:
            logger.error(f"Baostock行情获取失败: {e}")
            return None

    def _fetch_prices_easyquotation(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从easyquotation获取实时行情"""
        try:
            from .realtime_quote_fetcher import RealtimeQuoteFetcher

            fetcher = RealtimeQuoteFetcher(source='sina')
            quote = fetcher.fetch_single_quote(symbol)

            if not quote:
                return None

            return {
                'symbol': symbol,
                'latest': quote,
                'source': 'easyquotation'
            }

        except Exception as e:
            logger.error(f"easyquotation行情获取失败: {e}")
            return None

    def _fetch_prices_ashare(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从Ashare获取实时行情（双核心）"""
        try:
            from .realtime_quote_fetcher import AshareFetcher

            fetcher = AshareFetcher()
            data = fetcher.fetch_realtime_data(symbol)

            if not data:
                return None

            return {
                'symbol': symbol,
                'latest': data,
                'source': 'ashare'
            }

        except Exception as e:
            logger.error(f"Ashare行情获取失败: {e}")
            return None

    def _fetch_prices_akshare(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从AKShare获取行情"""
        try:
            import akshare as ak  # type: ignore
            import pandas as pd  # type: ignore

            period = kwargs.get('period', 'daily')
            adjust = kwargs.get('adjust', 'qfq')

            df = ak.stock_zh_a_hist(symbol=symbol, period=period, adjust=adjust)

            if df is None or df.empty:
                return None

            return {
                'symbol': symbol,
                'data': df.to_dict('records'),
                'latest': df.iloc[-1].to_dict(),
                'count': len(df)
            }

        except Exception as e:
            logger.error(f"AKShare行情获取失败: {e}")
            return None

    def _fetch_prices_mootdx(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从Mootdx获取行情（预留）"""
        logger.warning("Mootdx行情获取未实现")
        return None

    def _fetch_prices_local(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从本地缓存获取行情（预留）"""
        logger.warning("本地缓存行情获取未实现")
        return None

    def _fetch_prices_manual(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """手动输入行情（预留）"""
        logger.warning("手动输入行情未实现")
        return None

    # ============ 财务数据获取方法 ============

    def _fetch_financial_baostock(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从Baostock获取财务数据（推荐！）"""
        try:
            from .baostock_fetcher import BaostockFetcher

            fetcher = BaostockFetcher()
            quarter_str = kwargs.get('quarter', '2024Q2')
            year, q = quarter_str.split('Q')

            return fetcher.fetch_financial_data(symbol, int(year), int(q))

        except Exception as e:
            logger.error(f"Baostock财务数据获取失败: {e}")
            return None

    def _fetch_financial_akshare(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从AKShare获取财务数据"""
        from .financial_report_fetcher import FinancialReportFetcher

        fetcher = FinancialReportFetcher()
        quarter = kwargs.get('quarter', '2024Q2')
        return fetcher.fetch_quarterly_report(symbol, quarter)

    def _fetch_financial_local(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从本地获取财务数据"""
        from .financial_report_fetcher import FinancialReportFetcher

        fetcher = FinancialReportFetcher()
        quarter = kwargs.get('quarter', '2024Q2')
        return fetcher._fetch_from_local(symbol, quarter)

    def _fetch_financial_manual(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """手动输入财务数据"""
        logger.warning("需要手动输入财务数据")
        return None

    # ============ 公告数据获取方法 ============

    def _fetch_announcements_akshare(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从AKShare获取公告"""
        from .announcement_fetcher import AnnouncementFetcher

        fetcher = AnnouncementFetcher()
        announcements = fetcher.fetch_announcements(symbol)

        if not announcements:
            return None

        return {
            'symbol': symbol,
            'announcements': announcements,
            'count': len(announcements)
        }

    def _fetch_announcements_local(self, symbol: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """从本地获取公告（预留）"""
        logger.warning("本地公告获取未实现")
        return None

    def test_all_sources(self, symbol: str = "600519") -> Dict[str, Any]:
        """
        测试所有数据源的可用性

        Returns:
            测试结果字典
        """
        results = {}

        for data_type in self.fetch_methods.keys():
            logger.info(f"\n测试 {data_type} 数据源...")
            data = self.fetch_with_fallback(symbol, data_type, quarter='2024Q2')

            results[data_type] = {
                'success': data is not None,
                'source': data.get('_source') if data else None
            }

        return results


if __name__ == "__main__":
    # 测试降级机制
    fetcher = FallbackFetcher()

    print("=" * 60)
    print("测试数据源降级机制")
    print("=" * 60)

    results = fetcher.test_all_sources("600519")

    print("\n测试结果:")
    for data_type, result in results.items():
        status = "✅" if result['success'] else "❌"
        source = result['source'] or "全部失败"
        print(f"  {status} {data_type:15s} -> {source}")
