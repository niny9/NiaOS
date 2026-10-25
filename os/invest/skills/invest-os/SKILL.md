---
name: invest-os
description: NIA Invest OS 统一投资工作流入口，将既有量化闭环、五类投资对账、中金财富数据源与 Wealth OS 及行为、日志、评测、机会和同花顺交接模块协同运行。用于完整投资早报、持仓研究、财富与投资复盘、工作流检查和新旧投资能力融合。
---

# Invest OS 统一工作流

一个工作流、一个 run_id、一个人工决策出口。以 [workflow.json](references/workflow.json) 为模块注册表，沿用现有投资引擎和数据适配器；不复制第二套量化、对账或调度系统。执行器是当前 Agent，Python 助手负责发现、预检、任务分派和结果验收，不冒充独立 LLM 服务。

## 进入流程

1. 读 [能力与产物映射](references/capabilities.md)，确定当前任务和私有绑定路径。只要请求是完整投资/财富流程，从此入口开始；单查行情仍直接用原数据 Skill。
2. 执行 `python3 scripts/invest_workflow.py prepare --bindings PRIVATE_BINDINGS --as-of ISO时间 --max-age-hours N --probe-quant`。路径相对本 Skill。如只检查接线，可省略 bindings 和 probe；缺绑定会明确显示 unavailable，不建假数据。
3. 保存返回的 work order 到私有运行目录。它列出实际找到的 Skill 路径、版本哈希、依赖、输入快照状态，以及尚未执行的任务。`ready_for_agent` 只表示可开始处理，绝不意味着数据或分析已经通过。
4. 按 `tasks` 顺序读取 `skill_file`，给该模块传入 `orchestration_context=invest-os.stage`、run_id、任务输入和上游产物。需取数时再读 `provider_files` 对应 Skill，优先复用其已有脚本和返回结构。依赖顺序不得打乱；不要求拆成多代理，默认当前 Agent 串行完成，避免重复取数和额外调度。

## 执行任务

v1.8 新增 `journal`、`handoff`、`behavior`、`evaluation`、`opportunities` 五阶段；按注册表 14 阶段顺序执行。详情读各任务的 owner Skill，八项需求映射见 [v1.8 集成清单](references/v1.8-integration.md)。调用云端/Work/同花顺前读 [环境调用说明](references/invocation.md)。

- `holdings`：核验当前账户快照；缺数据形成 blocked 产物，公开研究仍继续。
- `market`：由市场情报模块按需调用中金财富行情/资讯/ETF/基金来源并联网核验官方资料。
- `quant`：由 finance-quant 提供行情、因子、样本与衰减、混合建议和风险证据。预检只执行 `status`。实际刷新需属于本轮研究授权且检查旧脚本副作用；只用其计算模式，不自动复用通知、Base 写回、模拟成交或自动化创建步骤。缺源就标 degraded。
- `reconciliation`：由原 investment-workflow 提供五类对账，财报数据可用中金财富财务模块，龙虎榜只用于相关异常事件。没有目标股票或论点时可 skipped，写原因。不得照抄旧示例数字；旧 runner 会写库，先检查路径与输入，缺证据不生成“未发现异常”。
- `diagnosis`：融合 holdings、market、quant、reconciliation。主观与量化冲突分别展示，不平均成确定信号；样本不足的量化结论不放大仓位。
- `risk`：用新仓位/回撤模块检查用户真实组合，同时保留旧量化风险结果；旧风险通过不能替代家庭现金或用户限额检查。
- `goals`：读取私有 2026–2032 目标与资产负债事实，逐项目标分别按金融资产、全部净资产或账户收益跟踪。
- `trade_plan`：只消费通过数据和风险检查的证据，输出 proposed 条件预案。缺持仓/规则/政策时 quantity 和 amount_cny 保持 null。
- `brief`：调用每日简报模块汇总同一 run 的产物，生成唯一主报告，缺项如实披露。

新阶段输出须含：journal 的 `signals_reviewed`/`trades_reviewed`（未知 null）；handoff 的 `connection_status`（manual_copy/verified_export/unavailable）；behavior 的 `gate`；evaluation 的 `reviews`；opportunities 的 `comparisons`（六类）及 `reallocation`。不把未发现日志等同没有交易。

各模块产物按 [结果契约](references/results.md) 保存为 `stage_id.json`，不改旧账本。调用每日简报或 finance-quant 时传上述 context，阻止它们重新启动此总流程。finance-quant 的细分系统诊断、原对账任务仍可独立使用。

## 收口与边界

用 `python3 scripts/invest_workflow.py check-results --plan WORK_ORDER --results-dir RUN_DIR` 验收 run_id、输入哈希、Skill 版本、阶段完整性和门禁。结构验收不能证明行情或事实真实；完成状态同时包含来源质量。执行失败/无证据的模块保持 blocked/degraded，不能用“文件存在”宣称完整投资闭环。

本流程不创建、不恢复任何自动化，不自动发送外部消息，不下单，不记录未确认交易。旧 `invest_pre_market_runner.py` 含固定建议模板，不能作为本工作流的数据源或决策入口。已存在的 ChatGPT 云端任务仍需其实际运行环境读取本工作流；本机安装回执不代表云端已加载。
