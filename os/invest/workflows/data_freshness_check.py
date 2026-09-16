#!/usr/bin/env python3
"""
Data Freshness Check - 数据新鲜度检查
检查 Invest OS 数据库的数据新鲜度
"""

import sqlite3
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


def check_table_freshness(
    db_path: str,
    table_name: str,
    date_column: str = 'date'
) -> Dict[str, Any]:
    """检查单个表的数据新鲜度"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取最新数据日期
        query = f"SELECT MAX({date_column}) FROM {table_name}"
        cursor.execute(query)
        result = cursor.fetchone()

        if not result or not result[0]:
            return {
                'table': table_name,
                'last_date': None,
                'days_old': None,
                'status': 'empty',
                'message': '表为空或无数据'
            }

        last_date_str = result[0]
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        today = datetime.now()
        days_old = (today - last_date).days

        # 判断新鲜度状态
        if days_old <= 7:
            status = 'fresh'
            message = '数据新鲜'
        elif days_old <= 30:
            status = 'stale'
            message = f'数据较旧（{days_old} 天），建议更新'
        else:
            status = 'expired'
            message = f'数据过期（{days_old} 天），拒绝使用'

        return {
            'table': table_name,
            'last_date': last_date_str,
            'days_old': days_old,
            'status': status,
            'message': message
        }

    except Exception as e:
        return {
            'table': table_name,
            'last_date': None,
            'days_old': None,
            'status': 'error',
            'message': f'检查失败: {str(e)}'
        }
    finally:
        conn.close()


def check_all_tables(db_path: str) -> Dict[str, Any]:
    """检查所有关键表的数据新鲜度"""

    # 关键表和它们的日期列
    tables_to_check = {
        'stock_daily_bar': 'date',
        'factor_scores': 'date',
        'model_portfolio': 'date',
        'parameter_performance': 'date'
    }

    results: List[Dict[str, Any]] = []

    for table_name, date_column in tables_to_check.items():
        print(f"📊 检查表: {table_name}")
        result = check_table_freshness(db_path, table_name, date_column)
        results.append(result)

        # 打印结果
        if result['status'] == 'fresh':
            print(f"  ✅ {result['message']} (最新: {result['last_date']}, {result['days_old']} 天前)")
        elif result['status'] == 'stale':
            print(f"  ⚠️  {result['message']} (最新: {result['last_date']})")
        elif result['status'] == 'expired':
            print(f"  ❌ {result['message']} (最新: {result['last_date']})")
        else:
            print(f"  ⚠️  {result['message']}")

    # 总体评估
    expired_count = sum(1 for r in results if r['status'] == 'expired')
    stale_count = sum(1 for r in results if r['status'] == 'stale')
    fresh_count = sum(1 for r in results if r['status'] == 'fresh')
    error_count = sum(1 for r in results if r['status'] == 'error')

    if expired_count > 0:
        overall_status = 'expired'
        overall_message = f'{expired_count} 个表数据过期（>30天），拒绝运行策略'
    elif stale_count > 0:
        overall_status = 'stale'
        overall_message = f'{stale_count} 个表数据较旧（7-30天），建议更新'
    elif error_count > 0:
        overall_status = 'error'
        overall_message = f'{error_count} 个表检查失败'
    else:
        overall_status = 'fresh'
        overall_message = '所有数据新鲜，可以运行策略'

    return {
        'db_path': db_path,
        'check_time': datetime.now().isoformat(),
        'overall_status': overall_status,
        'overall_message': overall_message,
        'summary': {
            'fresh': fresh_count,
            'stale': stale_count,
            'expired': expired_count,
            'error': error_count
        },
        'details': results
    }


def update_registry(check_result: Dict[str, Any], registry_path: str):
    """更新 market_data_registry.json"""

    if not Path(registry_path).exists():
        print(f"警告: Registry 不存在: {registry_path}")
        return

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # 更新新鲜度状态
    for data_source in registry.get('data_sources', []):
        # 查找对应的检查结果
        for detail in check_result['details']:
            if detail['table'] == 'stock_daily_bar':  # 主要数据表
                data_source['last_update'] = detail['last_date'] + 'T16:00:00Z' if detail['last_date'] else None
                data_source['freshness_status'] = detail['status']

    # 更新统计
    registry['statistics']['by_freshness'] = {
        'fresh': check_result['summary']['fresh'],
        'stale': check_result['summary']['stale'],
        'expired': check_result['summary']['expired']
    }

    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)

    print(f"✅ 已更新 registry: {registry_path}")


def main():
    parser = argparse.ArgumentParser(description='Data Freshness Check - 数据新鲜度检查')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/data/investment.db',
        help='数据库路径'
    )
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/market_data_registry.json',
        help='Registry 路径'
    )
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('--update-registry', action='store_true', help='更新 registry')

    args = parser.parse_args()

    print("🚀 Data Freshness Check 启动...")
    print(f"📁 数据库: {args.db_path}")
    print()

    if not Path(args.db_path).exists():
        print(f"❌ 数据库不存在: {args.db_path}")
        return 1

    # 执行检查
    result = check_all_tables(args.db_path)

    # 输出结果
    print()
    print("=" * 60)
    print("📊 数据新鲜度检查结果")
    print("=" * 60)
    print(f"\n总体状态: {result['overall_status'].upper()}")
    print(f"评估: {result['overall_message']}")
    print(f"\n统计:")
    print(f"  ✅ 新鲜 (≤7天): {result['summary']['fresh']} 个表")
    print(f"  ⚠️  较旧 (7-30天): {result['summary']['stale']} 个表")
    print(f"  ❌ 过期 (>30天): {result['summary']['expired']} 个表")
    print(f"  ⚠️  错误: {result['summary']['error']} 个表")

    # 更新 registry
    if args.update_registry:
        print()
        update_registry(result, args.registry)

    # JSON 输出
    if args.json:
        print()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 返回状态码
    if result['overall_status'] == 'expired':
        print("\n⛔ 数据过期，拒绝运行策略！")
        return 2
    elif result['overall_status'] == 'stale':
        print("\n⚠️  数据较旧，建议更新后再运行策略")
        return 1
    else:
        print("\n✅ 数据新鲜度检查通过！")
        return 0


if __name__ == '__main__':
    exit(main())
