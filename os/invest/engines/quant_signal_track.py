#!/usr/bin/env python3
"""
Invest OS - Quantitative Signal Track
投资OS - 数据客观技术线（量化信号）

技术指标 → 因子融合 → 量化信号 → 交易建议

Author: Nia OS Team
Version: 1.0
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


@dataclass
class TechnicalIndicator:
    """技术指标"""
    indicator_name: str
    value: float
    signal: SignalType
    weight: float  # 权重


@dataclass
class FactorScore:
    """因子评分"""
    factor_name: str  # momentum, value, quality, growth, volatility
    score: float  # -100 to 100
    percentile: float  # 0-100，在全市场的分位数
    signal: SignalType


@dataclass
class QuantSignal:
    """量化信号"""
    symbol: str
    date: str
    technical_score: float  # 技术面得分 -100 to 100
    factor_score: float  # 因子得分 -100 to 100
    composite_score: float  # 综合得分
    signal: SignalType
    confidence: float  # 0-1
    indicators: List[TechnicalIndicator] = field(default_factory=list)
    factors: List[FactorScore] = field(default_factory=list)
    created_at: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    strategy_name: str
    start_date: str
    end_date: str
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: int


class QuantSignalTrack:
    """量化信号线"""

    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.signals_file = self.base_path / "signals.json"
        self.backtest_file = self.base_path / "backtest_results.json"

        self.signals: Dict[str, List[QuantSignal]] = {}  # symbol -> [signals]
        self.backtests: List[BacktestResult] = []

        self._load_all()

    def _load_all(self):
        """加载所有数据"""
        if self.signals_file.exists():
            with open(self.signals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for symbol, signal_list in data.items():
                    self.signals[symbol] = []
                    for signal_data in signal_list:
                        signal_data['signal'] = SignalType(signal_data['signal'])
                        for ind in signal_data.get('indicators', []):
                            ind['signal'] = SignalType(ind['signal'])
                        for fac in signal_data.get('factors', []):
                            fac['signal'] = SignalType(fac['signal'])
                        self.signals[symbol].append(QuantSignal(**signal_data))

        if self.backtest_file.exists():
            with open(self.backtest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.backtests = [BacktestResult(**bt) for bt in data]

    def _save_all(self):
        """保存所有数据"""
        # 保存信号
        with open(self.signals_file, 'w', encoding='utf-8') as f:
            json.dump({
                symbol: [
                    {
                        'symbol': sig.symbol,
                        'date': sig.date,
                        'technical_score': sig.technical_score,
                        'factor_score': sig.factor_score,
                        'composite_score': sig.composite_score,
                        'signal': sig.signal.value,
                        'confidence': sig.confidence,
                        'indicators': [
                            {
                                'indicator_name': ind.indicator_name,
                                'value': ind.value,
                                'signal': ind.signal.value,
                                'weight': ind.weight
                            }
                            for ind in sig.indicators
                        ],
                        'factors': [
                            {
                                'factor_name': fac.factor_name,
                                'score': fac.score,
                                'percentile': fac.percentile,
                                'signal': fac.signal.value
                            }
                            for fac in sig.factors
                        ],
                        'created_at': sig.created_at
                    }
                    for sig in signals
                ]
                for symbol, signals in self.signals.items()
            }, f, indent=2, ensure_ascii=False)

        # 保存回测结果
        with open(self.backtest_file, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    'strategy_name': bt.strategy_name,
                    'start_date': bt.start_date,
                    'end_date': bt.end_date,
                    'total_return': bt.total_return,
                    'annual_return': bt.annual_return,
                    'sharpe_ratio': bt.sharpe_ratio,
                    'max_drawdown': bt.max_drawdown,
                    'win_rate': bt.win_rate,
                    'trades': bt.trades
                }
                for bt in self.backtests
            ], f, indent=2, ensure_ascii=False)

    def calculate_technical_score(
        self,
        symbol: str,
        ma_20: float,
        ma_50: float,
        ma_200: float,
        rsi: float,
        macd: float,
        volume_ratio: float,
        current_price: float
    ) -> Tuple[float, List[TechnicalIndicator]]:
        """计算技术面得分"""
        indicators = []

        # MA趋势
        ma_score = 0
        if current_price > ma_20 > ma_50 > ma_200:
            ma_score = 30
            ma_signal = SignalType.STRONG_BUY
        elif current_price > ma_50 > ma_200:
            ma_score = 15
            ma_signal = SignalType.BUY
        elif current_price < ma_20 < ma_50 < ma_200:
            ma_score = -30
            ma_signal = SignalType.STRONG_SELL
        else:
            ma_score = 0
            ma_signal = SignalType.HOLD

        indicators.append(TechnicalIndicator("MA_Trend", ma_score, ma_signal, 0.3))

        # RSI
        rsi_score: float = 0.0
        if rsi > 70:
            rsi_score = -20.0
            rsi_signal = SignalType.SELL
        elif rsi < 30:
            rsi_score = 20.0
            rsi_signal = SignalType.BUY
        else:
            rsi_score = (50 - rsi) * 0.4
            rsi_signal = SignalType.HOLD

        indicators.append(TechnicalIndicator("RSI", rsi, rsi_signal, 0.25))

        # MACD
        macd_score = macd * 10
        if macd > 0:
            macd_signal = SignalType.BUY
        elif macd < 0:
            macd_signal = SignalType.SELL
        else:
            macd_signal = SignalType.HOLD

        indicators.append(TechnicalIndicator("MACD", macd, macd_signal, 0.25))

        # 成交量
        vol_score = 0
        if volume_ratio > 2:
            vol_score = 20
            vol_signal = SignalType.BUY
        elif volume_ratio < 0.5:
            vol_score = -10
            vol_signal = SignalType.SELL
        else:
            vol_score = 0
            vol_signal = SignalType.HOLD

        indicators.append(TechnicalIndicator("Volume", volume_ratio, vol_signal, 0.2))

        # 加权总分
        total_score = sum(ind.value * ind.weight for ind in indicators if ind.indicator_name != "RSI")
        total_score += rsi_score * 0.25

        return total_score, indicators

    def calculate_factor_score(
        self,
        symbol: str,
        momentum_percentile: float,
        value_percentile: float,
        quality_percentile: float,
        growth_percentile: float,
        volatility_percentile: float
    ) -> Tuple[float, List[FactorScore]]:
        """计算因子得分"""
        factors = []

        # 转换分位数为得分 (-50 to 50)
        def percentile_to_score(percentile: float) -> float:
            return (percentile - 50)

        # 动量因子
        momentum_score = percentile_to_score(momentum_percentile)
        factors.append(FactorScore(
            "momentum",
            momentum_score,
            momentum_percentile,
            SignalType.BUY if momentum_score > 20 else SignalType.SELL if momentum_score < -20 else SignalType.HOLD
        ))

        # 价值因子
        value_score = percentile_to_score(value_percentile)
        factors.append(FactorScore(
            "value",
            value_score,
            value_percentile,
            SignalType.BUY if value_score > 20 else SignalType.SELL if value_score < -20 else SignalType.HOLD
        ))

        # 质量因子
        quality_score = percentile_to_score(quality_percentile)
        factors.append(FactorScore(
            "quality",
            quality_score,
            quality_percentile,
            SignalType.BUY if quality_score > 20 else SignalType.SELL if quality_score < -20 else SignalType.HOLD
        ))

        # 成长因子
        growth_score = percentile_to_score(growth_percentile)
        factors.append(FactorScore(
            "growth",
            growth_score,
            growth_percentile,
            SignalType.BUY if growth_score > 20 else SignalType.SELL if growth_score < -20 else SignalType.HOLD
        ))

        # 波动率因子（低波动为正）
        volatility_score = -percentile_to_score(volatility_percentile)
        factors.append(FactorScore(
            "volatility",
            volatility_score,
            volatility_percentile,
            SignalType.BUY if volatility_score > 20 else SignalType.SELL if volatility_score < -20 else SignalType.HOLD
        ))

        # 因子权重
        weights = {'momentum': 0.3, 'value': 0.25, 'quality': 0.25, 'growth': 0.15, 'volatility': 0.05}

        total_score = sum(fac.score * weights[fac.factor_name] for fac in factors)

        return total_score, factors

    def generate_signal(
        self,
        symbol: str,
        technical_indicators: Dict,
        factor_data: Dict
    ) -> QuantSignal:
        """生成综合信号"""
        # 计算技术面得分
        tech_score, indicators = self.calculate_technical_score(
            symbol,
            technical_indicators.get('ma_20', 0),
            technical_indicators.get('ma_50', 0),
            technical_indicators.get('ma_200', 0),
            technical_indicators.get('rsi', 50),
            technical_indicators.get('macd', 0),
            technical_indicators.get('volume_ratio', 1),
            technical_indicators.get('current_price', 0)
        )

        # 计算因子得分
        factor_score, factors = self.calculate_factor_score(
            symbol,
            factor_data.get('momentum_percentile', 50),
            factor_data.get('value_percentile', 50),
            factor_data.get('quality_percentile', 50),
            factor_data.get('growth_percentile', 50),
            factor_data.get('volatility_percentile', 50)
        )

        # 综合得分（技术面40% + 因子面60%）
        composite_score = tech_score * 0.4 + factor_score * 0.6

        # 生成信号
        if composite_score > 30:
            signal = SignalType.STRONG_BUY
            confidence = min((composite_score - 30) / 20, 1.0)
        elif composite_score > 10:
            signal = SignalType.BUY
            confidence = (composite_score - 10) / 20
        elif composite_score < -30:
            signal = SignalType.STRONG_SELL
            confidence = min((-composite_score - 30) / 20, 1.0)
        elif composite_score < -10:
            signal = SignalType.SELL
            confidence = (-composite_score - 10) / 20
        else:
            signal = SignalType.HOLD
            confidence = 1 - abs(composite_score) / 10

        quant_signal = QuantSignal(
            symbol=symbol,
            date=datetime.now().strftime("%Y-%m-%d"),
            technical_score=tech_score,
            factor_score=factor_score,
            composite_score=composite_score,
            signal=signal,
            confidence=confidence,
            indicators=indicators,
            factors=factors,
            created_at=datetime.now().isoformat()
        )

        # 保存信号
        if symbol not in self.signals:
            self.signals[symbol] = []
        self.signals[symbol].append(quant_signal)
        self._save_all()

        return quant_signal

    def get_latest_signal(self, symbol: str) -> Optional[QuantSignal]:
        """获取最新信号"""
        if symbol not in self.signals or not self.signals[symbol]:
            return None
        return self.signals[symbol][-1]

    def get_buy_signals(self, min_confidence: float = 0.6) -> List[QuantSignal]:
        """获取所有买入信号"""
        buy_signals = []
        for symbol_signals in self.signals.values():
            if symbol_signals:
                latest = symbol_signals[-1]
                if latest.signal in [SignalType.BUY, SignalType.STRONG_BUY] and latest.confidence >= min_confidence:
                    buy_signals.append(latest)

        return sorted(buy_signals, key=lambda x: x.composite_score, reverse=True)


def create_quant_signal_track(base_path: Optional[str] = None) -> QuantSignalTrack:
    """创建量化信号线"""
    if base_path is None:
        default_path = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/02_quant_signals"
        return QuantSignalTrack(default_path)
    return QuantSignalTrack(Path(base_path))
