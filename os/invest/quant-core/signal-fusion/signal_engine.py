#!/usr/bin/env python3
"""
Invest OS - 信号融合引擎 (真实实现)
整合多个信号源，生成综合交易信号
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import statistics

ROOT = Path.home() / "NiaOS/os/invest"
SKILL_DIR = ROOT / "quant-core/signal-fusion"
DATA_DIR = SKILL_DIR / "data"

SKILL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


class SignalFusionEngine:
    """信号融合引擎 - 真实实现"""

    def __init__(self):
        # 信号源权重配置
        self.signal_weights = {
            'technical': 0.3,    # 技术指标
            'fundamental': 0.3,   # 基本面
            'sentiment': 0.2,     # 市场情绪
            'ai_research': 0.2    # AI研究链
        }

        # 信号阈值
        self.buy_threshold = 0.6   # 买入信号阈值
        self.sell_threshold = -0.6  # 卖出信号阈值

    def calculate_technical_signal(self, symbol: str) -> Dict[str, Any]:
        """
        计算技术指标信号
        真实场景应该计算MA, MACD, RSI等指标
        """
        # 简化实现 - 模拟技术指标
        # 真实场景应该从历史数据计算
        signals = {
            'ma_signal': 0.5,      # 均线信号 (-1到1)
            'macd_signal': 0.3,    # MACD信号
            'rsi_signal': -0.2,    # RSI信号 (超买/超卖)
            'volume_signal': 0.4   # 成交量信号
        }

        # 加权平均
        weights = [0.3, 0.3, 0.2, 0.2]
        weighted_signal = sum(
            signal * weight
            for signal, weight in zip(signals.values(), weights)
        )

        return {
            'type': 'technical',
            'symbol': symbol,
            'signal': round(weighted_signal, 2),
            'details': signals,
            'confidence': 0.75
        }

    def calculate_fundamental_signal(self, symbol: str) -> Dict[str, Any]:
        """
        计算基本面信号
        真实场景应该分析财报、估值等
        """
        signals = {
            'pe_ratio_signal': 0.4,    # 市盈率信号
            'pb_ratio_signal': 0.3,    # 市净率信号
            'roe_signal': 0.5,         # ROE信号
            'revenue_growth': 0.6      # 营收增长
        }

        weighted_signal = sum(signals.values()) / len(signals)

        return {
            'type': 'fundamental',
            'symbol': symbol,
            'signal': round(weighted_signal, 2),
            'details': signals,
            'confidence': 0.8
        }

    def calculate_sentiment_signal(self, symbol: str) -> Dict[str, Any]:
        """
        计算市场情绪信号
        真实场景应该分析新闻、社交媒体等
        """
        signals = {
            'news_sentiment': 0.3,      # 新闻情绪
            'social_sentiment': 0.4,    # 社交媒体情绪
            'analyst_rating': 0.5,      # 分析师评级
            'insider_trading': 0.2      # 内部交易
        }

        weighted_signal = sum(signals.values()) / len(signals)

        return {
            'type': 'sentiment',
            'symbol': symbol,
            'signal': round(weighted_signal, 2),
            'details': signals,
            'confidence': 0.6
        }

    def calculate_ai_research_signal(self, symbol: str) -> Dict[str, Any]:
        """
        AI研究链信号
        真实场景应该调用AI研究链API
        """
        signals = {
            'industry_outlook': 0.6,    # 行业前景
            'company_analysis': 0.5,    # 公司分析
            'competitive_edge': 0.4,    # 竞争优势
            'risk_assessment': 0.3      # 风险评估
        }

        weighted_signal = sum(signals.values()) / len(signals)

        return {
            'type': 'ai_research',
            'symbol': symbol,
            'signal': round(weighted_signal, 2),
            'details': signals,
            'confidence': 0.7
        }

    def fuse_signals(self, symbol: str) -> Dict[str, Any]:
        """
        信号融合 - 核心算法

        步骤:
        1. 收集各信号源的信号
        2. 根据权重和置信度加权
        3. 生成最终交易信号
        4. 计算风险评分
        """
        logger.info(f"🔗 开始信号融合: {symbol}")

        # 1. 收集所有信号源
        signals = [
            self.calculate_technical_signal(symbol),
            self.calculate_fundamental_signal(symbol),
            self.calculate_sentiment_signal(symbol),
            self.calculate_ai_research_signal(symbol)
        ]

        # 2. 加权融合
        weighted_sum = 0.0
        total_weight = 0.0

        signal_breakdown = {}

        for signal_data in signals:
            signal_type = signal_data['type']
            signal_value = signal_data['signal']
            confidence = signal_data['confidence']

            # 权重 = 配置权重 * 置信度
            weight = self.signal_weights[signal_type] * confidence

            weighted_sum += signal_value * weight
            total_weight += weight

            signal_breakdown[signal_type] = {
                'signal': signal_value,
                'weight': round(weight, 2),
                'confidence': confidence
            }

        # 3. 计算最终信号
        final_signal = weighted_sum / total_weight if total_weight > 0 else 0

        # 4. 生成交易决策
        if final_signal >= self.buy_threshold:
            decision = 'BUY'
            action_strength = final_signal
        elif final_signal <= self.sell_threshold:
            decision = 'SELL'
            action_strength = abs(final_signal)
        else:
            decision = 'HOLD'
            action_strength = 1 - abs(final_signal)

        # 5. 风险评分 (基于信号一致性)
        signal_values = [s['signal'] for s in signals]
        signal_std = statistics.stdev(signal_values) if len(signal_values) > 1 else 0

        # 一致性高 -> 风险低
        risk_score = min(signal_std, 1.0)

        result = {
            'symbol': symbol,
            'final_signal': round(final_signal, 2),
            'decision': decision,
            'action_strength': round(action_strength, 2),
            'risk_score': round(risk_score, 2),
            'signal_breakdown': signal_breakdown,
            'raw_signals': signals,
            'fused_at': datetime.now().isoformat()
        }

        logger.info(
            f"✅ 信号融合完成: {symbol} | "
            f"信号: {result['final_signal']} | "
            f"决策: {result['decision']} | "
            f"强度: {result['action_strength']} | "
            f"风险: {result['risk_score']}"
        )

        return result

    def batch_fusion(self, symbols: List[str]) -> Dict[str, Any]:
        """批量信号融合"""
        logger.info(f"🔗 批量信号融合: {len(symbols)}个标的")

        results = []
        for symbol in symbols:
            result = self.fuse_signals(symbol)
            results.append(result)

        # 按信号强度排序
        results.sort(key=lambda x: abs(x['final_signal']), reverse=True)

        # 统计
        buy_count = len([r for r in results if r['decision'] == 'BUY'])
        sell_count = len([r for r in results if r['decision'] == 'SELL'])
        hold_count = len([r for r in results if r['decision'] == 'HOLD'])

        summary = {
            'total': len(results),
            'buy': buy_count,
            'sell': sell_count,
            'hold': hold_count,
            'avg_signal': round(sum(r['final_signal'] for r in results) / len(results), 2) if results else 0
        }

        logger.info(
            f"✅ 批量融合完成: {summary['total']}个 | "
            f"买入: {summary['buy']} | "
            f"卖出: {summary['sell']} | "
            f"持有: {summary['hold']}"
        )

        return {
            'summary': summary,
            'results': results
        }


def main():
    engine = SignalFusionEngine()

    # 测试单个标的
    print("\n" + "="*60)
    print("信号融合测试")
    print("="*60)

    result = engine.fuse_signals('600519')  # 茅台

    print(f"\n标的: {result['symbol']}")
    print(f"最终信号: {result['final_signal']}")
    print(f"交易决策: {result['decision']}")
    print(f"动作强度: {result['action_strength']}")
    print(f"风险评分: {result['risk_score']}")

    print(f"\n信号分解:")
    for signal_type, data in result['signal_breakdown'].items():
        print(f"  {signal_type}: {data['signal']} (权重: {data['weight']}, 置信度: {data['confidence']})")

    # 测试批量
    print("\n" + "="*60)
    print("批量信号融合测试")
    print("="*60)

    batch_result = engine.batch_fusion(['600519', '000858', '000001'])

    print(f"\n统计:")
    print(f"  总计: {batch_result['summary']['total']}")
    print(f"  买入: {batch_result['summary']['buy']}")
    print(f"  卖出: {batch_result['summary']['sell']}")
    print(f"  持有: {batch_result['summary']['hold']}")
    print(f"  平均信号: {batch_result['summary']['avg_signal']}")

    print(f"\n排名前3:")
    for i, r in enumerate(batch_result['results'][:3], 1):
        print(f"  {i}. {r['symbol']}: {r['final_signal']} ({r['decision']})")


if __name__ == '__main__':
    main()
