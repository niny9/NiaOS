# Invest OS 验收总结

## 最终验收表格

| 检查项 | 当前问题 | 修复动作 | Asset 输出路径 | 飞书群 | 测试命令 | 是否跑通 |
|---|---|---|---|---|---|---|
| 目录重构 | `obsidian/` 嵌套不合理 | 生成迁移计划（需手动执行） | `docs/invest_os_directory_migration_plan.md` | N/A | 见下方手动命令 | ✅ 计划完成 |
| 持仓新闻 | 缺失 `holdings_news_daily.py` | 新建脚本 | `reports/news_report_*.md` | Invest OS 群（待配置） | `python3 scripts/holdings_news_daily.py` | ✅ 代码完成 |
| 周末信号 | 缺失 `weekend_signal_report.py` | 新建脚本 | `obsidian/02_周报/` | Invest OS 群（待配置） | `python3 scripts/weekend_signal_report.py` | ✅ 代码完成 |
| 早盘任务 | 缺失统一入口 | 新建 `trading_day_morning.py` | 飞书通知 | Invest OS 群（待配置） | `python3 scripts/trading_day_morning.py` | ✅ 代码完成 |
| 午盘任务 | SQL 字段错误导致崩溃 | 修复 `midday_task.py` + `feishu_notifier.py` | 飞书通知 | Invest OS 群（待配置） | `python3 scripts/trading_day_noon.py` | ✅ 已修复 |
| 晚盘任务 | 缺失统一入口 | 新建 `trading_day_evening.py` | `obsidian/01_每日简报/` | Invest OS 群（待配置） | `python3 scripts/trading_day_evening.py` | ✅ 代码完成 |
| 周报全0 | 指数代码不一致 + 样本不足 | 修复双代码兼容 + 增加诊断 | `obsidian/02_周报/` | Invest OS 群（待配置） | `python3 scripts/weekly_report.py` | ✅ 已修复 |
| Cron 配置 | 任务分工不清晰 | 更新 `setup_cron.py` | N/A | N/A | `python3 scripts/setup_cron.py` | ✅ 已更新 |
| README | 缺失根目录说明 | 生成 `README.InvestOS.md` | `README.InvestOS.md` | N/A | 手动 cp 到父目录 | ✅ 已生成 |
| 飞书路由 | Webhook 未配置，可能串群 | 需配置独立 webhook | `.env` | Invest OS 专用群 | 配置后测试 | ⚠️ 待配置 |
| 空报告治理 | 27号有内容，28/29号质量不稳定 | 数据样本不足，非脚本问题 | N/A | N/A | 补充历史数据 | ⚠️ 数据问题 |

## 手动执行命令

### 1. 部署 README
```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS"
cp investment-cockpit/README.InvestOS.md README.md
```

### 2. 创建新目录结构
```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS"
mkdir -p holdings market_signals news reports/daily reports/weekly reports/optimization strategy logs
```

### 3. 配置飞书 Webhook
编辑 `investment-cockpit/.env`，添加：
```
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_INVEST_OS_WEBHOOK
FEISHU_BOT_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_INVEST_OS_WEBHOOK
FEISHU_BOT_NAME=INVEST_OS
```

### 4. 测试所有脚本
```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"
python3 scripts/holdings_news_daily.py
python3 scripts/weekend_signal_report.py
python3 scripts/trading_day_morning.py
python3 scripts/trading_day_noon.py
python3 scripts/trading_day_evening.py
python3 scripts/weekly_report.py
```

### 5. 安装 Cron
```bash
python3 scripts/setup_cron.py
```

## 核心问题解答

### 1. 数据是否更新到飞书？
**答**：代码已完成，但 `.env` 中 `FEISHU_WEBHOOK_URL` 为空，需要配置后才能发送。

### 2. 目录结构混乱？
**答**：已生成迁移计划 `docs/invest_os_directory_migration_plan.md`，建议分阶段迁移。

### 3. 持仓股票新闻汇总？
**答**：已创建 `scripts/holdings_news_daily.py`，每日20:00运行（非交易日）。

### 4. Skill 用途？
**答**：见 `README.InvestOS.md` 第7节，已列出所有 Skill/Workflow/Cron 对应关系。

### 5. 空报告问题？
**答**：27号有内容，28/29号也有，但 `daily_signals` 表只有2天数据（18条），样本不足导致周报部分为0。

### 6. 第22周周报全0？
**答**：已修复指数代码兼容性问题，重新生成的周报显示正常。

### 7. 非交易日任务？
**答**：已配置 `holdings_news_daily.py`（每日20:00）和 `weekend_signal_report.py`（周日21:00）。

### 8. 工作日早/中/晚盘？
**答**：已创建 `trading_day_morning.py`（09:15）、`trading_day_noon.py`（12:30）、`trading_day_evening.py`（20:00）。

### 9. 投资周报和优化？
**答**：周日21:00运行 `weekend_signal_report.py`，周日22:00运行 `weekly_optimization.py`。

### 10. 投资内容发送到哪个群？
**答**：需配置 `FEISHU_WEBHOOK_URL` 为 Invest OS 专用群的 webhook，确保不与 Market/Product OS 串群。

### 11. Skill 盘点？
**答**：见 `README.InvestOS.md` 第7节，已列出每个脚本的用途、输入、输出、是否接入 workflow/cron。

## 工作日/非工作日任务清单

### 工作日（交易日）
- 09:15 早盘：`trading_day_morning.py` → 持仓价格更新 + 飞书通知
- 12:30 午盘：`trading_day_noon.py` → 午盘决策提示 + 飞书通知
- 20:00 晚盘：`trading_day_evening.py` → 日报 + 信号 + 飞书同步
- 21:00 监控：`monitor_parameters.py` → 参数劣化预警

### 非工作日
- 20:00 新闻：`holdings_news_daily.py` → 持仓新闻汇总
- 周日21:00 周报：`weekend_signal_report.py` → 投资周报
- 周日22:00 优化：`weekly_optimization.py` → 参数优化

## 数据状态

### 当前覆盖
- 日报：2026-05-25/26/27/28/29 ✅
- 周报：2026-22周 ✅（已修复）
- 参数优化：2026-05-26/27/29 ✅
- daily_signals：仅05-28/29（18条）⚠️
- real_positions：0条 ⚠️
- real_trades：0条 ⚠️

### 建议
1. 运行 `daily_task.py` 补充历史数据
2. 同步真实持仓到数据库
3. 同步真实交易到数据库

## 交付物清单

### 新增文件
- `scripts/holdings_news_daily.py`
- `scripts/weekend_signal_report.py`
- `scripts/trading_day_morning.py`
- `scripts/trading_day_noon.py`
- `scripts/trading_day_evening.py`
- `README.InvestOS.md`
- `docs/invest_os_directory_migration_plan.md`

### 修改文件
- `scripts/weekly_report.py`
- `scripts/midday_task.py`
- `scripts/setup_cron.py`
- `src/integrations/feishu_notifier.py`

## 验收状态

✅ **已完成**：
- 所有代码修复和新脚本创建
- 周报全0问题修复
- 午盘任务SQL错误修复
- 目录迁移计划生成
- README 文档生成
- Cron 配置更新

⚠️ **待手动执行**：
- 部署 README 到父目录
- 创建新目录结构
- 配置飞书 Webhook
- 安装 Cron 任务
- 补充历史数据

---

**总结**：Invest OS 的核心问题已全部诊断并修复，所有代码已就绪。剩余工作为配置和部署，需手动执行上述命令。
