# Career OS 项目事实与能力证据

这批更新把此前遗漏的登录态补齐，并将月卡拆为“即买即用”和“我京页签心智透传”。六个当前项目共十二条工作流、十四条原子能力证据，均为已有私有材料的脱敏摘要。事实截止于 2026 年 10 月底材料快照，整理日期为 2026-11-06；没有声称核验此后的发布或效果。

| 用户链路 | 当前项目 | 本人可陈述的产品行动 |
|---|---|---|
| 进入服务 | [登录体验与跨应用登录](views/jd_login_state_optimization.md) | 短期组件复用、联登分阶段交付、授权与异常验收 |
| 理解并使用权益 | [月卡](views/jd_super_monthly_card_journey.md) | 即买即用与个人页价值表达分开推进，按生命周期组织体验 |
| 健康选择与记录 | [健康饮食](views/jd_current_health_channel_v1.md) | 场景分期、接口拆解与记录承接责任确认 |
| AI建议后的消费承接 | [AI健康建议](views/jd_tongue_health_shopping.md) | 评测与业务效果分离，检查商品、搜索与广告完整链路 |
| 看到真实权益价值 | [省钱信息](views/jd_my_savings_floor.md) | 数据语义、展示边界和相关方对齐 |
| 后续触达 | [Push分人群](views/jd_push_segmentation.md) | 人群需求与交付管理 |

## 可打开的底表

- [项目总览](views/项目总览.md)、[十二条工作流](views/周进度表.csv)、[十四条原子能力证据](views/原子能力证据.csv)。
- [结构化事实库](portfolio.redacted.json)。`PRIVATE-REF-*` 是私有来源引用，不是可公开访问或独立验证的原始材料。
- [验证报告](QA.md)与[执行脚本](scripts/project_evidence_sync.py)。

每次收到新的项目进展，沿用同一个 `project_id`，同批更新项目事实、工作流与原子能力。不能只更新汇报，也不能等用户再次提醒才归档。详见[增量更新流程](../workflows/project-progress-to-capability.md)。

## 能力、结果与职业表达

原子证据表示“这个项目中做过什么”，不是能力分数。`macro` 保留旧框架标识；`candidate_12d` 仅为已有十二维周检的待审阅方向，不能直接换分或证明 AI 技术能力。登录、月卡等非 AI 工作可以证明范围、数据和协作判断，不能据此声称模型或 Agent 经验。

设计证据、阶段评审、实际发布和业务结果分别核验。公开版不含内部指标、产品排期、接口细节、同事信息、原始截图、公司文档标识、HR答卷或个人路径。完整底稿和转正材料继续在原私有 Career OS 维护。新进展的读源审核、真实性判断与脱敏由 Agent/人负责；Python 负责验证与生成，不是后台监控器或自主事实核验器。

## 本地运行

支持 macOS/Linux，使用 Python 3.10+ 标准库，在本目录运行：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/project_evidence_sync.py --store portfolio.redacted.json --out /tmp/career-evidence-preview
```

生产使用时由既有运行配置传入私有 `--store`、`--out` 和可选 `--vault`。生成目录应专用于本工具，不能指向源材料目录。先对候选更新 `--input` 做 `--dry-run`，再按已有写回流程生成最小差异并校验并发修改。CLI 对同一事实库的完整读写过程持有文件锁，忙碌时明确拒绝第二个写入者并要求重试；各文件原子替换。外部编辑器不受该锁管理，笔记替换前会再次检查原文。跨文件不提供全有或全无的事务，失败后保留事实和备份，可修复原因后幂等重跑。
