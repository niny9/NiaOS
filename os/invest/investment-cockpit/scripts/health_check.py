#!/usr/bin/env python3
"""
Invest OS 数据源健康检查脚本
检查数据库、配置、API 状态
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def check_env_config() -> Dict[str, Any]:
    """检查 .env 配置"""
    env_file = PROJECT_ROOT / '.env'
    result = {
        'status': 'unknown',
        'file_exists': False,
        'db_path_configured': False,
        'db_path': None,
        'feishu_configured': False,
        'issues': []
    }
    
    if not env_file.exists():
        result['status'] = 'error'
        result['issues'].append('.env 文件不存在')
        return result
    
    result['file_exists'] = True
    
    # 读取配置
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DB_PATH='):
                result['db_path_configured'] = True
                result['db_path'] = line.split('=', 1)[1]
            elif line.startswith('FEISHU_APP_ID='):
                result['feishu_configured'] = True
    
    if not result['db_path_configured']:
        result['issues'].append('DB_PATH 未配置')
        result['status'] = 'error'
    elif result['db_path'] and 'database/investment.db' not in result['db_path']:
        result['issues'].append(f'DB_PATH 路径可能错误: {result["db_path"]}')
        result['status'] = 'warning'
    
    if result['status'] == 'unknown':
        result['status'] = 'ok'
    
    return result

def check_database() -> Dict[str, Any]:
    """检查数据库状态"""
    result = {
        'status': 'unknown',
        'file_exists': False,
        'file_size': 0,
        'holdings_count': 0,
        'active_holdings': 0,
        'last_update': None,
        'days_since_update': None,
        'issues': []
    }
    
    # 从 .env 读取数据库路径
    env_file = PROJECT_ROOT / '.env'
    db_path = None
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DB_PATH='):
                    db_path = PROJECT_ROOT / line.strip().split('=', 1)[1]
                    break
    
    if not db_path:
        result['status'] = 'error'
        result['issues'].append('无法从 .env 读取 DB_PATH')
        return result
    
    if not db_path.exists():
        result['status'] = 'error'
        result['issues'].append(f'数据库文件不存在: {db_path}')
        return result
    
    result['file_exists'] = True
    result['file_size'] = db_path.stat().st_size
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查持仓数量
        cursor.execute("SELECT COUNT(*) FROM holdings")
        result['holdings_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM holdings WHERE status = 'active'")
        result['active_holdings'] = cursor.fetchone()[0]
        
        # 检查最后更新时间
        cursor.execute("SELECT MAX(updated_at) FROM holdings")
        last_update = cursor.fetchone()[0]
        
        if last_update:
            result['last_update'] = last_update
            # 计算距今天数
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
        
        if result['active_holdings'] == 0:
            result['issues'].append('无活跃持仓')
            result['status'] = 'warning'
        
        if result['status'] == 'unknown':
            result['status'] = 'ok'
            
    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f'数据库查询失败: {str(e)}')
    
    return result

def check_python_env() -> Dict[str, Any]:
    """检查 Python 环境"""
    result = {
        'status': 'ok',
        'python_version': sys.version,
        'python_path': sys.executable,
        'missing_modules': [],
        'issues': []
    }
    
    # 检查必需模块
    required_modules = ['yaml', 'requests', 'sqlite3']
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            result['missing_modules'].append(module)
            result['status'] = 'error'
            result['issues'].append(f'缺少模块: {module}')
    
    # 检查 Python 路径
    if '/opt/anaconda3/bin/python' not in sys.executable:
        result['issues'].append(f'非 Anaconda Python: {sys.executable}')
        result['status'] = 'warning'
    
    return result

def check_output_files() -> Dict[str, Any]:
    """检查输出文件"""
    result = {
        'status': 'ok',
        'reports_dir_exists': False,
        'logs_dir_exists': False,
        'recent_reports': [],
        'issues': []
    }
    
    reports_dir = PROJECT_ROOT / 'reports'
    logs_dir = PROJECT_ROOT / 'logs'
    
    result['reports_dir_exists'] = reports_dir.exists()
    result['logs_dir_exists'] = logs_dir.exists()
    
    if not result['reports_dir_exists']:
        result['issues'].append('reports 目录不存在')
        result['status'] = 'warning'
    else:
        # 检查最近 7 天的报告
        seven_days_ago = datetime.now() - timedelta(days=7)
        for report_file in reports_dir.glob('news_report_*.md'):
            mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
            if mtime > seven_days_ago:
                size = report_file.stat().st_size
                result['recent_reports'].append({
                    'file': report_file.name,
                    'size': size,
                    'date': mtime.strftime('%Y-%m-%d')
                })
    
    return result

def generate_report(checks: Dict[str, Dict]) -> str:
    """生成健康检查报告"""
    lines = []
    lines.append("# Invest OS 健康检查报告")
    lines.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("\n---\n")
    
    # 总体状态
    all_statuses = [c['status'] for c in checks.values()]
    if 'error' in all_statuses:
        overall = '❌ 错误'
    elif 'warning' in all_statuses:
        overall = '⚠️ 警告'
    else:
        overall = '✅ 正常'
    
    lines.append(f"## 总体状态: {overall}\n")
    
    # 各项检查
    for check_name, check_result in checks.items():
        status_icon = {'ok': '✅', 'warning': '⚠️', 'error': '❌', 'unknown': '❓'}
        icon = status_icon.get(check_result['status'], '❓')
        
        lines.append(f"### {icon} {check_name}")
        lines.append(f"**状态**: {check_result['status']}")
        
        # 输出详细信息
        for key, value in check_result.items():
            if key in ['status', 'issues']:
                continue
            if isinstance(value, list) and len(value) > 0:
                lines.append(f"- **{key}**: {len(value)} 项")
            elif value is not None:
                lines.append(f"- **{key}**: {value}")
        
        # 输出问题
        if check_result['issues']:
            lines.append("\n**问题**:")
            for issue in check_result['issues']:
                lines.append(f"- {issue}")
        
        lines.append("")
    
    return '\n'.join(lines)

def main():
    print("========================================")
    print("Invest OS 健康检查")
    print("========================================")
    print()
    
    checks = {}
    
    print("[1/4] 检查 .env 配置...")
    checks['ENV 配置'] = check_env_config()
    
    print("[2/4] 检查数据库...")
    checks['数据库'] = check_database()
    
    print("[3/4] 检查 Python 环境...")
    checks['Python 环境'] = check_python_env()
    
    print("[4/4] 检查输出文件...")
    checks['输出文件'] = check_output_files()
    
    # 生成报告
    report = generate_report(checks)
    
    # 输出到文件
    output_file = PROJECT_ROOT / 'health_check_report.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print()
    print(f"✅ 报告已生成: {output_file}")
    print()
    print("========================================")
    print(report)
    
    # 返回状态码
    all_statuses = [c['status'] for c in checks.values()]
    if 'error' in all_statuses:
        sys.exit(1)
    elif 'warning' in all_statuses:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
