# Weekly Report 输出合同

在既有 `reports/weekly/` 中使用当前周期的单一主报告；已经有 `career-review` 或 `career-control-loop` 文件时继续更新其既有名称，不再生成竞争版本。JSON 与 Markdown 是同一报告的两种表示。

## 报告头

包含 review_id、profile_id、周期起止、执行时间/Asia/Shanghai、market_as_of、Skill/评分版本、上周引用、数据根绑定状态、来源覆盖、`complete / partial` 与缺失原因。

开头用两三句写本周判断：职业目标是否改变、证据真正增加在哪里、最优先的动作。没有足够信息则写“暂无法判断”，不得复制上周分数当本周评估。

## 1. 市场/岗位变化

公司池覆盖表：公司/层级、查询时间、岗位簇、已核验变化、source link/type、发布时间、抓取日、地点/主体状态、对能力及行动的影响、反证/不可访问项。

单列长期能力标杆、技术观察，避免与当前可投岗位混算。保留 new/materially_changed/unchanged/closed/unavailable 数量与口径。

## 2. 项目逐项审计

表格：project_id/项目、阶段、本人 ownership、12 问证据与分数/unknown、五项横向检查、Gate、最大缺口、最小取证动作。主表逐项覆盖活跃项目，重点项目可另加详述。

如有四条 Eval 生长线、权益/任务经济性或一次性营销，按 project-audit 的专项规则补充，不假定本周全部完成。

## 3. 能力缺口变化

12 行：能力 ID、目标岗位标准/source、上周等级、本周等级、目标、gap、证据、delta/不可比原因、下一产物。保留旧矩阵中的全球化、落户、MBA 等约束状态。

“无新证据、不升级”“不可访问、暂无法评”“新证据纠错下调”分别说明。

## 4. 新增可证明资产

按主业结果、中英文简历候选、作品集、面试/英文讲解记录 artifact/project/claim ID、证据、本人贡献、Gate、可用范围、相对上周的变化。

列出新合格结果、新设计证据、待补/blocked，若没有新增验证成果明确写“0”；不可把新增文件数当能力提升。附 Offer 约束状态：上海主体/落户、AI core、全球化/美国长期路径、MBA/EMBA、组织质量；每项为证据支持的状态或 unknown。

## 5. 最危险偏航点

按严重性列出 1–3 项：证据/触发迹象、对主线的影响、owner、缓解动作、下周如何判断改善。真实性污染、只有方案没有归因结果、只有概念没有技术运行证据是检查项，不是每周预设结论。

## 6. 下周 Top3

恰好三行：rank、目标公司/岗位簇、能力/项目 ID、选择原因及各因子得分、动作、产物、量化验收、owner、due_at、时间预算/未知、依赖、停止条件。指定具体日期，不能写“尽快”。

## 7. 停止 / 降投入

事项、stop/reduce/continue、依据、时间/范围上限、释放资源（估计需标注）、接收的 Top3、owner、恢复条件、复查日；不擅自取消主业承诺。

## 8. 待补证据项目

project/claim ID、缺字段/冲突、原因、影响到的能力/简历、最小取证动作、owner、deadline、私有证据引用。包括不可访问台账、过期 JD、未核验数值、未来日期和归因缺失，避免遗漏坏消息。

## 回写与执行附录

每个目标记录 `resolved_location / record_id / operation / before→after摘要 / evidence_refs / written|unchanged|pending|failed / error`。

- Career Learning Log：E/J/Capability/Evidence 的新增或更新 ID。
- Career Market Registry：来源与岗位变动 ID。
- Career Insight Registry：事实、推断、反证及适用范围。
- Career Decision Registry：决策、依据、Top3、Stop-Doing、owner、复查日、推翻条件。
- Project Cards / claim Gate / Gap Matrix：关联 ID 与 schema_version。

若目标不存在或无权限，将 pending mutation 留在此附录，标明目标逻辑名称、拟更新字段与所需绑定；它是本次运行的待写清单，不能当第二套事实总账。报告保存不等于 Registry 全部写入成功。
