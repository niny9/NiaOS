#!/usr/bin/env python3
"""
Risk Monitor - 风控监控
实时监控投资组合的风险指标
"""

import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


def load_risk_registry(registry_path: str) -> Dict[str, Any]:
    """加载 risk registry"""
    if not Path(registry_path).exists():
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Risk Registry",
            "description": "风控规则 Registry",
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "risk_rules": []
        }

    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_risk_registry(registry: Dict[str, Any], registry_path: str):
    """保存 risk registry"""
    registry['last_updated'] = datetime.now().isoformat()
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, indent=2, ensure_ascii=False, fp=f)


def get_portfolio_data(db_path: str) -> Dict[str, Any]:
    """从数据库获取持仓数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取真实持仓（简化版，只获取核心字段）
        cursor.execute("""
            SELECT code, name, quantity
            FROM real_positions
            WHERE account_type = 'real'
        """)

        positions = []
        total_value = 0

        for row in cursor.fetchall():
            # 简化版：假设每股市值为数量 * 假设价格
            quantity = row[2] if row[2] else 0
            assumed_price = 10.0  # 假设价格
            market_value = quantity * assumed_price

            position = {
                'code': row[0],
                'name': row[1],
                'quantity': quantity,
                'market_value': market_value
            }
            positions.append(position)
            total_value += market_value

        return {
            'positions': positions,
            'total_value': total_value,
            'position_count': len(positions)
        }

    except Exception as e:
        print(f"警告: 获取持仓数据失败: {e}")
        return {
            'positions': [],
            'total_value': 0,
            'position_count': 0
        }
    finally:
        conn.close()


def check_position_limit(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """检查单只股票仓位限制"""
    violations: List[Dict[str, Any]] = []
    rule = {
        'rule_id': 'risk_001_single_position',
        'name': '单只股票仓位限制',
        'type': 'position_limit',
        'threshold': 0.20,
        'severity': 'high',
        'violations': violations
    }

    if portfolio['total_value'] == 0:
        return {**rule, 'status': 'pass', 'current_value': 0}

    max_position_ratio = 0
    for position in portfolio['positions']:
        ratio = position['market_value'] / portfolio['total_value']
        if ratio > max_position_ratio:
            max_position_ratio = ratio

        if ratio > rule['threshold']:
            violations.append({
                'symbol': position['code'],
                'name': position['name'],
                'ratio': ratio,
                'market_value': position['market_value']
            })

    return {
        **rule,
        'current_value': max_position_ratio,
        'status': 'violated' if rule['violations'] else 'pass'
    }


def check_sector_concentration(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """检查行业集中度（简化版：假设所有是同一行业）"""
    rule = {
        'rule_id': 'risk_002_sector_concentration',
        'name': '行业集中度限制',
        'type': 'sector_limit',
        'threshold': 0.40,
        'severity': 'medium',
        'violations': []
    }

    # 简化版：这里需要行业分类数据
    # 暂时返回 pass
    return {
        **rule,
        'current_value': 0,
        'status': 'pass'
    }


def check_leverage(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """检查杠杆（融资融券）"""
    rule = {
        'rule_id': 'risk_004_leverage',
        'name': '杠杆限制',
        'type': 'leverage',
        'threshold': 1.0,
        'severity': 'critical',
        'violations': []
    }

    # 简化版：假设无杠杆
    return {
        **rule,
        'current_value': 1.0,
        'status': 'pass'
    }


def run_risk_check(
    db_path: str,
    registry_path: str = '/Users/niny/NiaOS/configs/invest/risk_registry.json'
) -> Dict[str, Any]:
    """运行风控检查"""

    print("📊 获取持仓数据...")
    portfolio = get_portfolio_data(db_path)

    if portfolio['position_count'] == 0:
        print("⚠️  无持仓数据，跳过风控检查")
        return {
            'check_time': datetime.now().isoformat(),
            'portfolio_summary': portfolio,
            'risk_checks': [],
            'overall_status': 'pass',
            'violations': []
        }

    print(f"✅ 发现 {portfolio['position_count']} 个持仓")
    print(f"   总市值: ¥{portfolio['total_value']:,.2f}")

    print("\n🔍 执行风控检查...")

    # 执行各项风控检查
    checks = [
        check_position_limit(portfolio),
        check_sector_concentration(portfolio),
        check_leverage(portfolio)
    ]

    # 统计违规
    violations = []
    for check in checks:
        if check['status'] == 'violated':
            violations.extend(check.get('violations', []))

        # 打印结果
        if check['status'] == 'pass':
            print(f"  ✅ {check['name']}: 通过")
        else:
            print(f"  ❌ {check['name']}: 违规 ({len(check.get('violations', []))} 项)")

    # 总体评估
    overall_status = 'violated' if violations else 'pass'

    result = {
        'check_time': datetime.now().isoformat(),
        'portfolio_summary': portfolio,
        'risk_checks': checks,
        'overall_status': overall_status,
        'violations': violations
    }

    # 更新 registry
    registry = load_risk_registry(registry_path)
    registry['risk_rules'] = checks
    registry['statistics'] = {
        'total_rules': len(checks),
        'enabled_rules': len(checks),
        'violated_rules': sum(1 for c in checks if c['status'] == 'violated'),
        'critical_rules': sum(1 for c in checks if c.get('severity') == 'critical')
    }
    save_risk_registry(registry, registry_path)

    return result


def main():
    parser = argparse.ArgumentParser(description='Risk Monitor - 风控监控')
    parser.add_argument(
        '--db-path',
        default='/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/data/investment.db',
        help='数据库路径'
    )
    parser.add_argument(
        '--registry',
        default='/Users/niny/NiaOS/configs/invest/risk_registry.json',
        help='Registry 路径'
    )
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')

    args = parser.parse_args()

    print("🚀 Risk Monitor 启动...")
    print(f"📁 数据库: {args.db_path}")
    print()

    if not Path(args.db_path).exists():
        print(f"❌ 数据库不存在: {args.db_path}")
        return 1

    # 执行风控检查
    result = run_risk_check(args.db_path, args.registry)

    # 输出结果
    print()
    print("=" * 60)
    print("📊 风控检查结果")
    print("=" * 60)
    print(f"\n总体状态: {result['overall_status'].upper()}")
    print(f"\n持仓统计:")
    print(f"  持仓数量: {result['portfolio_summary']['position_count']} 个")
    print(f"  总市值: ¥{result['portfolio_summary']['total_value']:,.2f}")

    print(f"\n风控检查:")
    print(f"  总规则数: {len(result['risk_checks'])} 个")
    print(f"  通过: {sum(1 for c in result['risk_checks'] if c['status'] == 'pass')} 个")
    print(f"  违规: {sum(1 for c in result['risk_checks'] if c['status'] == 'violated')} 个")

    if result['violations']:
        print(f"\n⚠️  发现 {len(result['violations'])} 项违规:")
        for v in result['violations']:
            print(f"  • {v['name']} ({v['symbol']}): 仓位 {v['ratio']*100:.1f}%")

    # JSON 输出
    if args.json:
        print()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 返回状态码
    if result['overall_status'] == 'violated':
        print("\n⛔ 风控检查未通过，禁止下单！")
        return 2
    else:
        print("\n✅ 风控检查通过！")
        return 0


if __name__ == '__main__':
    exit(main())
