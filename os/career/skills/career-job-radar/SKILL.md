---
name: career-job-radar
description: 采集 Career OS 目标公司与岗位簇的有来源职位快照，为统一职业周检提供市场输入；不负责自动投递。
---

# Career Job Radar

复用既有本地 radar 与手工核验输入，不新建爬虫或职位数据库。先读取 active Career OS 的 career_strategy，再按 [公司池与岗位簇](../career-weekly-review/references/targets-and-scoring.md) 完整扫描。

每条职位记录公司、job ID/title、岗位簇、实际地点/主体、职责、经验要求、source URL/type、发布时间、采集/核验时间、状态。优先官方招聘页，第三方仅作待核验线索；搜索失败记录 empty/unavailable，禁止 mock 补齐。

输出沿用 `data/jobs/manual_jobs.json`、`outputs/career-job-radar/job_search_results.json` 和既有 Market Registry；schema 与数据根先按 [binding 规则](../career-weekly-review/references/integration.md) 核对。是否 new/changed/closed 必须有对比证据，失联不等于关闭。

采集结果交给 [career-weekly-review](../career-weekly-review/SKILL.md) 做个人能力与行动决策。每周运行由同一 orchestrator/自动任务复用，不额外创建一份周检或重复扫描。不得联系招聘方或自动投递。
