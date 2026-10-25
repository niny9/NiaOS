# 接入现有 NIA OS 与自动任务

统一入口现为同级 `invest-os/SKILL.md`，机器可读调用关系见其 `references/workflow.json`。本简报 Skill 是终端汇总阶段。旧 finance-quant 与 investment-workflow 通过受限路由块连接到该入口，中金财富六项通过 provider_skills 分配给情报/对账阶段。依赖、模块版本与输入快照由统一预检和结果验收负责。

## 路径和职责

发布仓库是 `niny9/NiaOS`，不等于 `niny9/nia-os`、NailOS 或其他同名公共项目。Wealth OS 是现有 `os/invest` 下的个人财富研究工作流；七个 Skill 放在 `os/invest/skills/nia-wealth-*`，工作流入口 `os/invest/workflows/nia-wealth-daily.md`。安装时全部保持同级目录，保留脚本和 references。

现有 Invest OS 的 `engines/` 提供对账分析思路，`workflows/` 和 `investment-cockpit/` 属于既有运行组件。本次不搬迁其数据库、不启动其调度、不替换其数据源。历史“100%完成”报告不是当前可用性证据。

统一工作流显式注册本地 `finance-quant-closed-loop` 和 `investment-workflow` 为量化/对账阶段，中金财富六项作为按需取数 provider。使用前检查真实存在、凭证、源时间戳及运行结果；缺失时将对应阶段或 provider 标记不可用，仍可用联网官方资料继续公开研究。不要把已安装适配器等同于行情接通。任何旧脚本先检查副作用，不能因本次简报任务默认触发其通知、模拟成交或 Base 写回。

## 私有绑定

优先当前任务明确给定的 `WEALTH_OS_PRIVATE_ROOT`；其次现有自动任务中的实际输入路径；再核对已有 NIA OS 的有效持仓/目标绑定。每次输出 resolved binding map：持仓文件、目标文件、风险政策、报告目录和验证状态。冲突用 disputed；缺失用 unresolved，不选择“最新修改文件”就当权威。

私有根建议包含 `holdings/`、`goals.json`、`risk-policy.json`、`reports/`，但已有结构优先。模板不自动变成真实数据；不自动改旧主账。若当前任务已给出持仓/目标路径直接沿用，不另建平行真源。

截至安装时，没有可证实的当前账户快照，应保持 holdings unavailable；这不妨碍安装技能。准确的财富目标金额和确认来源只留私有目标文件，公开模板保留 2026–2032 年份与 null 金额。

## 已有自动化的连接与验收

用户已创建 NIA Wealth OS 每日任务。本次发布不新增自动化，不改变时间、模型、通知策略或项目。后续运行入口可以是 `$nia-wealth-daily-brief`；只要调度环境能加载本地 Skills 或读取已发布仓库的该 Skill 及依赖，就可使用此定义。

ChatGPT 云端任务不必然读取本机 `~/.codex/skills`。若运行位置是云端，需在原任务可用上下文中提供 GitHub 工作流/Skill 链接；不能把本机安装回执当作云端加载证明。原任务的定时触发、读取版本及实际报告需用该任务自己的运行回执验收。本次没有新建或重新安排该任务的授权范围扩展。

完成状态分开报告：文件已编写、校验已通过、GitHub commit/PR 已回读、本机已安装、调度已加载、市场数据已核验、持仓已确认。只标记有证据的项。
