# Invest OS 测试结果报告

生成时间：2026-05-31
工作目录：`investment-cockpit`
执行模式：`fullAuto: true`

## 1. 测试执行结果（4项）

| 测试项 | 执行命令 | 结果 | 证据 |
|---|---|---|---|
| 飞书通知测试 | `python3 scripts/test_feishu_bot.py` | ✅ 成功 | 用户已确认“通知发送成功”；历史 `daily_task` 日志也显示 `feishu_bot_notify_sent: true` |
| 完整日报流程（晚盘） | `python3 scripts/trading_day_evening.py` | 🔄 状态待确认（沙箱限制） | `ps/pgrep` 在当前环境无权限；`logs/daily_task.log` 仅见 `2026-05-31 00:03:28 | Daily task started`，未见对应 `daily_task_*.json` 新文件 |
| 周报生成 | `python3 scripts/weekend_signal_report.py` | ✅ 成功 | `logs/weekend_signal_report_20260531_000617.json` 存在，且 `obsidian/02_周报/2026-22_投资周报.md` 更新时间为 May 31 00:06 |
| Cron 安装 | `python3 scripts/setup_cron.py` | ✅ 成功（按用户反馈） | 用户已确认“7个任务已安装”；任务定义见 `scripts/setup_cron.py` |

## 2. 晚盘任务状态检查

执行命令：
- `ps aux | grep "trading_day_evening.py" | grep -v grep`

结果：
- 当前沙箱环境限制系统进程读取（`operation not permitted: ps`），无法直接确认进程是否仍在运行。
- 备用检查 `pgrep -fl trading_day_evening.py` 同样受限（`Cannot get process list`）。

基于日志的间接结论：
- `logs/daily_task.log` 最新包含 `2026-05-31 00:03:28 | Daily task started`。
- 未发现 2026-05-31 对应的 `logs/daily_task_*.json` 完成记录。
- 因此当前应标记为“运行状态无法在沙箱内直接确认，需在本机终端复核”。

## 3. 任务输出检查

### 3.1 daily_task JSON（最近10分钟）
- 命令 `find logs/ -name "daily_task_*.json" -type f -mmin -10 | sort | tail -1` 返回空。
- 最新可见文件：`logs/daily_task_20260529_135637.json`。

### 3.2 最新日报
- 目录：`obsidian/01_每日简报/`
- 最新文件：`2026-05-29_AI产业链投资日报.md`（May 30 14:09，2.7K）

### 3.3 最新新闻报告
- 目录：`reports/`
- 最新文件：`news_report_2026-05-29.md`（May 30 14:09，61B）

### 3.4 最新周报
- 目录：`obsidian/02_周报/`
- 最新文件：`2026-22_投资周报.md`（May 31 00:06，1.9K）

## 4. 飞书通知状态

| 通知类型 | 状态 | 依据 |
|---|---|---|
| 飞书 Bot 主动通知 | ✅ 成功 | 用户手工测试成功；`daily_task_20260529_135637.json` 中 `feishu_bot_notify_sent: true` |
| 飞书 Bitable 同步通知 | ⚠️ 未成功 | `daily_task_20260529_135637.json` 中 `feishu_bitable_sync_notify_sent: false` |
| 飞书通用通知字段 | ⚠️ 未成功 | `daily_task_20260529_135637.json` 中 `feishu_notify_sent: false` |

## 5. Cron 任务列表（7项）

来源：`scripts/setup_cron.py` 中 `JOBS`

1. `15 9 * * 1-5` `scripts/trading_day_morning.py`
2. `30 12 * * 1-5` `scripts/trading_day_noon.py`
3. `0 20 * * 1-5` `scripts/trading_day_evening.py`
4. `0 20 * * 6,0` `scripts/holdings_news_daily.py`
5. `0 21 * * 1-5` `scripts/monitor_parameters.py`
6. `0 21 * * 0` `scripts/weekend_signal_report.py`
7. `0 22 * * 0` `scripts/weekly_optimization.py`

备注：当前沙箱无法执行 `crontab -l`，以上为脚本定义与用户安装反馈的交叉确认。

## 6. 数据状态汇总

| 数据项 | 当前状态 | 依据 |
|---|---|---|
| 日报 | ✅ 已生成（最新为 2026-05-29） | `obsidian/01_每日简报/2026-05-29_AI产业链投资日报.md` |
| 周报 | ✅ 已生成（第22周） | `obsidian/02_周报/2026-22_投资周报.md` + `logs/weekly_report_20260531_000617.json` |
| 信号总数（周报口径） | ✅ 18 条 | `weekly_report_20260531_000617.json.metrics.signal_count=18` |
| 信号胜率（周报口径） | ⚠️ 11.11% | `weekly_report_20260531_000617.json.metrics.signal_win_rate=0.1111` |
| 最新日报信号数（日报口径） | ⚠️ 0 条 | `daily_task_20260529_135637.json.signal_count=0` |

## 7. 已知问题

1. `industry` 字段问题
- 现象：`KeyError: "['industry'] not in index"`
- 位置：`logs/update_data.log`（2026-05-30 14:08:22）
- 影响：`update_data` 的 `stock_basic` 步骤失败，可能导致基础信息字段不完整。

2. `signal performance` 更新问题
- 现象：`Signal performance update failed: no such column: t.code`
- 位置：`logs/daily_task.log` 多次出现
- 影响：信号绩效跟踪表更新失败，影响策略胜率与回测闭环质量。

## 8. 下一步建议

1. 在本机终端执行一次：
   - `ps aux | grep "trading_day_evening.py" | grep -v grep`
   - `crontab -l | sed -n '/investment-cockpit automation/,$p'`
2. 修复 `fetch_stock_basic.py` 对 `industry` 字段的列选择兼容逻辑（对缺列做回退映射）。
3. 修复 `update_signal_performance.py` 中 `t.code` 列引用，与实际表结构对齐后补跑一次晚盘任务。
4. 补充一次端到端回归：`trading_day_evening.py` 完整跑通并生成新的 `daily_task_*.json`（含 `finished_at`）。
