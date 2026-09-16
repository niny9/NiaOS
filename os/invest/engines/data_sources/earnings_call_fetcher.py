"""
电话会议记录获取器
从巨潮资讯获取投资者关系活动记录
"""
import logging
from typing import Dict, Optional, List, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class EarningsCallFetcher:
    """
    电话会议记录获取器
    来源：巨潮资讯/手动上传
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or "/Users/niny/NiaOS/os/invest/data/reconciliation/calls"
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def fetch_earnings_call_transcript(
        self,
        symbol: str,
        quarter: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取电话会议文字记录

        Args:
            symbol: 股票代码
            quarter: 季度（如 2024Q3）

        Returns:
            会议记录和关键信息
        """
        logger.info(f"获取 {symbol} {quarter} 电话会议记录")

        # 尝试从AKShare获取投资者关系活动
        data = self._fetch_from_akshare(symbol)
        if data:
            return data

        # 尝试从本地文件获取
        data = self._fetch_from_local(symbol, quarter)
        if data:
            return data

        logger.warning(
            f"无法获取 {symbol} {quarter} 电话会议记录，"
            f"请手动上传到: {self.base_path}/{symbol}_{quarter}.txt"
        )
        return None

    def _fetch_from_akshare(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从AKShare获取投资者关系活动"""
        try:
            import akshare as ak  # type: ignore

            # 获取投资者关系信息
            df = ak.stock_irm_cninfo(symbol=symbol)

            if df is None or df.empty:
                return None

            # 取最新一条记录
            latest = df.iloc[0]

            return {
                'symbol': symbol,
                'date': str(latest.get('日期', '')),
                'type': str(latest.get('活动类型', '')),
                'participants': str(latest.get('参与人员', '')),
                'content': str(latest.get('主要内容', '')),
                'source': 'akshare',
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"从AKShare获取投资者关系活动失败: {e}")
            return None

    def _fetch_from_local(
        self,
        symbol: str,
        quarter: str
    ) -> Optional[Dict[str, Any]]:
        """从本地文件获取"""
        filepath = Path(self.base_path) / f"{symbol}_{quarter}.txt"

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'symbol': symbol,
                'quarter': quarter,
                'content': content,
                'source': 'local_file',
                'fetched_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"读取本地文件失败: {e}")
            return None

    def extract_management_statements(
        self,
        transcript: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        从会议记录中提取管理层关键表述

        识别承诺、预期、计划等关键语句
        """
        content = transcript.get('content', '')

        if not content:
            return []

        # 关键词列表（承诺类语句）
        keywords = [
            '计划', '预计', '预期', '将会', '目标', '预测',
            '预估', '展望', '打算', '准备', '即将', '力争'
        ]

        statements = []

        # 按句子分割
        sentences = content.replace('。', '。\n').split('\n')

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 检查是否包含关键词
            for keyword in keywords:
                if keyword in sentence:
                    statements.append({
                        'statement': sentence,
                        'keyword': keyword,
                        'type': 'commitment'
                    })
                    break

        logger.info(f"提取到 {len(statements)} 条管理层表述")
        return statements

    def save_manual_transcript(
        self,
        symbol: str,
        quarter: str,
        content: str
    ) -> bool:
        """
        保存手动输入的会议记录
        """
        filepath = Path(self.base_path) / f"{symbol}_{quarter}.txt"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"会议记录已保存: {filepath}")
            return True

        except Exception as e:
            logger.error(f"保存会议记录失败: {e}")
            return False


if __name__ == "__main__":
    # 测试
    fetcher = EarningsCallFetcher()
    transcript = fetcher.fetch_earnings_call_transcript("600519", "2024Q2")

    if transcript:
        print(f"✅ 获取到电话会议记录:")
        print(f"  日期: {transcript.get('date', 'N/A')}")
        print(f"  类型: {transcript.get('type', 'N/A')}")
        print(f"  来源: {transcript.get('source', 'N/A')}")

        # 提取管理层表述
        statements = fetcher.extract_management_statements(transcript)
        print(f"\n提取到 {len(statements)} 条管理层表述")
        for stmt in statements[:3]:
            print(f"  - {stmt['statement'][:50]}...")
    else:
        print("❌ 电话会议记录获取失败")
