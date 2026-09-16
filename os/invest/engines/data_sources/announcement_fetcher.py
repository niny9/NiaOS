"""
公告获取器
从东方财富/AKShare获取公司公告
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnnouncementFetcher:
    """
    公司公告获取器
    重点关注：业绩预告、重大事项、分红预案
    """

    IMPORTANT_TYPES = [
        '业绩预告', '业绩快报', '年度报告', '半年度报告', '季度报告',
        '分红', '送转', '增发', '配股', '重大合同', '重大诉讼',
        '股权激励', '高管变动', '业绩修正'
    ]

    def fetch_announcements(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取公司公告

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)，默认30天前
            end_date: 结束日期 (YYYY-MM-DD)，默认今天

        Returns:
            公告列表
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        logger.info(f"获取 {symbol} 从 {start_date} 到 {end_date} 的公告")

        # 尝试从AKShare获取
        announcements = self._fetch_from_akshare(symbol, start_date, end_date)

        if not announcements:
            logger.warning(f"未能获取 {symbol} 的公告数据")
            return []

        # 筛选重要公告
        important = self.filter_important_announcements(announcements)
        logger.info(f"共获取 {len(announcements)} 条公告，其中重要公告 {len(important)} 条")

        return important

    def _fetch_from_akshare(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """从AKShare获取公告"""
        try:
            import akshare as ak  # type: ignore

            # 使用东方财富公告接口
            df = ak.stock_notice_report(symbol=symbol)

            if df is None or df.empty:
                return []

            # 转换为字典列表
            announcements = []
            for _, row in df.iterrows():
                announcement = {
                    'date': str(row.get('公告日期', '')),
                    'title': str(row.get('公告标题', '')),
                    'type': str(row.get('公告类型', '')),
                    'url': str(row.get('公告链接', '')),
                    'symbol': symbol,
                    'source': 'akshare',
                    'fetched_at': datetime.now().isoformat()
                }

                # 日期过滤
                ann_date = announcement['date']
                if start_date <= ann_date <= end_date:
                    announcements.append(announcement)

            return announcements

        except Exception as e:
            logger.error(f"从AKShare获取公告失败: {e}")
            return []

    def filter_important_announcements(
        self,
        announcements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        筛选重要公告

        根据标题和类型判断是否为重要公告
        """
        important = []

        for ann in announcements:
            title = ann.get('title', '')
            ann_type = ann.get('type', '')

            # 检查是否包含重要关键词
            is_important = any(
                keyword in title or keyword in ann_type
                for keyword in self.IMPORTANT_TYPES
            )

            if is_important:
                ann['importance'] = 'high'
                important.append(ann)

        # 按日期倒序排列
        important.sort(key=lambda x: x.get('date', ''), reverse=True)

        return important

    def extract_earnings_forecast(
        self,
        announcements: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        从公告中提取业绩预告信息
        """
        for ann in announcements:
            title = ann.get('title', '')
            if '业绩预告' in title or '业绩快报' in title:
                return {
                    'date': ann['date'],
                    'title': title,
                    'url': ann.get('url', ''),
                    'type': '业绩预告'
                }

        return None


if __name__ == "__main__":
    # 测试
    fetcher = AnnouncementFetcher()
    announcements = fetcher.fetch_announcements("600519")

    print(f"✅ 获取到 {len(announcements)} 条重要公告:")
    for ann in announcements[:5]:  # 只显示前5条
        print(f"  - {ann['date']} {ann['title']}")
