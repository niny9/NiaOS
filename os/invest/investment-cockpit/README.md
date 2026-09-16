# 投资驾驶舱（Investment Cockpit）

> 更新时间：2026-05-27
> 状态：生产可用（五阶段全部完成）

## 项目简介
投资驾驶舱是一个面向 A 股 AI 产业链的本地化研究与执行系统，覆盖“数据获取 -> 因子计算 -> 策略评分 -> 风控检查 -> 报告输出 -> 飞书同步 -> 参数自优化”全流程。系统支持每日自动运行、周度复盘、参数监控与优化，形成可持续自迭代闭环。

## 系统架构

```text
investment-cockpit/
├── src/
│   ├── config/            # 配置与环境管理
│   ├── database/          # SQLite 数据访问层
│   ├── data_ingestion/    # 行情/基础数据采集
│   ├── universe/          # 股票池管理
│   ├── factors/           # 技术 + 基本面/新闻/行业因子
│   ├── scoring/           # 策略评分与信号生成
│   ├── risk/              # 风险控制引擎
│   ├── portfolio/         # 真实持仓与交易管理
│   ├── optimization/      # 参数版本、优化器、制度检测
│   ├── reporting/         # 日报/周报/优化报告
│   └── integrations/      # 飞书 Webhook 与多维表格同步
├── scripts/               # 自动化任务脚本与 Skills 命令
├── data/                  # 数据与数据库
├── obsidian/              # 输出到知识库
├── reports/               # 报告产物
└── logs/                  # 运行日志
```

## 核心功能
- 每日任务流水线：数据更新、因子计算、策略评分、风控、日报生成、飞书通知。
- 三类策略体系：短线、波段、稳健统一评分与信号输出。
- 双账户机制：真实账户 + 模型账户，支持执行偏离与归因复盘。
- 参数自迭代：参数版本管理、周度优化、性能监控、自动切换。
- 参数评估方式：参数优化使用真实回测引擎（重算因子、重建信号、BacktestEngine 输出真实绩效指标）。
- 飞书协同：Webhook 文本通知 + Bitable 增量同步。
- 报告体系：日报、周报、参数优化报告、自动化日志与状态报告。

## 自动化时间表

### 工作日
- 20:00：`daily_task.py`（完整日报任务）
- 21:00：`monitor_parameters.py`（参数性能监控）

### 周末（周日）
- 21:00：`weekly_report.py`（投资周报）
- 22:00：`weekly_optimization.py`（参数优化）

> 配置来源：`scripts/setup_cron.py`

## 技术栈
- Python 3.9+
- SQLite（真实业务数据存储）
- Pandas
- AKShare（真实市场与财报数据源）
- PyYAML
- Requests（飞书接口）
- BacktestEngine（真实历史信号与价格回测评估）

## 数据真实性
- 市场数据：AKShare API 真实行情数据。
- 新闻数据：数据库 `news_report`/`news_events` 真实新闻数据。
- 基本面数据：AKShare 财报与财务指标数据。
- 行业数据：基于真实股票与真实行业分类计算。
- 回测数据：BacktestEngine 基于真实历史信号与真实价格回放。
- 持仓交易数据：数据库 `real_positions`/`real_trades` 真实交易数据。
- 结论：系统所有核心数据均为真实来源，支持比赛与实盘研究场景。

## 目录结构

```text
.
├── README.md
├── SUMMARY.md
├── PROJECT_SUMMARY.md
├── docs/
├── scripts/
│   ├── daily_task.py
│   ├── weekly_report.py
│   ├── weekly_optimization.py
│   ├── monitor_parameters.py
│   └── skills/
├── src/
├── data/
├── obsidian/
├── reports/
└── logs/
```

## 快速开始

```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_database.py
python scripts/daily_task.py
```

## 飞书配置
在 `.env` 中配置：
- `FEISHU_WEBHOOK_URL`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_BITABLE_APP_TOKEN`

初始化：

```bash
python scripts/init_feishu.py
```
