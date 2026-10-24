---
name: career-orchestrator
description: 编排现有 Career OS 工作流、复用输入与运行状态，将每周职业复盘路由至唯一 career-weekly-review Skill。
---

# Career Orchestrator

沿用现有调度与数据流，不复制 runtime。周检路由：

1. 读取策略与 [运行数据绑定](../career-weekly-review/references/integration.md)，锁定单一 active root。
2. 复用本次有效雷达快照；未刷新时调用 [career-job-radar](../career-job-radar/SKILL.md)。
3. 执行 [career-weekly-review](../career-weekly-review/SKILL.md)：个人证据审计、12 维、Gate、Top3、Stop-Doing、原台账回写及八段主报告。
4. 只有 Gate 通过的新 claim 才交由既有 resume studio 生成候选表述；无变化不改简历正文。
5. 记录每个步骤 written/unchanged/pending/failed，交付主报告。雷达失败允许继续个人审计，不能以 success 隐藏 partial。

保留现有申请、面试、时间线与月度复盘路由；月度流程消费既有周报，不再复制每周闭环。每周沿用现有 `career-os` 自动任务（周一 09:00 Asia/Shanghai），不创建重复任务或新增默认通知。

旧 `weekly_review` Python pipeline 如先执行 resume refresh，只能当草稿刷新；其 11 维报告不是统一周检的最终产物。未经另行授权不因编排而投递、发信、发通知或提交申请。
