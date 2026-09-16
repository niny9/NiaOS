---
name: weekly-optimize
description: 运行投资驾驶舱的周度参数优化任务
---

运行周度参数优化任务，自动优化策略参数。

```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"
python3 scripts/weekly_optimization.py
```

功能：
- 检测当前市场制度（牛市/熊市/震荡市）
- 根据市场制度定义参数搜索空间
- 使用最近3个月数据进行参数优化
- 对比当前参数和优化后参数的表现
- 如果提升显著（夏普比率 > 0.2），自动切换参数
- 发送优化结果到飞书
