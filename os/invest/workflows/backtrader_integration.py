#!/usr/bin/env python3
"""
Backtrader Integration - Backtrader回测框架集成
使用Backtrader进行策略回测
"""

import json
import argparse
from datetime import datetime


def install_backtrader():
    """安装Backtrader"""
    print("💡 Backtrader安装指南:")
    print("   pip install backtrader")
    print("   pip install backtrader[plotting]")


def create_backtrader_strategy() -> str:
    """创建Backtrader策略模板"""

    strategy_code = '''
import backtrader as bt

class MyStrategy(bt.Strategy):
    """示例策略"""

    params = (
        ('maperiod', 20),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # 添加移动平均线指标
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod
        )

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                print(f'买入执行, 价格: {order.executed.price:.2f}')
            elif order.issell():
                print(f'卖出执行, 价格: {order.executed.price:.2f}')

        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            # 没有持仓，考虑买入
            if self.dataclose[0] > self.sma[0]:
                self.order = self.buy()
        else:
            # 有持仓，考虑卖出
            if self.dataclose[0] < self.sma[0]:
                self.order = self.sell()
'''

    return strategy_code


def run_backtest_example():
    """运行回测示例"""

    print("📊 Backtrader回测示例:\n")

    example_code = '''
import backtrader as bt

# 创建Cerebro引擎
cerebro = bt.Cerebro()

# 添加策略
cerebro.addstrategy(MyStrategy)

# 加载数据
data = bt.feeds.YahooFinanceData(
    dataname='AAPL',
    fromdate=datetime(2020, 1, 1),
    todate=datetime(2021, 1, 1)
)
cerebro.adddata(data)

# 设置初始资金
cerebro.broker.setcash(100000.0)

# 设置手续费
cerebro.broker.setcommission(commission=0.001)

# 运行回测
print('初始资金: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('最终资金: %.2f' % cerebro.broker.getvalue())

# 绘图
cerebro.plot()
'''

    print(example_code)


def main():
    parser = argparse.ArgumentParser(description='Backtrader Integration - Backtrader集成')
    parser.add_argument('--action', default='guide',
                        choices=['guide', 'template', 'example'])

    args = parser.parse_args()

    print("🚀 Backtrader Integration 启动...")
    print()

    if args.action == 'guide':
        print("📖 Backtrader使用指南\n")
        install_backtrader()

        print("\n✨ 主要功能:")
        print("  • 策略开发")
        print("  • 历史回测")
        print("  • 性能分析")
        print("  • 可视化图表")

        print("\n📝 快速开始:")
        print("  1. 安装: pip install backtrader")
        print("  2. 创建策略: python3 backtrader_integration.py --action template")
        print("  3. 运行回测: python3 backtrader_integration.py --action example")

    elif args.action == 'template':
        print("📝 策略模板:\n")
        template = create_backtrader_strategy()
        print(template)

        # 保存模板
        template_file = '/Users/niny/NiaOS/os/invest/strategies/backtrader_template.py'
        import os
        os.makedirs(os.path.dirname(template_file), exist_ok=True)

        with open(template_file, 'w') as f:
            f.write(template)

        print(f"\n✅ 模板已保存: {template_file}")

    elif args.action == 'example':
        run_backtest_example()

    print("\n✅ Backtrader Integration 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
