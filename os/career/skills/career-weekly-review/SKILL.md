---
name: career-weekly-review
description: 执行统一版 Career OS 职业周检：复用岗位雷达、Career Learning Log 和现有 Registry，审计真实项目、12 维 AI PM 能力及简历证据，输出每周 Top3、停止投入项并回写既有系统。用于职业周检、能力缺口与求职准备度复盘。
---

# Career OS 统一职业周检

## Trigger

- “执行统一版 Career OS 周检”“Career OS 周检”“本周职业复盘”“检查能力缺口/职业偏航”。
- 每周自动运行：沿用现有 `career-os` 自动任务，每周一 09:00，`Asia/Shanghai`；不另建 scheduler。
- `career-os-weekly-review` 是口头别名，唯一 Skill ID 为 `career-weekly-review`。
- 单次找岗位交给 job radar；单个工作 case 交给 career-reflection；月度趋势交给 monthly review。

核心链路：真实项目证据 → 项目审计 → 能力缺口 → Resume Asset Gate → Top3 / Stop-Doing → 原有 Log / Registry。岗位需求改变优先级，只有个人证据能够改变已证明能力。

## Inputs

先按 [integration.md](references/integration.md) 解析唯一运行数据根目录及既有台账位置，再读取：

1. 已确认的 career_strategy、timeline、capability_map、resume_asset_pipeline、resume_fact_union（存在时）；用户最新明确更正优先，历史简历仅是待核验线索。
2. 上周报告、Capability Gap Matrix、Top3 执行结果、Stop-Doing、待补证据队列。
3. Career Learning Log；Career Market / Career Insight / Career Decision Registry 的既有记录。
4. 当前 Project Cards、项目事实底稿、变更记录、脱敏指标、Eval/实验/Trace、个人职责及第三方反馈。
5. 岗位雷达输出及本周可重新访问的官方 JD；四类资产：主业业务结果、中英文简历、AI 作品集、面试与英文讲解。

记录 `review_id = profile_id + period_start + period_end`、执行日期、市场信息截止日、时区、数据来源与缺项。默认复盘上一个完整周一至周日；用户指定区间优先，历史补录保持原区间，不能用文件修改时间代替事件日期。缺输入仍完成可做部分，未知项明确标记，不能填造数值。

## Market Intelligence

调用或读取已有 [career-job-radar](../career-job-radar/SKILL.md)，每周覆盖完整公司池；角色、优先级及桥接证据见 [targets-and-scoring.md](references/targets-and-scoring.md)。不得因为搜索失败缩小公司池。

- 每个岗位记录 company/job ID、title、岗位簇、地点/签约主体、职责、经验要求、原文链接、source type、发布/更新/抓取日期、核验状态。
- 与上周按 job ID 或规范化 URL 比较 `new / materially_changed / unchanged / closed / unavailable`。只有官方关闭证据才记 closed；页面失联不等于关闭。首次扫描是 baseline，不声称需求环比上涨。
- 技术信号只提取对岗位与实际项目有影响的官方产品文档、论文、发布说明；模型发布不等于 PM 岗位新增。
- 输出“变化 → 对哪个岗位簇/能力维度有影响 → 应保留/调整的动作”，保留反证、覆盖率、陈旧/不可访问来源。
- 上海实际办公地、主体与落户可行性、AI 核心决策权、国际用户/英文协作、美国长期路径、MBA/EMBA 的 leadership/impact/recommender 价值分别核验。未知不能当通过，不因公司名气推断签证、落户或调动资格。

## Project Interrogation

逐项覆盖当前项目底稿中的全部活跃项目，暂停/终止项目也要交代本周状态，不只挑漂亮案例。对每项按同一组问题取证：

1. 真实用户/业务问题是什么？规模、基线、失败代价是什么？
2. 为什么需要 AI？与规则、搜索、人工、无改动相比是否更好？
3. 实际 AI 能力在哪一层：规则、检索、生成、模型策略、工具调用还是 Agent？
4. 输入/输出、数据来源、系统边界与本人 ownership 是什么？
5. 模型、策略、质量和资源的取舍是什么？什么反证会改变决定？
6. Eval 的数据集、rubric、grader、基线、校准、版本、回归和上线门槛是什么？
7. 离线质量如何对应线上任务成功和业务指标？有无对照、观测窗与混杂因素？
8. 失败如何定位、回流数据、修复并回归？
9. 本人实际跑过什么查询、API、prototype、实验或调试？
10. MVP、资源和 scope 如何收敛，哪些内容被主动放弃？
11. 关键 owner、组织阻力、决策记录与本人推动是什么？
12. 增量价值、归因、净 ROI 与代价是什么？相对“不做”有何差异？

