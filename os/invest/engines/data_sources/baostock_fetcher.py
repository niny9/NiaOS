"""
Baostock数据源
完全免费、无需token的A股数据接口
官网: http://baostock.com/
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class BaostockFetcher:
    """
    Baostock数据获取器

    优势：
    - 完全免费，无需注册token
    - 数据全面：日K、财务、公告、分红等
    - 稳定可靠，API不会突然变化

    限制：
    - 无实时数据（最新到上一个交易日）
    - 需要login/logout会话管理
    """

    def __init__(self):
        try:
            import baostock as bs  # type: ignore
            self.bs = bs
            self.available = True
            self._logged_in = False
            logger.info("Baostock已加载")
        except ImportError:
            self.available = False
            logger.warning("Baostock未安装，请运行: pip install baostock")
            self.bs = None

    def _login(self) -> bool:
        """登录Baostock"""
        if not self.available or self._logged_in:
            return self._logged_in

        try:
            lg = self.bs.login()
            if lg.error_code == '0':
                self._logged_in = True
                logger.info("Baostock登录成功")
                return True
            else:
                logger.error(f"Baostock登录失败: {lg.error_msg}")
                return False
        except Exception as e:
            logger.error(f"Baostock登录异常: {e}")
            return False

    def _logout(self):
        """登出Baostock"""
        if self.available and self._logged_in:
            self.bs.logout()
            self._logged_in = False

    def __del__(self):
        """析构时自动登出"""
        self._logout()

    def fetch_history_k_data(
        self,
        symbol: str,
        start_date: str = "2020-01-01",
        end_date: Optional[str] = None,
        frequency: str = "d"
    ) -> Optional[pd.DataFrame]:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码（如 sh.600519）
            start_date: 开始日期
            end_date: 结束日期（默认今天）
            frequency: d=日k, w=周k, m=月k, 5=5分钟, 15=15分钟等

        Returns:
            K线数据DataFrame
        """
        if not self.available:
            return None

        if not self._login():
            return None

        # 处理股票代码格式
        if not symbol.startswith(('sh.', 'sz.')):
            if symbol.startswith('6'):
                symbol = f'sh.{symbol}'
            else:
                symbol = f'sz.{symbol}'

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        try:
            rs = self.bs.query_history_k_data_plus(
                symbol,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag="3"  # 1=后复权, 2=前复权, 3=不复权
            )

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning(f"Baostock未获取到数据: {symbol}")
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"Baostock获取 {len(df)} 条K线数据")
            return df

        except Exception as e:
            logger.error(f"Baostock获取K线失败: {e}")
            return None

    def fetch_financial_data(
        self,
        symbol: str,
        year: int,
        quarter: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务数据

        Args:
            symbol: 股票代码
            year: 年份
            quarter: 季度（1-4）

        Returns:
            财务数据字典
        """
        if not self.available or not self._login():
            return None

        # 处理股票代码格式
        if not symbol.startswith(('sh.', 'sz.')):
            if symbol.startswith('6'):
                symbol = f'sh.{symbol}'
            else:
                symbol = f'sz.{symbol}'

        try:
            # 获取季度业绩快报
            rs = self.bs.query_performance_express_report(symbol, start_date=f"{year}-01-01", end_date=f"{year}-12-31")

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning(f"Baostock未获取到财务数据: {symbol}")
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 筛选对应季度
            quarter_map = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
            target_date = f"{year}-{quarter_map[quarter]}"

            matched = df[df['performanceExpPubDate'].str.contains(target_date, na=False)]

            if matched.empty:
                # 如果没有精确匹配，返回最新一条
                matched = df.iloc[[0]]

            row = matched.iloc[0]

            return {
                'symbol': symbol,
                'year': year,
                'quarter': quarter,
                'revenue': float(row.get('operatingRevenue', 0)) if row.get('operatingRevenue') else None,
                'net_profit': float(row.get('netProfit', 0)) if row.get('netProfit') else None,
                'eps': float(row.get('EPS', 0)) if row.get('EPS') else None,
                'roe': float(row.get('ROE', 0)) if row.get('ROE') else None,
                'source': 'baostock',
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Baostock获取财务数据失败: {e}")
            return None

    def fetch_dividend_data(self, symbol: str, year: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """
        获取分红配股数据

        Args:
            symbol: 股票代码
            year: 年份（可选）

        Returns:
            分红配股记录列表
        """
        if not self.available or not self._login():
            return None

        # 处理股票代码格式
        if not symbol.startswith(('sh.', 'sz.')):
            if symbol.startswith('6'):
                symbol = f'sh.{symbol}'
            else:
                symbol = f'sz.{symbol}'

        try:
            rs = self.bs.query_dividend_data(code=symbol, year=str(year) if year else "", yearType="report")

            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                logger.warning(f"Baostock未获取到分红数据: {symbol}")
                return None

            df = pd.DataFrame(data_list, columns=rs.fields)

            # 转换为字典列表
            dividends = []
            for _, row in df.iterrows():
                dividends.append({
                    'dividend_year': row.get('dividendYear'),
                    'dividend_date': row.get('dividendDate'),
                    'cash_dividend': float(row.get('cashDividendRatio', 0)) if row.get('cashDividendRatio') else 0,
                    'stock_dividend': float(row.get('stockDividendRatio', 0)) if row.get('stockDividendRatio') else 0,
                })

            logger.info(f"Baostock获取 {len(dividends)} 条分红记录")
            return dividends

        except Exception as e:
            logger.error(f"Baostock获取分红数据失败: {e}")
            return None


if __name__ == "__main__":
    # 测试Baostock
    fetcher = BaostockFetcher()

    if fetcher.available:
        print("=" * 60)
        print("测试Baostock数据获取")
        print("=" * 60)

        # 1. 测试K线数据
        print("\n1. 获取K线数据...")
        df = fetcher.fetch_history_k_data("600519", start_date="2024-01-01")
        if df is not None:
            print(f"✅ 获取 {len(df)} 条K线")
            print(f"最新: {df.iloc[-1]['date']} 收盘价: {df.iloc[-1]['close']}")
        else:
            print("❌ K线获取失败")

        # 2. 测试财务数据
        print("\n2. 获取财务数据...")
        financial = fetcher.fetch_financial_data("600519", 2024, 2)
        if financial:
            print(f"✅ 获取财务数据")
            print(f"营收: {financial.get('revenue')}")
            print(f"净利润: {financial.get('net_profit')}")
        else:
            print("❌ 财务数据获取失败")

        # 3. 测试分红数据
        print("\n3. 获取分红数据...")
        dividends = fetcher.fetch_dividend_data("600519", 2023)
        if dividends:
            print(f"✅ 获取 {len(dividends)} 条分红记录")
            for div in dividends:
                print(f"  {div['dividend_date']}: 现金分红 {div['cash_dividend']}")
        else:
            print("❌ 分红数据获取失败")

    else:
        print("❌ Baostock未安装")
        print("请运行: pip install baostock")
