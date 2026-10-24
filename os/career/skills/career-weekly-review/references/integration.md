# 既有系统接入与回写

## 单一入口与职责

公开 Skill 定义：`niny9/NiaOS/os/career/skills/career-weekly-review/SKILL.md`。沿用本地已有的 `career-weekly-review` 名称；不另建 career-os-weekly-review 文件夹。

| 既有组件 | 继续负责 | 与统一周检的关系 |
|---|---|---|
| career-orchestrator | 调度、运行状态与依赖 | 调用 job radar → 统一周检；避免重复扫描与重复周报 |
| career-job-radar | 职位采集、规范化、source freshness | 提供输入，不独立判断个人能力或另选 Top3 |
| career-reflection | 单个 case 的 Experience/Judgment/Capability/Evidence | 继续写原 Career Learning Log；周检引用其 ID |
| career-weekly-review | 项目审计、12 维、Gate、Top3、Stop-Doing、回写 | 本文定义的唯一每周决策闭环 |
| career-resume-studio / career-precision-applier | 简历草稿、岗位版本与 claim diff | 只消费通过 Gate 的 claim；周检不复刻生成器 |
| career-monthly-review | 聚合本月周报、月度方向与资源决策 | 引用周报/Registry ID，不重复跑四次雷达，不用平均分代替证据复核 |

本次发布复用本地组件的职责，补齐 GitHub 中缺失的接入说明；不复制本地 main.py、数据、通知器或 scheduler。仓库 Skill 是供 Agent 执行的操作合同，不能声称本仓库已有完整 Python runtime。

## Runtime bindings / Inputs 发现

区分 Skill 定义根与私有运行数据根。显式提供的 `CAREER_OS_ROOT`/现有任务配置优先；否则检查当前 Career OS 项目。路径需实际存在且含正确 profile/策略，不能只因目录名字相似就选中。

2026-10-25 读取到的既有位置（用于发现，不代表全都应写入）：

- 当前 Codex `career-os` 自动任务的项目为本地 `~/Documents/GitHub/nia-os`；其 Career OS 位于 `legacy/scattered-sources/career-os/`。
- 同名本地运行目录还有 `~/career-os/`，旧 NiaOS 目录为 `~/NiaOS/os/career/`；这些是迁移/历史来源，不应全部同步写成多个真相源。
- 远程目标是 **niny9/NiaOS**；`niny9/nia-os` 是不同仓库，本 Skill 的发布不能误推到后者。

读取各来源的配置、上次成功回写位置与最新用户更正，形成一次运行的 resolved binding map。确认一个 active data root 后，其余只读；遇到策略或事实冲突就列 disputed，不自动迁移/覆盖。未来路径变化用实际配置解析，不把个人绝对路径写入公开报告。

| 逻辑资产 | 已观察到的现有存储/定位方式 | 使用原则 |
|---|---|---|
| 职业策略/能力/事实底稿 | active root 下 `config/career_strategy.json`、`config/capability_map.json`、`config/resume_asset_pipeline.json`、`config/resume_fact_union.json`（若存在）、`config/timeline.json` | 读取策略与事实状态，旧生成内容不自动 verified |
| Career Learning Log | `reflections/`、既有 career-reflection 指向的 Obsidian 职业复盘笔记 | 继续 E/J/L/Evidence 框架与既有 ID，不新建学习库 |
| Career Market Registry | `data/market/market_registry_*.json`；雷达输入为 `data/jobs/manual_jobs.json`、`outputs/career-job-radar/job_search_results.json` | 沿用现有快照与字段；补 evidence/freshness 元数据，不伪造在线结果 |
| Career Insight Registry | 先查既有 Log 的 Judgment/Insight 段、报告引用与已绑定外部台账 | 本次未定位到独立同名文件；不得猜一个路径后创建空库 |
| Career Decision Registry | `data/decisions/` 与 `reports/weekly/*decisions*` 的既有对应关系 | 保持原记录、决策 ID 与历史，只补变化 |
| Project Cards / claim Gate | `data/resume/project_cards.json`、既有 fact union、Project Gap Queue | 一 project_id 一完整项目；先事实，后候选简历 |
| Capability Gap Matrix | `data/capability/gap_matrix_latest.json` | 保留原字段/历史；加带版本的 12 维视图 |
| Weekly Report | `reports/weekly/` 的当前命名约定 | 同周期一个主报告，支持 md/json，不建第二份总账 |

上述映射是已发现的存储候选，不意味着所有逻辑 Registry 已验证可写。每次核对实际内容/ID/schema：若现有 Insight 记录就是 Learning Log 的 J 段，复用并在 binding map 指定该段；若仍未定位，则标 `unresolved`，待写项进入周报附录，不把别的文件擅自改名充当它。

## Write-back / Registry Update

1. **先读取再写**：读取目标最新内容、现有 IDs、schema、私密范围与上次 run；不得从空模板覆盖原台账。
2. **生成最小变更集**：证据/项目状态 → claim Gate → 12 维视图 → Market/Insight/Decision/Log → 主报告。每项携带 review_id、引用证据、前后差异与目标位置。
3. **稳定 ID 去重**：Market 用官方 job ID 或规范化 URL；Project 用原 project_id；Log/Insight/Decision 沿用原 ID，只有确实新记录才按既有规则分配。没有 ID 时按来源+事件日期+主题查重，不依赖标题文字完全一致。
4. **更正保留历史**：冲突记录为 disputed；新证据修正用 supersedes 或现有历史字段，不删除旧决定。重复运行没有新证据时不新增 insight、不增加等级、不重复计成果。
5. **保密与写入**：按原格式原子替换/追加；写前校验并发变更，变化时重读合并。公开仓库只提交脱敏 Skill/报告或允许公开的证据引用；不复制私有原始指标、履历库、cookie、联系方式或公司文档。
6. **回读验证**：核对实际路径/记录 ID/版本与写入状态，失败标 pending/failed。GitHub 提交前检查 diff；使用正常快进，不 force push，拒绝后重读 main 再合并。确认远端后才称已同步。

市场不可访问时继续个人项目审计；证据不可访问则 unknown、不升分；主台账不可写则保留周报内按目标分组的 pending mutations。授权/权限问题明确报告，不能创建平行系统绕过。

## 每周自动运行与兼容

复用已有 Codex 自动任务 `career-os`，每周一 09:00 Asia/Shanghai，保留原模型、项目、时间与通知设置。任务提示应先读取上述唯一 Skill 及其引用，再使用原 private runtime 完成周检；读取失败明确降级，不能声称已执行最新版。

旧本地 orchestrator 的 `weekly_review` 顺序曾是 radar → resume refresh → weekly review。resume refresh 如仍在前置阶段，只可整理草稿/来源，不能先升 verified；统一周检完成 Gate 后再让原生成器消费通过的 claim。旧 CLI 的 11 维自动报告只能作为输入/中间结果，不能代替本 Skill 的 12 维、项目审计、真实性与八段输出验收。

本次不另装 cron、不复制调度器、不默认执行可能发送飞书通知的旧 CLI。若后续要修改实际 runtime，先检查调用者及通知副作用；已有用户授权继续有效。文档“每周自动运行”表示接入上述现有任务，不等于已观察到某次未来任务成功。