逐项保存答案、证据链接、阶段、缺项和下一步最小取证动作。采用 [评分锚点](references/targets-and-scoring.md) 评估 **项目证据成熟度**（12 项，各 0–4，满分 48），不是个人最终能力或招聘概率。分数不能替代 Gate。适用于主业具体场景的核对规则见 [project-audit.md](references/project-audit.md)。

## 12 维 AI PM Capability Matrix

统一使用下列 12 维，不能把上面的 12 个项目问题直接当能力表：

| ID | 能力维度 | 最小证据方向 |
|---|---|---|
| C01 | Product Judgment / Taste | 用户问题、取舍理由、反证及验证 |
| C02 | AI/LLM/Agent 技术理解 | 模型/检索/上下文/工具的边界与架构决策 |
| C03 | Eval 与实验 | 数据集、校准 rubric、运行结果与发布门槛 |
| C04 | Data Flywheel | 线上失败 → 标签/数据 → 迭代 → 回归结果 |
| C05 | SQL/数据/指标 | 可复核查询、漏斗、实验与归因 |
| C06 | Engineering Hands-on | 实际可运行的 API/SDK/prototype/调试记录 |
| C07 | Research→Product | 研究证据如何改变 MVP、需求和验证 |
| C08 | Agent/Harness | Tool、Memory、Context、Trace、权限与失败回放 |
| C09 | Scope/复杂执行 | 范围取舍、依赖、里程碑与实际交付 |
| C10 | Stakeholder Judgment | 权责判断、资源协调与决策记录 |
| C11 | Business/ROI | 增量、反事实、成本与可归因业务结果 |
| C12 | Ambiguity & Learning Velocity | 假设 → 实验 → 改变判断 → 下一轮证据 |

每行包含目标岗位标准及来源、上周/本周证据、当前等级、目标等级、gap、变化原因、最大缺口、下一产物、deadline、confidence。无新证据不升级；新证据推翻旧判断可以降级并保留更正依据。

采用 `ai_pm_12d_v1` 的 0–4 锚点。无法访问证据为 `unknown`；已检查材料但没有证明为 0（证据不足，不代表不会）。目标等级未核验为 unknown，不默认全是 4。旧 11 维 1–5、Learning Log L1–L7 不直接换算；用 [映射规则](references/targets-and-scoring.md) 在原有 Gap Matrix 中增加带版本的 12 维视图，保留旧历史及全球化/MBA/落户等约束。

## 横向要求：安全 / 隐私 / 可靠性 / 成本 / 延迟

每个项目、能力证据、资产 Gate、上线验收均检查五项；每项填 `pass / fail / unknown / not_applicable + 理由 + 证据 + owner`：

- 安全：高风险错误、权限/越权、滥用与人工兜底；健康场景的不确定性与专家复核。
- 隐私：数据用途/访问权限、最小化、脱敏、保存边界与对外可用范围。
- 可靠性：任务成功率、异常/失败类型、重试/回滚、回归与可回放性。
- 成本：每任务/每成功任务成本、人工复核和补贴成本；注明口径、币种及测量窗。
- 延迟：端到端分位数或受样本限制的实际观测值、超时/降级；无实测不能编 p95。

阈值按真实场景约定，不制造万能标准。安全/隐私 fail 阻止发布；其余关键项 fail/unknown 不得写“生产就绪”或“稳定提升”。不能用高总分抵消这些门槛。

## Resume Asset Gate

在既有 Project Card 与 claim 级账本上判定，沿用原验证字段并附 Gate 结论：

| Gate | 允许用途 | 通过条件 |
|---|---|---|
| Design evidence passed | 设计/研究/原型经历，准确使用“设计/研究/验证方案” | 实际产物、日期、本人职责及脱敏检查通过 |
| Result verified | 对应已证明结果的简历/STAR候选表述 | 项目背景/本人行动/结果完整；每项 claim 有原始证据、口径、观测窗、归因；横向门槛满足相应表述 |
| Candidate / evidence needed | 待补证据队列与内部草稿 | 已有线索，但项目完整性或某项 claim 未通过 |
| Blocked / disputed | 不进入投递稿、匹配的已证明能力或 MBA 成果 | 数值冲突、未来成果、拼接项目、保密问题、无法归因或夸大技术深度 |

