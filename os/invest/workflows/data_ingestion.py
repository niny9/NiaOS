#!/usr/bin/env python3
"""
Data Ingestion - 数据接入
从多个数据源抓取市场数据并存入本地数据库
"""

import sqlite3
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json


def load_market_data_registry(registry_path: str) -> Dict[str, Any]:
    """加载 market data registry"""
    if not os.path.exists(registry_path):
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Market Data Registry",
            "description": "市场数据 Registry",
            "version": "1.0.0",
            "data_sources": []
        }

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_market_data_registry(registry: Dict[str, Any], registry_path: str):
    """保存 market data registry"""
    registry['last_updated'] = datetime.now().isoformat()
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)
    print(f"✅ 已更新 registry: {registry_path}")


def fetch_from_yahoo_finance(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """从 Yahoo Finance 获取数据（需要 yfinance 库）"""
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        data = []
        for date, row in df.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        return data

    except ImportError:
        print("警告: yfinance 未安装，请运行: pip install yfinance")
        return []
    except Exception as e:
        print(f"警告: Yahoo Finance 获取失败: {e}")
        return []


def fetch_from_akshare(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """从 AKShare 获取数据（A股）"""
    try:
        import akshare as ak

        # AKShare 股票代码格式：600000（不需要.SH后缀）
        clean_symbol = symbol.replace('.SH', '').replace('.SZ', '')

        df = ak.stock_zh_a_hist(symbol=clean_symbol, start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''), adjust="qfq")

        data = []
        for _, row in df.iterrows():
            data.append({
                'date': row['日期'],
                'open': float(row['开盘']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'close': float(row['收盘']),
                'volume': int(row['成交量'])
            })

        return data

    except ImportError:
        print("警告: akshare 未安装，请运行: pip install akshare")
        return []
    except Exception as e:
        print(f"警告: AKShare 获取失败: {e}")
        return []


def fetch_mock_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """生成模拟数据（用于测试）"""
    import random

    data = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    base_price = 100.0

    while current <= end:
        # 跳过周末
        if current.weekday() < 5:
            change = random.uniform(-0.05, 0.05)
            base_price *= (1 + change)

            data.append({
                'date': current.strftime('%Y-%m-%d'),
                'open': round(base_price * random.uniform(0.98, 1.02), 2),
                'high': round(base_price * random.uniform(1.00, 1.05), 2),
                'low': round(base_price * random.uniform(0.95, 1.00), 2),
                'close': round(base_price, 2),
                'volume': random.randint(1000000, 10000000)
            })

        current += timedelta(days=1)

    return data


def save_to_database(db_path: str, symbol: str, data: List[Dict[str, Any]], source: str) -> int:
    """保存数据到数据库"""

    if not data:
        print(f"警告: 无数据可保存")
        return 0

    # 确保数据库目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_daily_bar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, date)
        )
    ''')

    # 插入数据（忽略重复）
    inserted = 0
    for row in data:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO stock_daily_bar
                (code, date, open, high, low, close, volume, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                row['date'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume'],
                source
            ))

            if cursor.rowcount > 0:
                inserted += 1

        except Exception as e:
            print(f"警告: 插入失败: {e}")

    conn.commit()
    conn.close()

    return inserted


def ingest_data(
    symbol: str,
    start_date: str,
    end_date: str,
    source: str,
    db_path: str,
    registry_path: str,
    mock: bool = False
) -> Dict[str, Any]:
    """数据接入主函数"""

    print(f"📊 开始接入数据...")
    print(f"   股票: {symbol}")
    print(f"   来源: {source}")
    print(f"   周期: {start_date} ~ {end_date}")
    print()

    # 1. 获取数据
    print(f"🔍 从 {source} 获取数据...")

    if mock:
        data = fetch_mock_data(symbol, start_date, end_date)
    elif source == 'yahoo':
        data = fetch_from_yahoo_finance(symbol, start_date, end_date)
    elif source == 'akshare':
        data = fetch_from_akshare(symbol, start_date, end_date)
    else:
        print(f"❌ 不支持的数据源: {source}")
        return {'success': False, 'error': 'Unsupported source'}

    if not data:
        print(f"❌ 未获取到数据")
        return {'success': False, 'error': 'No data fetched'}

    print(f"✅ 获取到 {len(data)} 条数据")

    # 2. 保存到数据库
    print(f"\n💾 保存到数据库...")
    inserted = save_to_database(db_path, symbol, data, source)
    print(f"✅ 新增 {inserted} 条数据")

    # 3. 更新 registry
    print(f"\n📝 更新 registry...")
    registry = load_market_data_registry(registry_path)

    # 更新或添加数据源
    found = False
    for ds in registry.get('data_sources', []):
        if ds.get('symbol') == symbol:
            ds['last_update'] = datetime.now().isoformat()
            ds['data_end_date'] = end_date
            found = True
            break

    if not found:
        registry.setdefault('data_sources', []).append({
            'symbol': symbol,
            'name': f'股票 {symbol}',
            'asset_type': 'stock',
            'data_provider': source,
            'data_path': db_path,
            'last_update': datetime.now().isoformat(),
            'data_start_date': start_date,
            'data_end_date': end_date,
            'frequency': 'daily'
        })

    save_market_data_registry(registry, registry_path)

    return {
        'success': True,
        'symbol': symbol,
        'source': source,
        'fetched': len(data),
        'inserted': inserted,
        'db_path': db_path
    }


def main():
    parser = argparse.ArgumentParser(description='Data Ingestion - 数据接入')
    parser.add_argument('--symbol', required=True, help='股票代码（如 600000.SH 或 AAPL）')
    parser.add_argument('--source', default='mock', choices=['yahoo', 'akshare', 'mock'],
                        help='数据源')
    parser.add_argument('--start-date', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='获取最近N天数据（默认30天）')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/NiaOS/data/invest/market_data.db',
        help='数据库路径'
    )
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/market_data_registry.json',
        help='Registry 路径'
    )
    parser.add_argument('--mock', action='store_true', help='使用模拟数据')

    args = parser.parse_args()

    print("🚀 Data Ingestion 启动...")
    print()

    # 计算日期范围
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y-%m-%d')

    if not args.start_date:
        end = datetime.strptime(args.end_date, '%Y-%m-%d')
        start = end - timedelta(days=args.days)
        args.start_date = start.strftime('%Y-%m-%d')

    # 执行数据接入
    result = ingest_data(
        args.symbol,
        args.start_date,
        args.end_date,
        args.source,
        args.db_path,
        args.registry,
        args.mock
    )

    # 输出结果
    print()
    print("=" * 60)
    print("📊 数据接入结果")
    print("=" * 60)

    if result['success']:
        print(f"\n✅ 数据接入成功")
        print(f"   股票: {result['symbol']}")
        print(f"   来源: {result['source']}")
        print(f"   获取: {result['fetched']} 条")
        print(f"   新增: {result['inserted']} 条")
        print(f"   数据库: {result['db_path']}")
    else:
        print(f"\n❌ 数据接入失败: {result.get('error', '未知错误')}")
        return 1

    print("\n✅ Data Ingestion 完成！")
    return 0


if __name__ == '__main__':
    import os
    exit(main())
