# Invest OS 目录迁移计划（仅规划，不执行移动）

## 目标结构
```text
/Assets/Invest OS/
├── README.md
├── holdings/
├── market_signals/
├── news/
├── reports/
│   ├── daily/
│   ├── weekly/
│   └── optimization/
├── strategy/
├── logs/
└── investment-cockpit/
    ├── scripts/
    ├── src/
    └── data/
```

## 当前内容映射
- `investment-cockpit/obsidian/00_总览/*` -> `strategy/`（总览与策略说明）
- `investment-cockpit/obsidian/01_每日简报/*` -> `reports/daily/`
- `investment-cockpit/obsidian/02_周报/*` -> `reports/weekly/`
- `investment-cockpit/obsidian/03_参数优化/*` -> `reports/optimization/`
- `investment-cockpit/obsidian/05_交易复盘/*` -> `reports/weekly/`（复盘类）
- `investment-cockpit/reports/news_report_*` -> `news/`
- `investment-cockpit/reports/investment_report_*` -> `reports/daily/`
- `investment-cockpit/logs/*` -> `logs/`
- `investment-cockpit/data/*` 保持在代码目录（运行数据）

## 分阶段迁移（建议）
1. 先创建新目录骨架，不移动文件。
2. 修改脚本输出路径参数，支持“旧路径 + 新路径”双写一周。
3. 校验飞书通知中的报告链接是否已指向新路径。
4. 双写稳定后，批量迁移历史文档。
5. 再切换到仅新路径输出，旧路径保留 2~4 周后归档。

## 建议迁移命令（暂不执行）
```bash
mkdir -p "../holdings" "../market_signals" "../news" "../reports/daily" "../reports/weekly" "../reports/optimization" "../strategy" "../logs"

# 仅示例：真正执行前先 dry-run
rsync -avhn "obsidian/01_每日简报/" "../reports/daily/"
rsync -avhn "obsidian/02_周报/" "../reports/weekly/"
rsync -avhn "obsidian/03_参数优化/" "../reports/optimization/"
rsync -avhn "obsidian/05_交易复盘/" "../reports/weekly/"
rsync -avhn "reports/" "../news/"
rsync -avhn "logs/" "../logs/"
```

## 风险与回滚
- 风险：Obsidian 链接失效、飞书消息内路径变更、脚本硬编码路径。
- 回滚：保留旧路径不删；若新路径异常，切换脚本回旧路径输出即可。
