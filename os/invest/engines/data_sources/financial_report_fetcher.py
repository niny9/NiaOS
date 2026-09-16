"""
财报获取器
多源财报获取，支持降级
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialReportFetcher:
    """
    多源财报获取器
    数据源优先级：
    1. AKShare财报接口（免费，稳定）
    2. 巨潮资讯（官方，需要解析PDF）
    3. 手动上传PDF
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or "/Users/niny/NiaOS/os/invest/data/reconciliation/reports"
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def fetch_quarterly_report(self, symbol: str, quarter: str) -> Optional[Dict[str, Any]]:
        """
        获取季度财报

        Args:
            symbol: 股票代码（如 600519）
            quarter: 季度（如 2024Q3）

        Returns:
            结构化财报数据，包含关键指标
        """
        logger.info(f"开始获取 {symbol} {quarter} 季度财报")

        # 尝试方法1: AKShare
        data = self._fetch_from_akshare(symbol, quarter)
        if data:
            logger.info(f"从AKShare成功获取 {symbol} 财报")
            return data

        # 尝试方法2: 本地缓存
        data = self._fetch_from_local(symbol, quarter)
        if data:
            logger.info(f"从本地缓存获取 {symbol} 财报")
            return data

        # 尝试方法3: 手动上传
        logger.warning(f"无法自动获取 {symbol} {quarter} 财报，请手动上传到: {self.base_path}/{symbol}_{quarter}.json")
        return None

    def _fetch_from_akshare(self, symbol: str, quarter: str) -> Optional[Dict[str, Any]]:
        """从AKShare获取财报数据"""
        try:
            import akshare as ak
            import pandas as pd

            # 获取财务指标
            df = ak.stock_financial_analysis_indicator(symbol=symbol)

            if df is None or df.empty:
                return None

            # 解析季度
            year, q = quarter.split('Q')
            quarter_map = {'1': '03-31', '2': '06-30', '3': '09-30', '4': '12-31'}
            target_date = f"{year}-{quarter_map[q]}"

            # 查找对应季度数据
            df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
            matched = df[df['日期'] == target_date]

            if matched.empty:
                # 如果找不到精确匹配，返回最新数据
                matched = df.iloc[[0]]

            # 提取关键指标
            row = matched.iloc[0]

            return {
                'symbol': symbol,
                'quarter': quarter,
                'date': row.get('日期', ''),
                'revenue': float(row.get('营业总收入', 0)),
                'net_profit': float(row.get('净利润', 0)),
                'roe': float(row.get('净资产收益率', 0)),
                'gross_margin': float(row.get('销售毛利率', 0)),
                'debt_to_asset': float(row.get('资产负债率', 0)),
                'current_ratio': float(row.get('流动比率', 0)),
                'quick_ratio': float(row.get('速动比率', 0)),
                'receivables': float(row.get('应收账款', 0)) if '应收账款' in row else None,
                'inventory': float(row.get('存货', 0)) if '存货' in row else None,
                'operating_cashflow': float(row.get('经营活动现金流量净额', 0)) if '经营活动现金流量净额' in row else None,
                'source': 'akshare',
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"从AKShare获取财报失败: {e}")
            return None

    def _fetch_from_local(self, symbol: str, quarter: str) -> Optional[Dict[str, Any]]:
        """从本地缓存获取"""
        import json

        filepath = Path(self.base_path) / f"{symbol}_{quarter}.json"
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['source'] = 'local_cache'
                    return data
            except Exception as e:
                logger.error(f"读取本地缓存失败: {e}")

        return None

    def fetch_annual_report(self, symbol: str, year: int) -> Optional[Dict[str, Any]]:
        """
        获取年度财报（Q4数据）
        """
        return self.fetch_quarterly_report(symbol, f"{year}Q4")

    def save_manual_data(self, symbol: str, quarter: str, data: Dict[str, Any]) -> bool:
        """
        保存手动输入的财报数据
        """
        import json

        filepath = Path(self.base_path) / f"{symbol}_{quarter}.json"
        try:
            data['source'] = 'manual'
            data['saved_at'] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"手动财报数据已保存: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存手动数据失败: {e}")
            return False

    def parse_pdf_to_structured_data(self, pdf_path: str) -> Optional[Dict[str, Any]]:
        """
        解析PDF财报（未实现，预留接口）
        需要安装: pip install pdfplumber
        """
        logger.warning("PDF解析功能未实现，请使用save_manual_data()手动输入数据")
        return None


if __name__ == "__main__":
    # 测试
    fetcher = FinancialReportFetcher()
    data = fetcher.fetch_quarterly_report("600519", "2024Q2")
    if data:
        print(f"✅ 成功获取财报数据:")
        print(f"  营收: {data['revenue']:.2f} 万元")
        print(f"  净利润: {data['net_profit']:.2f} 万元")
        print(f"  ROE: {data['roe']:.2f}%")
    else:
        print("❌ 财报获取失败")