先更新事实底稿和 Project Card，再把通过的 claims 交给既有 resume studio/precision applier 生成中英文候选表述。没有新合格证据时保持简历正文不变；不得为“本周有进展”制造完整 STAR。设计证据通过不等于业务结果通过。投递/发信不是周检动作。

## Evidence Policy 与 Truthfulness Guardrails

- 区分 `fact / user_report / inference / plan / unknown / disputed`；验证状态、保密级别与项目阶段分别记录。先前 AI 总结和旧简历不是独立证据。
- 最小证据字段：evidence ID、来源/可访问引用、事件日期、采集日期、对应 claim/project、本人职责、核验方式、适用范围、confidentiality、限制/反证。
- 官方 JD/招聘系统优先；第三方快照仅为线索，不能称“当前可投”。每周重查活跃岗位；超过 7 天未核验标 stale。技术文档记录版本；政策在 shortlist、终面、签约前重查当期官方来源。
- 计划、实现、已验证改善严格分开；不把 PRD 当上线，不把 Eval 设计当评测系统，不把工具使用当模型训练/Agent ownership。
- 业绩数字必须有基线、分子/分母、绝对/相对值、观测窗、对照/归因及来源。缺哪项就限制表述或留空；团队/主站数据不能算独立 App 或本人贡献。
- 进行中项目截至 review cutoff 只写已发生部分；未来结束日期只作计划。履历时长由已核实起止日期计算，实习/全职分开且不重复加总。
- 重叠调研样本不可相加；拆开的项目不能拼成一条大成果。用户自述可保留并明确标签，不自动升 verified。
- 现有材料冲突时保留原记录并标 disputed，隔离出正式输出；不为了好看挑最大数字。获新证据后记录 supersedes、更正理由与受影响资产。
- GitHub 只写可公开/已脱敏内容；公司原始指标、订单、个人信息、凭据及未脱敏截图留在已有私有证据库。使用不泄露内容的 evidence ID，不上传私有材料副本。

## Scoring Rubric、Top3 Priority Engine 与 Stop-Doing Gate

评分公式、证据锚点、缺数处理及同分规则见 [targets-and-scoring.md](references/targets-and-scoring.md)。三种分数分别记录：项目 0–48、能力各 0–4、行动优先级 0–100；都不是 offer 匹配概率。

先处理真实性污染、安全/隐私红线和即将到期依赖，再按需求、缺口、证据价值、紧迫性、可执行性、后续依赖选 **恰好 Top3**。每项写岗位/公司关联、能力 ID、行动、可交付产物、量化验收、owner、到期日、预计投入、依赖和停止条件。没有可靠候选时选择最小取证/修复动作，不能编工作或硬凑新产品。

每周做 Stop-Doing Gate：对重复 UI 重绘、泛资讯消费、无验证的学习、大而全无资源方案、平行 OS 框架、无增量的一次性活动逐项检查本周实际情况。输出 `stop / reduce / continue`、依据、释放时间、接收该时间的 Top3、恢复条件与复查日。建议停止的业务承诺仍需由实际 owner 决定，不能自动取消。

## Weekly Report

按 [weekly-report.md](references/weekly-report.md) 写一份主报告，固定包括：市场/岗位变化、项目逐项审计、能力缺口变化、新增可证明资产、最危险偏航点、Top3、停止/降投入、待补证据项目。既有中英文简历/作品集/面试/主业结果与 Offer 约束是资产审计的视图，不另起系统。

## Write-back / Registry Update

依 [integration.md](references/integration.md) 回写原有 Career Learning Log、Market / Insight / Decision Registry、Project Cards、Gap Matrix 与周报。按稳定 ID 去重，同一周期重跑只补差异；洞察与决策引用证据，决策保留可推翻条件。不得另建同名数据库、总账或评分系统。

路径找不到或写权限不足时：完成报告，将按目标台账分类的 pending mutations 放在本周报告内，说明实际成功/待写/失败；不新建替代 Registry，不声称同步成功。保留最小缺失位置问题供用户补充，不阻塞其他审计。

完成条件：八项周输出齐全；12 维与活跃项目均有证据/缺项；Top3 可验收；Stop-Doing 指向资源取舍；原台账写入结果可追踪；市场或证据失败已如实披露。自动执行不能隐含投递、联系他人、辞职、签 Offer 或提交申请的授权。
