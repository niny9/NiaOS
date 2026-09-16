#!/usr/bin/env python3
"""
Invest OS 数据源健康检查脚本（修复版）
检查数据库、配置、API 状态
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent

def check_database() -> Dict[str, Any]:
    """检查数据库状态"""
    result = {
        'status': 'unknown',
        'file_exists': False,
        'file_size': 0,
        'positions_count': 0,
        'active_positions': 0,
        'active_symbols': [],
        'last_update': None,
        'days_since_update': None,
        'issues': []
    }
    
    env_file = PROJECT_ROOT / '.env'
    db_path = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DB_PATH='):
                    db_path = PROJECT_ROOT / line.strip().split('=', 1)[1]
                    break
    
    if not db_path or not db_path.exists():
        result['status'] = 'error'
        result['issues'].append(f'数据库文件不存在: {db_path}')
        return result
    
    result['file_exists'] = True
    result['file_size'] = db_path.stat().st_size
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 使用 real_positions 表（不是 holdings）
        cursor.execute("SELECT COUNT(*) FROM real_positions")
        result['positions_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM real_positions WHERE status = 'active'")
        result['active_positions'] = cursor.fetchone()[0]
        
        # 获取活跃持仓代码
        cursor.execute("SELECT code, name FROM real_positions WHERE status = 'active'")
        result['active_symbols'] = [f"{row[0]} {row[1]}" for row in cursor.fetchall()]
        
        # 检查最后更新时间
        cursor.execute("SELECT MAX(updated_at) FROM real_positions")
        last_update = cursor.fetchone()[0]
        
        if last_update:
            result['last_update'] = last_update
            try:
                update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                days_ago = (datetime.now() - update_dt).days
                result['days_since_update'] = days_ago
                
                if days_ago > 7:
                    result['issues'].append(f'持仓数据已 {days_ago} 天未更新')
                    result['status'] = 'warning'
            except:
                pass
        
        conn.close()
        
        if result['active_positions'] == 0:
            result['issues'].append('无活跃持仓')
            result['status'] = 'warning'
        
        if result['status'] == 'unknown':
            result['status'] = 'ok'
            
    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f'数据库查询失败: {str(e)}')
    
    return result

def generate_report(db_check: Dict) -> str:
    """生成健康检查报告"""
    lines = []
    lines.append("# Invest OS 健康检查报告（修复版）")
    lines.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("\n---\n")
    
    status_icon = {'ok': '✅', 'warning': '⚠️', 'error': '❌', 'unknown': '❓'}
    icon = status_icon.get(db_check['status'], '❓')
    
    lines.append(f"## {icon} 数据库状态: {db_check['status']}")
    lines.append(f"- **文件存在**: {db_check['file_exists']}")
    lines.append(f"- **文件大小**: {db_check['file_size']} 字节")
    lines.append(f"- **总持仓数**: {db_check['positions_count']}")
    lines.append(f"- **活跃持仓**: {db_check['active_positions']}")
    
    if db_check['active_symbols']:
        lines.append(f"\n**活跃持仓列表**:")
        for symbol in db_check['active_symbols']:
            lines.append(f"- {symbol}")
    
    if db_check['last_update']:
        lines.append(f"\n- **最后更新**: {db_check['last_update']}")
        if db_check['days_since_update'] is not None:
            lines.append(f"- **距今天数**: {db_check['days_since_update']} 天")
    
    if db_check['issues']:
        lines.append("\n**问题**:")
        for issue in db_check['issues']:
            lines.append(f"- {issue}")
    
    lines.append("\n---\n")
    lines.append("## 修复说明")
    lines.append("- ✅ 已修复：使用 `real_positions` 表（原健康检查错误使用了不存在的 `holdings` 表）")
    lines.append(f"- 数据库架构：使用 `real_positions`, `real_trades` 等表")
    
    return '\n'.join(lines)

def main():
    print("========================================")
    print("Invest OS 健康检查（修复版）")
    print("========================================")
    print()
    
    print("检查数据库...")
    db_check = check_database()
    
    report = generate_report(db_check)
    
    output_file = PROJECT_ROOT / 'health_check_report_fixed.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成: {output_file}")
    print()
    print(report)
    
    if db_check['status'] == 'error':
        sys.exit(1)
    elif db_check['status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
