"""
新浪/腾讯实时行情获取器
基于easyquotation库，完全免费无需token
"""
import logging
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)


class RealtimeQuoteFetcher:
    """
    实时行情获取器
    基于新浪财经和腾讯财经的免费接口

    优势：
    - 完全免费，无需token
    - 实时数据（有15秒延迟）
    - 支持批量获取

    限制：
    - 可能被限流
    - 接口偶尔会变化
    """

    def __init__(self, source: str = "sina"):
        """
        初始化

        Args:
            source: 数据源 (sina/tencent)
        """
        self.source = source
        try:
            import easyquotation as eq  # type: ignore
            self.eq = eq
            self.available = True

            if source == "sina":
                self.quotation = eq.use('sina')
            elif source == "tencent":
                self.quotation = eq.use('tencent')
            else:
                self.quotation = eq.use('sina')

            logger.info(f"实时行情获取器已加载 (source={source})")
        except ImportError:
            self.available = False
            self.quotation = None
            logger.warning("easyquotation未安装，请运行: pip install easyquotation")

    def fetch_realtime_quote(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        获取实时行情

        Args:
            symbols: 股票代码列表 (如 ['600519', '000858'])

        Returns:
            实时行情字典
        """
        if not self.available:
            return None

        try:
            quotes = self.quotation.stocks(symbols)

            if not quotes:
                logger.warning(f"未获取到实时行情: {symbols}")
                return None

            logger.info(f"获取 {len(quotes)} 只股票的实时行情")
            return quotes

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None

    def fetch_single_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单只股票的实时行情

        Args:
            symbol: 股票代码

        Returns:
            行情数据
        """
        quotes = self.fetch_realtime_quote([symbol])
        if quotes and symbol in quotes:
            return quotes[symbol]
        return None

    def fetch_market_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        获取市场快照（主要指数）

        Returns:
            指数行情
        """
        if not self.available:
            return None

        try:
            # 获取主要指数
            indices = ['sh000001', 'sz399001', 'sz399006']  # 上证、深成指、创业板
            quotes = self.quotation.stocks(indices)

            logger.info(f"获取市场快照: {len(quotes)} 个指数")
            return quotes

        except Exception as e:
            logger.error(f"获取市场快照失败: {e}")
            return None


class AshareFetcher:
    """
    Ashare实时行情获取器
    新浪+腾讯双核心，自动故障切换

    GitHub: https://github.com/mpquant/Ashare
    """

    def __init__(self):
        try:
            from Ashare import Ashare  # type: ignore
            self.ashare = Ashare()
            self.available = True
            logger.info("Ashare已加载（新浪+腾讯双核心）")
        except ImportError:
            self.available = False
            logger.warning("Ashare未安装，请运行: pip install Ashare")

    def fetch_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取实时数据（自动切换新浪/腾讯）

        Args:
            symbol: 股票代码

        Returns:
            实时数据
        """
        if not self.available:
            return None

        try:
            # Ashare会自动在新浪和腾讯之间切换
            df = self.ashare.get_price(symbol)

            if df is None or df.empty:
                logger.warning(f"Ashare未获取到数据: {symbol}")
                return None

            # 转换为字典
            latest = df.iloc[-1].to_dict()
            logger.info(f"Ashare获取实时数据成功: {symbol}")
            return latest

        except Exception as e:
            logger.error(f"Ashare获取数据失败: {e}")
            return None


if __name__ == "__main__":
    # 测试实时行情获取
    print("=" * 60)
    print("测试实时行情获取")
    print("=" * 60)

    # 测试easyquotation (新浪)
    print("\n1. 测试easyquotation (新浪)...")
    fetcher_sina = RealtimeQuoteFetcher(source="sina")
    if fetcher_sina.available:
        quote = fetcher_sina.fetch_single_quote("600519")
        if quote:
            print(f"✅ 贵州茅台:")
            print(f"  当前价: {quote.get('now', 'N/A')}")
            print(f"  涨跌幅: {quote.get('changepercent', 'N/A')}%")
        else:
            print("❌ 获取失败")
    else:
        print("⚠️ easyquotation未安装")

    # 测试Ashare
    print("\n2. 测试Ashare (双核心)...")
    fetcher_ashare = AshareFetcher()
    if fetcher_ashare.available:
        data = fetcher_ashare.fetch_realtime_data("600519")
        if data:
            print(f"✅ Ashare获取成功")
            print(f"  数据: {data}")
        else:
            print("❌ 获取失败")
    else:
        print("⚠️ Ashare未安装")

    print("\n安装命令:")
    print("  pip install easyquotation")
    print("  pip install Ashare")
