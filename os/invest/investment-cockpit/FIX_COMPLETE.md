# Invest OS 数据问题修复报告（最终验收）

## 执行时间
- 执行日期：2026-05-31
- 工作目录：`/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit`

## 已修复问题

### 1) `industry` 字段缺失（KeyError）
- 文件：`src/data_ingestion/fetch_stock_basic.py`
- 问题：AKShare 返回列可能缺失 `industry`，最终列选择时触发 `KeyError: "['industry'] not in index"`
- 修复：
  - 在 `spot_use` 构建后增加缺省列：`industry=''`
  - 在 `merge` 后再次兜底：若无 `industry` 列则创建，并统一 `fillna('')`
- 结果：字段缺失时不再报错，能稳定返回目标列集。

### 2) `signal performance` 结构问题（历史 `t.code` / 当前表结构不匹配）
- 文件：`scripts/update_signal_performance.py`
- 问题：历史日志中有 `no such column: t.code`；同时当前插入逻辑与 `signal_performance_tracking` 表结构不一致（`signal_id`、`date` 为 NOT NULL 但未写入）
- 修复：
  - 新信号查询改为 `SELECT s.id AS signal_id ...`
  - 关联条件改为 `LEFT JOIN signal_performance_tracking t ON t.signal_id = s.id`
  - 插入列补齐：`signal_id, date, signal_date, ...`
- 结果：消除 `t.code` 路径和主键关联错位，插入逻辑与表结构一致。

### 3) 晚盘链路新增结构问题（验收中发现）
- 文件：`src/integrations/performance_sync.py`
- 问题：查询了不存在列 `signal` / `final_return`，而表中实际为 `strategy_type` / `exit_return`
- 修复：
  - SQL 选择列改为 `strategy_type, exit_return`
  - 映射字段与唯一键改为使用 `strategy_type` 和 `exit_return`
- 结果：晚盘任务不再因 `no such column: signal` 中断。

## 备份文件
- `src/data_ingestion/fetch_stock_basic.py.bak_20260531`
- `scripts/update_signal_performance.py.bak_20260531`
- `src/integrations/performance_sync.py.bak_20260531`
- `src/integrations/performance_sync.py.bak_20260531_v2`

## 紧急复核（V2）
- 复核日期：2026-05-31
- 背景：后台任务再次报告 `sqlite3.OperationalError: no such column: signal`（`src/integrations/performance_sync.py` line 29）
- 执行项：
  - 全量检查 `src/integrations/performance_sync.py` 的 SQL 与映射字段（`sync_signal_performance` / `sync_daily_strategy_performance`）
  - 复核表结构：
    - `signal_performance_tracking`：确认存在 `strategy_type`、`exit_return`，不存在 `signal`、`final_return`
    - `daily_strategy_performance`：确认使用 `strategy_type`
  - 复跑：`python3 scripts/trading_day_evening.py`
- 结果：
  - 当前 `src/integrations/performance_sync.py` 已全部使用正确列名（`strategy_type`、`exit_return`），未发现残留 `signal`/`final_return` 查询
  - 晚盘任务本次运行退出码 `0`，未复现 `no such column: signal`
  - 当前失败项仅为外部网络 DNS（行情与飞书），非列名问题

## 测试与验收结果

### A. 代码级测试
- 命令：
  - `python3 -c "... StockBasicFetcher ..."`
- 结果：`Test passed`

### B. 信号表现脚本测试
- 命令：`python3 scripts/update_signal_performance.py`
- 结果：代码逻辑可运行到行情拉取阶段；未出现 `t.code`/列结构错误。
- 阻塞：当前环境 DNS 无法解析 `82.push2.eastmoney.com`，导致行情请求失败。

### C. 晚盘任务最终验收
- 命令：`python3 scripts/trading_day_evening.py`
- 结果：任务完成（退出码 0），不再出现 `t.code` 或 `signal` 列错误。
- 日志关键点：
  - `Daily task finished summary=...`
  - `signal_performance` / `strategy_performance` 同步流程已执行
- 产物检查：
  - 日报存在并刷新时间更新：`obsidian/01_每日简报/2026-05-29_AI产业链投资日报.md`
- 未满足项：
  - 未生成新的 `logs/daily_task_*.json`（目录最新仍为 2026-05-29）
  - 飞书通知发送失败（`open.feishu.cn` DNS 解析失败）

## 修复前后对比（摘要）
- 修复前：存在 `industry` 缺列崩溃风险；晚盘链路出现 `t.code` / `signal` 列错误。
- 修复后：上述结构性数据错误已修复；晚盘流程在离线网络条件下可走完本地任务主链路。

## 最终验收结论
- 结论：**代码层数据结构问题已完成修复并通过本地验收**。
- 剩余阻塞：**外部网络 DNS 不可达**（行情源与飞书），导致实时价格更新与飞书通知无法完成；这属于环境问题，不属于本次代码缺陷。
