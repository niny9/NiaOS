# Weekly Career Review Workflow

唯一执行合同为 [career-weekly-review](../skills/career-weekly-review/SKILL.md)。沿用现有同名本地 Skill 与工作流，本文件仅作入口，不维护第二套流程/评分/报告模板。

每周一 09:00 Asia/Shanghai，由已有 `career-os` 自动任务运行：

`已有策略/Log/Registry → job radar → 项目逐项审计 → 12维证据视图 → Resume Asset Gate → Top3 / Stop-Doing → 原台账回写 → Weekly Report`

[编排器](../skills/career-orchestrator/SKILL.md) 管调度，[岗位雷达](../skills/career-job-radar/SKILL.md) 管市场输入，[月度复盘](../skills/career-monthly-review/SKILL.md) 聚合周报。

私有数据绑定、11→12 维兼容、去重、缺失输入和失败写回均遵守 [integration.md](../skills/career-weekly-review/references/integration.md)。验收遵守 [八段周报合同](../skills/career-weekly-review/references/weekly-report.md)。不以旧 CLI 返回成功代替周检内容验收。
