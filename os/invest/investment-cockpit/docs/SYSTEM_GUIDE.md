# 投资驾驶舱系统使用文档

> 文档目标：汇总当前代码库（MVP Week-4）的真实状态，提供可执行的日常使用手册。
> 项目目录：`/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit`

## 1. 系统概述

投资驾驶舱是一个本地运行的 A 股 AI 产业链研究与决策支持系统，核心能力覆盖：
- 数据获取与增量更新（股票基础信息、个股/指数日线）
- 因子计算与多策略评分（短线/波段/稳健）
- 风控检查与信号筛选
- 真实持仓管理 + 模型组合跟踪
- 每日日报/每周复盘自动生成
- 飞书通知与多维表格同步
- Obsidian 知识库沉淀

技术栈：Python 3.9+、SQLite、Pandas、AKShare、PyYAML、Requests。

架构分层（代码目录）：
- `src/data_ingestion`：行情与基础数据拉取
- `src/universe`：AI 产业链股票池管理
- `src/factors`：趋势/动量/成交量因子
- `src/scoring`：三策略评分 + `daily_signals` 写入
- `src/risk`：仓位、止损、流动性、追高风险检查
- `src/portfolio`：真实持仓/交易同步/模型组合/回测
- `src/reporting`：日报、新闻简报、周度复盘、Obsidian 导出
- `src/integrations`：飞书 Webhook 与 Bitable 同步
- `scripts`：可执行入口（每日、午间、周度、初始化等）

## 2. 已完成功能

### 2.1 数据与股票池
- `stock_basic` 增量更新
- AI 产业链种子股票池初始化与维护（`watchlist`）
- 个股日线批量更新（失败隔离）
- 指数日线更新（写入 `stock_daily_bar`，代码形如 `INDEX:*`）

### 2.2 因子与策略
- 趋势因子（MA/趋势分）
- 动量因子（多周期动量/相对强弱）
- 成交量因子（成交额、量比、资金强度）
- 三类策略评分：短线、波段、稳健
- 每日信号落库：`daily_signals`

### 2.3 风控
- 单票仓位限制
- 行业集中度检查
- 止损触发检查
- 高位追涨与流动性检查
- 风险等级输出（用于报告）

### 2.4 持仓、交易与复盘
- 真实持仓管理（CRUD、盈亏、仓位）
- 交易同步（交互录入、批量导入、撤销）
- 模型组合（短线/波段/稳健三组合）
- 周度复盘分析与归因

### 2.5 输出与集成
- 每日日报 Markdown 生成
- 周度复盘 Markdown 生成
- Obsidian 自动导出与总览更新
- 飞书群 Webhook 文本通知
- 飞书多维表格增量同步（含本地 hash 状态表）

## 3. 数据流程

完整流程（从数据获取到报告生成）：

1. 初始化连接与配置
- 读取 `.env` 与 YAML 配置
- 建立 SQLite 连接（默认 `data/database/investment.db`）

2. 数据更新（`scripts/update_data.py`）
- 更新 `stock_basic`
- 初始化/更新 `watchlist`
- 拉取股票池行情到 `stock_daily_bar`
- 拉取指数行情到 `stock_daily_bar`
- 计算因子并写入 `factor_scores`
- 输出更新日志 `logs/update_data_*.json`

3. 每日主流程（`scripts/daily_task.py`）
- 可达性检查通过后执行 `run_update`
- 重新计算最新交易窗口因子（增量 upsert）
- 拉取持仓相关新闻并生成 `reports/news_report_YYYY-MM-DD.md`
- 三策略评分并写入 `daily_signals`
- 风控检查并生成投资日报
- 导出日报到 Obsidian
- 同步到飞书（持仓/交易/信号/股票池）
- 发送飞书群日报通知（Webhook）
- 输出执行摘要 `logs/daily_task_*.json`

4. 周度流程（`scripts/weekly_task.py`）
- 基于 `daily_signals` 驱动模型组合按日调仓
- 生成周度复盘与归因报告
- 同步周度复盘到飞书
- 输出执行摘要 `logs/weekly_task_*.json`

## 4. 定时任务（launchd：早盘 / 午盘 / 晚盘）

当前状态：
- 仓库内已有 `com.investment-cockpit.daily.plist`，默认 16:00 执行 `scripts/daily_task.py`（晚盘）。
- 早盘、午盘脚本已存在（`scripts/morning_task.py`、`scripts/midday_task.py`），但对应独立 plist 需自行在 `~/Library/LaunchAgents/` 新增。

建议三任务：
- 早盘：09:00 运行 `scripts/morning_task.py`
- 午盘：12:30 运行 `scripts/midday_task.py`
- 晚盘：16:00 运行 `scripts/daily_task.py`

