# 云端、Work 与同花顺调用

## Work / 本地 Codex

已安装后说：`使用 $invest-os，读取本工作区的私有绑定，按 v1.8 生成今日九项报告；数据缺失时降级，不更改定时任务。`

入口为仓库 `os/invest/runners/invest_os.py`。先 prepare，再由 Agent 执行 14 阶段，最后 check-results；prepare 成功只说明模块可发现。新安装 Skill 在下一轮可发现。私有绑定可包含 goals/holdings/risk、historical_baseline、handoff、behavior_profile、ai_signal_journal、actual_trade_journal、unreconciled_updates 与 trading_calendar 的文件路径；没有的填 null。

新增日志在本轮验收后归档，不能一边读取旧哈希一边改输入。只有真实核实成交才能交 holdings 对账，脚本没有交易接口。

## 既有 ChatGPT 云端任务

沿用现有 08:00 日报与交易时段小时观察，不在此处创建或改时间。GitHub 提交和本地安装不会自动改变云端提示词，也不会让云端读取电脑路径。

待用户要核对/更新既有任务时，给该任务可访问的**已核实 commit 的 GitHub 链接**，不要只给未合并的 main 路径。建议调用文字：

> 读取我提供的 NiaOS commit 下 os/invest/skills/invest-os/SKILL.md、references/workflow.json、references/invocation.md 及实际调用的模块。先报告读到的 commit、system_version 和本轮可访问的数据。按 v1.8 生成九项日报，使用本次云端可访问且已核实的账户资料；无法读取入口或私有数据则明确降级，不声称加载成功、不猜测持仓，不创建其他任务。每项行情和重要信息带来源及时间，AI 建议/真实成交分账，不自动下单。

云端若无代码执行环境，可由 Agent 按同一协议执行文本研究，但不能宣称运行 Python 校验；若 GitHub/附件不可读，上传经审阅的公开入口与模块包到该任务能访问的位置。账户明细只提供给本人授权的私有任务上下文，不能放公共仓库。

验收以**一次真实运行回执**为准：commit/version、读到哪些模块、持仓与源时间、执行/跳过的校验、九项报告及缺口。提示词已写某功能、Skill 已装、任务仍启用，都不能替代这份运行证据。

## 同花顺 AI

使用 [交接复制指令](../../nia-invest-tonghuashun-bridge/references/handoff-guide.md)。同花顺侧提供实际可见数据，NIA 负责策略和纪律第二意见；需要手工复制就如实标 manual_copy。15:30 是交接约定，不是本次新增调度。任何自动连接需另有成功导出/导入证据。
