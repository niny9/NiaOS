#!/usr/bin/env python3
"""
Factor Engine - 因子引擎
使用 vectorbt 计算技术因子
"""

import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import pandas as pd
import numpy as np


def load_stock_data(db_path: str, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """从数据库加载股票数据"""
    conn = sqlite3.connect(db_path)

    try:
        query = f"""
            SELECT date, open, high, low, close, volume
            FROM stock_daily_bar
            WHERE code = '{symbol}'
        """

        if start_date:
            query += f" AND date >= '{start_date}'"
        if end_date:
            query += f" AND date <= '{end_date}'"

        query += " ORDER BY date"

        df = pd.read_sql_query(query, conn)

        if df.empty:
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        return df

    finally:
        conn.close()


def calculate_ma(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """计算移动平均线"""
    return df['close'].rolling(window=window).mean()


def calculate_ema(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """计算指数移动平均线"""
    return df['close'].ewm(span=window, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """计算 RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """计算 MACD"""
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
    """计算布林带"""
    middle = df['close'].rolling(window=window).mean()
    std = df['close'].rolling(window=window).std()

    upper = middle + (std * num_std)
    lower = middle - (std * num_std)

    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """计算 ATR（平均真实波幅）"""
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()

    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=window).mean()

    return atr


def calculate_all_factors(df: pd.DataFrame) -> Dict[str, Any]:
    """计算所有因子"""
    factors = {}

    print("  📊 计算趋势类因子...")
    factors['ma_5'] = calculate_ma(df, 5)
    factors['ma_10'] = calculate_ma(df, 10)
    factors['ma_20'] = calculate_ma(df, 20)
    factors['ma_60'] = calculate_ma(df, 60)
    factors['ema_12'] = calculate_ema(df, 12)
    factors['ema_26'] = calculate_ema(df, 26)

    print("  📊 计算动量类因子...")
    factors['rsi_14'] = calculate_rsi(df, 14)

    macd_result = calculate_macd(df)
    factors['macd'] = macd_result['macd']
    factors['macd_signal'] = macd_result['signal']
    factors['macd_histogram'] = macd_result['histogram']

    print("  📊 计算波动类因子...")
    bb_result = calculate_bollinger_bands(df)
    factors['bb_upper'] = bb_result['upper']
    factors['bb_middle'] = bb_result['middle']
    factors['bb_lower'] = bb_result['lower']

    factors['atr_14'] = calculate_atr(df, 14)

    print("  ✅ 完成，共计算 14 个因子")

    return factors


def save_factors_to_registry(
    symbol: str,
    factors: Dict[str, Any],
    registry_path: str = '/Users/niny/NiaOS/configs/invest/factor_registry.json'
):
    """保存因子到 registry"""

    if Path(registry_path).exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    else:
        registry = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Factor Registry",
            "description": "因子库 Registry",
            "version": "1.0.0",
            "factors": []
        }

    # 更新因子列表
    existing_factor_names = {f['name'] for f in registry.get('factors', [])}

    for factor_name in factors.keys():
        if factor_name not in existing_factor_names:
            registry.setdefault('factors', []).append({
                'factor_id': f"factor_{len(registry.get('factors', [])) + 1:03d}_{factor_name}",
                'name': factor_name,
                'category': 'technical',
                'status': 'active',
                'created_at': datetime.now().isoformat()
            })

    registry['last_updated'] = datetime.now().isoformat()
    registry['statistics'] = {
        'total_factors': len(registry.get('factors', [])),
        'by_category': {'technical': len(registry.get('factors', []))},
        'by_status': {'active': len(registry.get('factors', []))}
    }

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)

    print(f"✅ 已保存到 registry: {registry_path}")


def main():
    parser = argparse.ArgumentParser(description='Factor Engine - 因子引擎')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/data/investment.db',
        help='数据库路径'
    )
    parser.add_argument('--symbol', default='600000.SH', help='股票代码')
    parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/factor_registry.json',
        help='Registry 路径'
    )
    parser.add_argument('--output', help='输出文件路径 (CSV)')

    args = parser.parse_args()

    print("🚀 Factor Engine 启动...")
    print(f"📁 数据库: {args.db_path}")
    print(f"📊 股票: {args.symbol}")
    print()

    # 加载数据
    print("📊 加载股票数据...")
    df = load_stock_data(args.db_path, args.symbol, args.start_date, args.end_date)

    if df.empty:
        print(f"❌ 无数据: {args.symbol}")
        return 1

    print(f"✅ 加载 {len(df)} 天数据 ({df.index[0].date()} ~ {df.index[-1].date()})")

    # 计算因子
    print("\n🔬 计算因子...")
    factors = calculate_all_factors(df)

    # 保存到 registry
    print(f"\n💾 保存因子...")
    save_factors_to_registry(args.symbol, factors, args.registry)

    # 输出到 CSV
    if args.output:
        factor_df = pd.DataFrame(factors)
        factor_df.to_csv(args.output)
        print(f"✅ 已保存到: {args.output}")

    # 输出统计
    print("\n" + "=" * 60)
    print("📊 因子计算结果")
    print("=" * 60)
    print(f"\n股票: {args.symbol}")
    print(f"数据周期: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"数据点数: {len(df)}")
    print(f"\n计算的因子 ({len(factors)} 个):")

    for i, (name, series) in enumerate(factors.items(), 1):
        valid_count = series.notna().sum()
        print(f"  {i:2d}. {name:20s} - 有效值: {valid_count}/{len(series)}")

    print("\n✅ Factor Engine 完成！")
    return 0


if __name__ == '__main__':
    exit(main())