配置要点（每个 plist 都应包含）：
- `ProgramArguments`：使用 `/bin/zsh -c`，先 `cd` 项目目录，再 `source .venv/bin/activate`，再执行脚本
- `StandardOutPath` / `StandardErrorPath`：写入 `logs/`
- `StartCalendarInterval`：设置对应小时分钟

加载命令：
```bash
launchctl load ~/Library/LaunchAgents/com.investment-cockpit.morning.plist
launchctl load ~/Library/LaunchAgents/com.investment-cockpit.midday.plist
launchctl load ~/Library/LaunchAgents/com.investment-cockpit.daily.plist
```

查看状态：
```bash
launchctl list | grep investment-cockpit
```

注意：`midday_task.py` 当前查询的是 `strategy_signals/stocks` 老表名，和现有 `daily_signals/watchlist/stock_basic` 不一致，需修正后再长期启用午盘自动任务。

## 5. 手动运行

### 5.1 初始化
```bash
python scripts/init_database.py
```

### 5.2 数据更新与日报
```bash
python scripts/update_data.py
python scripts/daily_task.py
```

### 5.3 早盘 / 午盘 / 晚盘
```bash
python scripts/morning_task.py
python scripts/midday_task.py
python scripts/daily_task.py
```

### 5.4 持仓与交易
```bash
python scripts/init_portfolio.py --file data/init_positions.json
python scripts/sync_trade.py
python scripts/sync_trade.py --import trades.json
python scripts/sync_trade.py --undo
python scripts/view_portfolio.py
python scripts/update_positions_price.py
```

### 5.5 周度复盘
```bash
python scripts/weekly_task.py
python scripts/weekly_task.py --start 2026-05-19 --end 2026-05-25 --week "2026年第21周"
```

### 5.6 飞书检查
```bash
python scripts/init_feishu.py
python scripts/test_feishu_integration.py
python scripts/diagnose_feishu_fields.py
```

### 5.7 验证与测试
```bash
python scripts/validate_week2.py
python -m unittest discover -s tests -v
```

## 6. 飞书集成

飞书集成包含两部分：

1) Webhook 通知（群消息）
- 配置项：`FEISHU_WEBHOOK_URL`
- 调用位置：`scripts/daily_task.py` 中 `FeishuNotifier.send_daily_report()`
- 作用：发送当日简报摘要到群

2) 多维表格同步（Bitable）
- 配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_BITABLE_APP_TOKEN`
- 首次初始化：`python scripts/init_feishu.py`
- 日常同步：
  - 每日任务同步：`real_positions`、`real_trades`、`daily_signals`、`watchlist`
  - 每周任务同步：`weekly_review`
- 增量机制：使用 `feishu_sync_state` 记录 `logical_table + unique_key + row_hash`，内容不变则跳过

推荐排查顺序：
1. 校验 `.env` 凭证
2. 运行 `python scripts/test_feishu_integration.py`
3. 查看 `logs/daily_task_*.json` / `logs/weekly_task_*.json` 中 `feishu_sync`

## 7. 文件结构

重要目录：
- `src/`：核心业务代码
- `scripts/`：任务入口
- `data/database/`：SQLite 数据库文件
- `reports/`：中间报告（如新闻报告）
- `obsidian/01_每日简报/`：每日投资日报
- `obsidian/05_交易复盘/`：周度复盘报告
- `logs/`：任务日志与执行摘要 JSON
- `docs/`：项目文档

关键文件：
- `README.md`：项目说明与主流程
- `QUICKSTART.md`：上手与常见操作
- `PROJECT_SUMMARY.md`：开发里程碑与模块总览
- `com.investment-cockpit.daily.plist`：现有晚盘 launchd 配置
- `.env.example`：环境变量模板

## 8. 下一步计划

建议优先级（按当前代码状态）：

1. 修复午盘任务
- 将 `scripts/midday_task.py` 从老表结构迁移到当前 `daily_signals` 数据模型
- 增加单元测试，确保午盘建议可稳定生成

2. 补齐三段 launchd 配置
- 新增 `morning` / `midday` plist 文件并版本化管理
- 为三段任务增加独立日志文件与健康检查

3. 强化数据与策略层
- 落地新闻/公告结构化入库（`news_events` 当前为预留）
- 增加基本面与行业景气度评分，减少默认分占比

4. 完善复盘与评估
- 扩展模型 vs 实盘偏离统计指标
- 补充更多回测约束（停牌、涨跌停、滑点动态化）

5. 工程化提升
- 增加端到端回归测试（每日/周度任务）
- 建立告警机制（任务失败自动通知）
- 统一文档与代码中的表结构命名，消除历史兼容歧义
