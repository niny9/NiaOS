#!/usr/bin/env python3
"""
Paper Trading Simulator - 模拟交易系统
完整的Paper Trading模拟器
"""

import json
import argparse
from typing import Dict, List, Any
from datetime import datetime


class PaperTradingSimulator:
    """模拟交易器"""

    def __init__(self, initial_capital: float = 100000):
        self.capital = initial_capital
        self.positions = {}
        self.trade_history = []
        self.cash = initial_capital

    def place_order(self, symbol: str, action: str, quantity: int, price: float) -> Dict[str, Any]:
        """下单"""

        order = {
            'order_id': f"order_{len(self.trade_history)+1}",
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }

        # 执行订单
        if action == 'BUY':
            cost = quantity * price
            if self.cash >= cost:
                self.cash -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                order['status'] = 'filled'
                print(f"✅ 买入 {symbol} {quantity}股 @ ¥{price}")
            else:
                order['status'] = 'rejected'
                order['reason'] = '资金不足'
                print(f"❌ 订单被拒: 资金不足")

        elif action == 'SELL':
            if self.positions.get(symbol, 0) >= quantity:
                revenue = quantity * price
                self.cash += revenue
                self.positions[symbol] -= quantity
                order['status'] = 'filled'
                print(f"✅ 卖出 {symbol} {quantity}股 @ ¥{price}")
            else:
                order['status'] = 'rejected'
                order['reason'] = '持仓不足'
                print(f"❌ 订单被拒: 持仓不足")

        self.trade_history.append(order)

        return order

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """获取组合价值"""

        holdings_value = 0
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                price = current_prices.get(symbol, 0)
                holdings_value += quantity * price

        total_value = self.cash + holdings_value

        return {
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total_value': total_value,
            'pnl': total_value - self.capital,
            'return_pct': ((total_value - self.capital) / self.capital * 100)
        }

    def get_performance_report(self) -> Dict[str, Any]:
        """获取绩效报告"""

        filled_orders = [o for o in self.trade_history if o['status'] == 'filled']

        report = {
            'total_trades': len(filled_orders),
            'buy_orders': len([o for o in filled_orders if o['action'] == 'BUY']),
            'sell_orders': len([o for o in filled_orders if o['action'] == 'SELL']),
            'current_cash': self.cash,
            'positions': self.positions
        }

        return report


def main():
    parser = argparse.ArgumentParser(description='Paper Trading Simulator - 模拟交易')
    parser.add_argument('--capital', type=float, default=100000, help='初始资金')

    args = parser.parse_args()

    print("🚀 Paper Trading Simulator 启动...")
    print()
    print(f"💰 初始资金: ¥{args.capital:,.2f}\n")

    simulator = PaperTradingSimulator(args.capital)

    # 模拟交易
    print("📊 执行模拟交易:\n")

    simulator.place_order('600000', 'BUY', 1000, 10.5)
    simulator.place_order('000001', 'BUY', 2000, 15.2)
    simulator.place_order('600000', 'SELL', 500, 11.0)

    # 获取组合价值
    current_prices = {'600000': 11.2, '000001': 15.8}

    print("\n📈 组合状态:")
    portfolio = simulator.get_portfolio_value(current_prices)

    print(f"  现金: ¥{portfolio['cash']:,.2f}")
    print(f"  持仓市值: ¥{portfolio['holdings_value']:,.2f}")
    print(f"  总市值: ¥{portfolio['total_value']:,.2f}")
    print(f"  盈亏: ¥{portfolio['pnl']:,.2f} ({portfolio['return_pct']:.2f}%)")

    print("\n📊 绩效报告:")
    report = simulator.get_performance_report()
    print(f"  总交易数: {report['total_trades']}")
    print(f"  买入: {report['buy_orders']} | 卖出: {report['sell_orders']}")

    print("\n✅ Paper Trading Simulator 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
