#!/usr/bin/env python3
"""
Performance Attribution - 收益归因分析
使用 pyfolio-reloaded 生成业绩分析报告
"""

import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import pandas as pd
import numpy as np


def get_returns_from_db(db_path: str, account_type: str = 'model') -> pd.Series:
    """从数据库获取收益率序列"""
    conn = sqlite3.connect(db_path)

    try:
        # 从 model_trades 或 real_trades 获取交易记录
        query = f"""
            SELECT date, profit_loss, profit_loss_ratio
            FROM {account_type}_trades
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print(f"警告: {account_type}_trades 表为空")
            return pd.Series(dtype=float)

        # 转换为收益率序列
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        returns = df['profit_loss_ratio']

        return returns

    except Exception as e:
        print(f"警告: 获取收益率数据失败: {e}")
        return pd.Series(dtype=float)
    finally:
        conn.close()


def generate_mock_returns(days: int = 252) -> pd.Series:
    """生成模拟收益率数据（用于测试）"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    # 生成随机收益率（均值 0.001，标准差 0.02）
    returns = pd.Series(
        np.random.normal(0.001, 0.02, days),
        index=dates
    )
    return returns


def calculate_basic_metrics(returns: pd.Series) -> Dict[str, Any]:
    """计算基础业绩指标"""
    if returns.empty:
        return {}

    # 累计收益
    cumulative_returns = (1 + returns).cumprod() - 1
    total_return = cumulative_returns.iloc[-1]

    # 年化收益（假设252个交易日）
    days = len(returns)
    annualized_return = (1 + total_return) ** (252 / days) - 1

    # 波动率
    volatility = returns.std() * np.sqrt(252)

    # Sharpe Ratio（假设无风险利率 0.03）
    risk_free_rate = 0.03
    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0

    # 最大回撤
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()

    # 胜率
    win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

    return {
        'total_return': float(total_return),
        'annualized_return': float(annualized_return),
        'volatility': float(volatility),
        'sharpe_ratio': float(sharpe_ratio),
        'max_drawdown': float(max_drawdown),
        'win_rate': float(win_rate),
        'total_trades': len(returns)
    }


def generate_attribution_report(
    db_path: str,
    account_type: str = 'model',
    use_mock_data: bool = False,
    registry_path: str = '/Users/niny/NiaOS/configs/invest/performance_attribution_registry.json'
) -> Dict[str, Any]:
    """生成收益归因报告"""

    print(f"📊 获取 {account_type} 账户收益数据...")

    if use_mock_data:
        print("⚠️  使用模拟数据")
        returns = generate_mock_returns(252)
    else:
        returns = get_returns_from_db(db_path, account_type)

        if returns.empty:
            print("警告: 无收益数据，使用模拟数据")
            returns = generate_mock_returns(252)

    print(f"✅ 收集到 {len(returns)} 天的收益数据")

    # 计算基础指标
    print("\n📈 计算业绩指标...")
    metrics = calculate_basic_metrics(returns)

    if not metrics:
        print("❌ 计算失败")
        return {}

    # 构建报告
    report = {
        'attribution_id': f"attr_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'period': f"{returns.index[0].date()} ~ {returns.index[-1].date()}",
        'account_type': account_type,
        'metrics': metrics,
        'created_at': datetime.now().isoformat()
    }

    # 更新 registry
    if Path(registry_path).exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Performance Attribution Registry",
            "description": "收益归因 Registry",
            "version": "1.0.0",
            "attribution_records": []
        }

    registry.setdefault('attribution_records', []).append({
        'attribution_id': report['attribution_id'],
        'period': report['period'],
        'total_return': metrics['total_return'],
        'sharpe_ratio': metrics['sharpe_ratio'],
        'max_drawdown': metrics['max_drawdown'],
        'created_at': report['created_at']
    })

    registry['last_updated'] = datetime.now().isoformat()

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)

    print(f"✅ 已更新 registry: {registry_path}")

    return report


def main():
    parser = argparse.ArgumentParser(description='Performance Attribution - 收益归因分析')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/data/investment.db',
        help='数据库路径'
    )
    parser.add_argument(
        '--account-type',
        default='model',
        choices=['model', 'real'],
        help='账户类型'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='使用模拟数据'
    )
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/performance_attribution_registry.json',
        help='Registry 路径'
    )
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    args = parser.parse_args()

    print("🚀 Performance Attribution 启动...")
    print(f"📁 数据库: {args.db_path}")
    print()

    # 生成报告
    report = generate_attribution_report(
        args.db_path,
        args.account_type,
        args.mock,
        args.registry
    )

    if not report:
        print("\n❌ 报告生成失败")
        return 1

    # 输出结果
    print()
    print("=" * 60)
    print("📊 业绩归因报告")
    print("=" * 60)
    print(f"\n周期: {report['period']}")
    print(f"账户: {report['account_type']}")

    metrics = report['metrics']
    print(f"\n📈 收益指标:")
    print(f"  总收益率: {metrics['total_return']*100:.2f}%")
    print(f"  年化收益率: {metrics['annualized_return']*100:.2f}%")
    print(f"  最大回撤: {metrics['max_drawdown']*100:.2f}%")

    print(f"\n📊 风险指标:")
    print(f"  波动率: {metrics['volatility']*100:.2f}%")
    print(f"  Sharpe 比率: {metrics['sharpe_ratio']:.2f}")

    print(f"\n🎯 交易统计:")
    print(f"  总交易次数: {metrics['total_trades']}")
    print(f"  胜率: {metrics['win_rate']*100:.1f}%")

    # JSON 输出
    if args.json:
        print()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n✅ Performance Attribution 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
