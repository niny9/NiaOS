"""
研报获取器
从东方财富获取券商研报
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResearchReportFetcher:
    """
    券商研报获取器
    免费源：东方财富
    """

    def fetch_research_reports(
        self,
        symbol: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取券商研报

        Args:
            symbol: 股票代码
            days: 最近N天，默认30天

        Returns:
            研报列表
        """
        logger.info(f"获取 {symbol} 最近 {days} 天的研报")

        reports = self._fetch_from_akshare(symbol)

        if not reports:
            logger.warning(f"未能获取 {symbol} 的研报数据")
            return []

        # 过滤最近N天
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        recent_reports = [r for r in reports if r.get('date', '') >= cutoff_date]

        logger.info(f"共获取 {len(reports)} 份研报，最近{days}天有 {len(recent_reports)} 份")

        return recent_reports

    def _fetch_from_akshare(self, symbol: str) -> List[Dict[str, Any]]:
        """从AKShare获取研报"""
        try:
            import akshare as ak  # type: ignore

            # 使用东方财富研报接口
            df = ak.stock_research_report_em(symbol=symbol)

            if df is None or df.empty:
                return []

            reports = []
            for _, row in df.iterrows():
                report = {
                    'date': str(row.get('日期', '')),
                    'title': str(row.get('标题', '')),
                    'institution': str(row.get('研究机构', '')),
                    'analyst': str(row.get('分析师', '')),
                    'rating': str(row.get('投资评级', '')),
                    'url': str(row.get('相关链接', '')),
                    'symbol': symbol,
                    'source': 'akshare',
                    'fetched_at': datetime.now().isoformat()
                }
                reports.append(report)

            return reports

        except Exception as e:
            logger.error(f"从AKShare获取研报失败: {e}")
            return []

    def extract_rating_changes(
        self,
        reports: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取评级变化

        识别买入、增持、中性、减持、卖出等评级
        """
        rating_changes = []

        # 定义评级权重（用于判断升级/降级）
        rating_weights = {
            '买入': 5,
            '强烈推荐': 5,
            '增持': 4,
            '推荐': 4,
            '中性': 3,
            '观望': 3,
            '减持': 2,
            '卖出': 1
        }

        for report in reports:
            rating = report.get('rating', '')

            # 匹配评级
            matched_rating = None
            weight = 0
            for key, val in rating_weights.items():
                if key in rating:
                    matched_rating = key
                    weight = val
                    break

            if matched_rating:
                rating_changes.append({
                    'date': report['date'],
                    'institution': report['institution'],
                    'rating': matched_rating,
                    'weight': weight,
                    'title': report['title']
                })

        # 按日期排序
        rating_changes.sort(key=lambda x: x['date'], reverse=True)

        return rating_changes

    def get_consensus_rating(
        self,
        reports: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        计算一致性评级

        Returns:
            平均评级和分布
        """
        if not reports:
            return None

        rating_changes = self.extract_rating_changes(reports)

        if not rating_changes:
            return None

        # 计算平均权重
        total_weight = sum(r['weight'] for r in rating_changes)
        avg_weight = total_weight / len(rating_changes)

        # 统计评级分布
        rating_dist: Dict[str, int] = {}
        for r in rating_changes:
            rating = r['rating']
            rating_dist[rating] = rating_dist.get(rating, 0) + 1

        # 判断一致性评级
        if avg_weight >= 4.5:
            consensus = '买入'
        elif avg_weight >= 3.5:
            consensus = '增持'
        elif avg_weight >= 2.5:
            consensus = '中性'
        elif avg_weight >= 1.5:
            consensus = '减持'
        else:
            consensus = '卖出'

        return {
            'consensus': consensus,
            'avg_weight': avg_weight,
            'distribution': rating_dist,
            'total_reports': len(rating_changes)
        }


if __name__ == "__main__":
    # 测试
    fetcher = ResearchReportFetcher()
    reports = fetcher.fetch_research_reports("600519", days=90)

    if reports:
        print(f"✅ 获取到 {len(reports)} 份研报:")
        for r in reports[:5]:
            print(f"  - {r['date']} {r['institution']}: {r['rating']}")

        # 一致性评级
        consensus = fetcher.get_consensus_rating(reports)
        if consensus:
            print(f"\n一致性评级: {consensus['consensus']} (权重: {consensus['avg_weight']:.2f})")
            print(f"评级分布: {consensus['distribution']}")
    else:
        print("❌ 研报获取失败")
