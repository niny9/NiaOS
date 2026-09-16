# Invest OS README（用于 `/Assets/Invest OS/README.md`）

> 说明：当前执行环境不允许写入 `../README.md`，本文件为可直接落位到 `/Assets/Invest OS/README.md` 的正式内容。

## 1) Invest OS 职责
- 管理 AI 产业链投资研究与交易执行支持。
- 产出每日/每周投资报告、交易复盘、参数优化结论。
- 同步核心结果到飞书（机器人通知 + 多维表格）。

## 2) 数据结构
- 代码与运行数据：`investment-cockpit/`
- 建议资产层结构（迁移目标）：`holdings/`、`market_signals/`、`news/`、`reports/`、`strategy/`、`logs/`
- SQLite：`investment-cockpit/data/investment.db`（当前 `.env` 指向 `data/investment.db`）

## 3) 工作日任务频率（交易日）
- 09:15 `scripts/trading_day_morning.py`：更新持仓价格 + 更新行情 + 飞书早盘信号
- 12:30 `scripts/trading_day_noon.py`：午盘决策提示 + 飞书午盘通知
- 20:00 `scripts/trading_day_evening.py`：日终全流程（数据、信号、日报、飞书同步）
- 21:00 `scripts/monitor_parameters.py`：参数劣化监控

## 4) 非交易日任务频率
- 20:00 `scripts/holdings_news_daily.py`：持仓/观察池新闻汇总
- 周日 21:00 `scripts/weekend_signal_report.py`：周报
- 周日 22:00 `scripts/weekly_optimization.py`：周度参数优化

## 5) 输出路径
- 每日简报：`investment-cockpit/obsidian/01_每日简报/`
- 周报：`investment-cockpit/obsidian/02_周报/`
- 参数优化：`investment-cockpit/obsidian/03_参数优化/`
- 交易复盘：`investment-cockpit/obsidian/05_交易复盘/`
- 新闻报告：`investment-cockpit/reports/news_report_*.md`
- 执行日志：`investment-cockpit/logs/*.json|*.log`

## 6) 飞书群机器人配置
- `.env` 当前字段：`FEISHU_WEBHOOK_URL`、`FEISHU_BOT_WEBHOOK`
- 当前状态：两项为空，`FEISHU_APP_ID/SECRET/BITABLE_TOKEN` 也为空，默认无法确认已路由到 Invest OS 专用群。
- 建议：
- 新增 `FEISHU_BOT_NAME=INVEST_OS`
- 新增 `FEISHU_CHAT_SCOPE=invest-os-only`
- 将 Market OS / Product OS 使用独立 webhook，避免串群。

## 7) Skill / Workflow / Cron 对应关系
- Skill（业务能力）：
- `daily_task.py`（日报主流程）
- `weekly_report.py`（周报）
- `holdings_news_daily.py`（持仓新闻）
- `monitor_parameters.py`（参数监控）
- Workflow（任务编排入口）：
- `trading_day_morning.py` -> `morning_task.py`
- `trading_day_noon.py` -> `midday_task.py`
- `trading_day_evening.py` -> `daily_task.py`
- `weekend_signal_report.py` -> `weekly_report.py`
- Cron（安装脚本）：
- `scripts/setup_cron.py`

## 8) 已跑通 / Pending
- 已跑通（有产物）：
- 日报：`2026-05-27/28/29`
- 周报：`2026-22_投资周报.md`
- 参数优化报告：`2026-05-26/27/29`
- Pending / 风险项：
- 飞书配置未实填（目前不可确认是否成功发送）
- 周报样本覆盖不足（`daily_signals` 仅 2026-05-28/29 两天）
- 目录尚未从 `investment-cockpit/obsidian/` 迁移到资产层结构
