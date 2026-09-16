"""
VectorBT回测引擎
使用vectorbt进行快速矢量化回测
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class VectorbtBacktest:
    """
    使用vectorbt进行快速回测
    优势：矢量化计算，速度快，适合参数优化
    """

    def __init__(self):
        try:
            import vectorbt as vbt  # type: ignore
            self.vbt = vbt
            self.available = True
            logger.info("VectorBT已加载")
        except ImportError:
            self.available = False
            logger.warning("VectorBT未安装，请运行: pip install vectorbt")

    def backtest_strategy(
        self,
        prices: pd.DataFrame,
        signals: Dict[str, pd.Series],
        initial_cash: float = 100000.0,
        commission: float = 0.0003
    ) -> Optional[Dict[str, Any]]:
        """
        回测交易策略

        Args:
            prices: 价格数据，包含close列
            signals: 信号字典，包含buy和sell的布尔序列
            initial_cash: 初始资金
            commission: 手续费率

        Returns:
            回测结果统计
        """
        if not self.available:
            logger.error("VectorBT不可用")
            return None

        try:
            # 创建投资组合
            portfolio = self.vbt.Portfolio.from_signals(
                close=prices['close'],
                entries=signals['buy'],
                exits=signals['sell'],
                init_cash=initial_cash,
                fees=commission
            )

            # 获取统计数据
            stats = portfolio.stats()

            # 转换为字典
            result = {
                'total_return': float(stats.get('Total Return [%]', 0)),
                'sharpe_ratio': float(stats.get('Sharpe Ratio', 0)),
                'max_drawdown': float(stats.get('Max Drawdown [%]', 0)),
                'win_rate': float(stats.get('Win Rate [%]', 0)),
                'total_trades': int(stats.get('Total Trades', 0)),
                'final_value': float(stats.get('End Value', 0)),
                'benchmark': 'buy_and_hold'
            }

            logger.info(f"回测完成: 总收益 {result['total_return']:.2f}%, 夏普比率 {result['sharpe_ratio']:.2f}")

            return result

        except Exception as e:
            logger.error(f"回测失败: {e}")
            return None

    def optimize_parameters(
        self,
        prices: pd.DataFrame,
        param_grid: Dict[str, list],
        strategy_func: Any
    ) -> Optional[Dict[str, Any]]:
        """
        参数优化

        Args:
            prices: 价格数据
            param_grid: 参数网格，如 {'short_window': [5, 10, 20], 'long_window': [20, 30, 60]}
            strategy_func: 策略函数，接受参数并返回信号

        Returns:
            最优参数和结果
        """
        if not self.available:
            logger.error("VectorBT不可用")
            return None

        try:
            from itertools import product

            best_result = None
            best_params = None
            best_return = float('-inf')

            # 生成参数组合
            param_names = list(param_grid.keys())
            param_values = list(param_grid.values())

            for values in product(*param_values):
                params = dict(zip(param_names, values))

                # 生成信号
                signals = strategy_func(prices, **params)

                # 回测
                result = self.backtest_strategy(prices, signals)

                if result and result['total_return'] > best_return:
                    best_return = result['total_return']
                    best_params = params
                    best_result = result

            logger.info(f"最优参数: {best_params}, 收益: {best_return:.2f}%")

            return {
                'best_params': best_params,
                'best_result': best_result
            }

        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            return None

    def generate_simple_ma_signals(
        self,
        prices: pd.DataFrame,
        short_window: int = 5,
        long_window: int = 20
    ) -> Dict[str, pd.Series]:
        """
        生成简单均线交叉信号（示例）

        Args:
            prices: 价格数据
            short_window: 短期均线窗口
            long_window: 长期均线窗口

        Returns:
            买入和卖出信号
        """
        short_ma = prices['close'].rolling(window=short_window).mean()
        long_ma = prices['close'].rolling(window=long_window).mean()

        # 金叉买入，死叉卖出
        buy_signal = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        sell_signal = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

        return {
            'buy': buy_signal,
            'sell': sell_signal
        }


if __name__ == "__main__":
    # 示例：生成模拟数据并回测
    import pandas as pd
    import numpy as np

    # 生成随机价格数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    prices = pd.DataFrame({
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    }, index=dates)

    # 创建回测引擎
    backtest = VectorbtBacktest()

    if backtest.available:
        # 生成信号
        signals = backtest.generate_simple_ma_signals(prices, short_window=5, long_window=20)

        # 回测
        result = backtest.backtest_strategy(prices, signals)

        if result:
            print("回测结果:")
            print(f"  总收益: {result['total_return']:.2f}%")
            print(f"  夏普比率: {result['sharpe_ratio']:.2f}")
            print(f"  最大回撤: {result['max_drawdown']:.2f}%")
            print(f"  胜率: {result['win_rate']:.2f}%")
            print(f"  总交易次数: {result['total_trades']}")
    else:
        print("VectorBT未安装，跳过回测测试")
