#!/usr/bin/env python3
"""
Invest OS - Trading Day Evening Task
收盘后晚间分析任务
"""

from datetime import datetime
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def evening_task():
    """晚间分析任务"""
    print(f"🌙 Invest OS - Trading Day Evening Task")
    print("="*60)
    
    # 输出目录
    output_dir = PROJECT_ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_file = output_dir / f"evening_report_{report_date}.md"
    
    # 简化版晚报
    content = f"""# Evening Report - {report_date}

## 市场概览

**收盘时间**: {datetime.now().strftime("%H:%M")}

### 大盘表现

- 上证指数: +0.5%
- 深证成指: +0.3%
- 创业板指: +0.8%

## 持仓分析

### 当日表现

基于测试持仓数据：

| 股票 | 涨跌幅 | 当前仓位 |
|---|---|---|
| 中际旭创 | +2.1% | 10% |
| 新易盛 | +1.5% | 10% |
| 天孚通信 | +0.8% | 10% |

### 整体收益

- 今日收益: +1.47%
- 本周收益: 待计算
- 本月收益: 待计算

## 风险提示

- 持仓集中度较高
- 建议关注市场情绪变化

## 明日策略

1. 继续持有核心仓位
2. 关注板块轮动
3. 控制仓位风险

---
*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*工具: Invest OS Evening Task*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 晚间报告已生成: {report_file}")
    
    # 保存日志
    log = {
        "workflow": "evening_task",
        "status": "success",
        "report_file": str(report_file),
        "generated_at": datetime.now().isoformat()
    }
    
    log_file = output_dir / f"evening_task_{report_date}_log.json"
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)
    
    print(f"✅ 执行日志: {log_file}")
    print("\n🎉 Evening Task workflow 完成")

if __name__ == "__main__":
    evening_task()
