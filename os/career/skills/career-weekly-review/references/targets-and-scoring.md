# 公司池、岗位簇与评分

## 公司池

此表是既有职业策略和统一周检的监控范围，**不是当前招聘事实**。每次运行以最新已确认策略为准；调整城市、时间窗、岗位主线须记录用户决定。S0/S1 仅作历史周报标签，归一到原策略 P0/P1，不能把一次热点直接升级公司优先级。

| 层级 | 公司 | 用途 |
|---|---|---|
| P0 | TikTok / ByteDance 国际化 AI（含 TikTok Shop） | 上海国际化 AI、Search/Shopping、Agent/Harness |
| P0 | MiniMax、StepFun / 阶跃星辰 | 模型应用、Agent、评测、开发者平台 |
| P1 | 小红书 AI、Trip.com / 携程 AI | 搜索、交易、消费体验与全球业务 |
| P1 | Z.ai / 智谱、SenseTime / 商汤 | 模型、Agent、平台产品 |
| P1 | PDD / Temu | 国际电商 AI 与可归因业务结果 |
| P1 | 无问芯穹 / Infinigence AI、上海人工智能实验室 | AI 基础设施、Eval、Research→Product |
| 技术观察 | DeepSeek、Moonshot AI / Kimi | 模型/评测/Agent 技术与产品信号；不默认满足上海岗位约束 |
| 长期能力标杆 | OpenAI、Anthropic、Google DeepMind | 模型/研究产品、Agent API、数据飞轮；不直接替代下一跳上海公司池 |

四个岗位簇沿用既有 ID：

| ID | 岗位簇 | 应证明的能力与资产 |
|---|---|---|
| ai_search_shopping | AI Search / Shopping | C01/C03/C05/C11；检索/排序/生成边界、相关性评测、交易漏斗与增量 |
| model_eval | Model / Eval | C02/C03/C04/C07；数据集、校准 grader、实验、badcase 回流与模型行为取舍 |
| agent_harness | Agent / Harness | C02/C03/C06/C08；工具契约、上下文/记忆、Trace、权限、回放与成功率 |
| developer_platform_builder | Developer Platform / Builder Ecosystem | C06/C07/C09/C10/C11；API/SDK、开发者路径、激活留存、平台质量与成本 |

每条机会需单独检查地点、签约主体、AI 核心参与度、国际化 scope、组织质量与时间窗，不能以公司层面标签代替岗位核验。

## Scoring Rubric

### 证据成熟度 0–4

| 分数 | 项目单项评分与能力评分的共同锚点 |
|---|---|
| 0 | 已检查输入，尚无支持该项的可审计证据；不代表没有能力 |
| 1 | 有具体理解、假设或计划，尚无可运行/已实施证据 |
| 2 | 有可追溯的设计、原型或局部实践，完整验证或个人归因仍不足 |
| 3 | 本人独立负责的完整案例已验证交付，有结果、失败分析与相关横向检查 |
| 4 | 在跨迭代/跨案例中持续负责，结果可复核，形成可重复机制并有改进证据 |

`unknown` 表示证据不可访问/未完成核验，不是 0；`N/A` 只能有明确理由，不计入个人维度评分。项目没有使用 AI 时仍评价“不用 AI 的合理判断”，不能自动把技术层给高分。

项目 12 问各 0–4，全部可评时报告 `sum/48`。缺项时报告“已评 n/12、已知小计 s/(4n)、unknown 项目”，不得用 0 补齐后伪装可比总分。主业非 AI 案例可证明产品/业务能力，不自动证明 C02/C03/C08。

能力按维度独立评分，不将所有项目平均、累加或取最高分。引用足以支持等级的个人证据、职责范围、时效与反证；成熟度相同的一百份规划不等于一次独立验证。记录人工判断理由与 confidence，不产生假精确度。

### 与旧体系的兼容

在既有 `data/capability/gap_matrix_latest.json` 中保留现有字段；仅增量加入 `ai_pm_12d` 视图（schema_version=`ai_pm_12d_v1`、review_id、dimensions），不要另建 capability 总账。首次出现为 baseline，跨量表 delta=`not_comparable`，旧 1–5 分不减 1 得新分。

| 旧 capability ID / Learning Log | 新视图关联（证据重新评，不搬分数） |
|---|---|
| business_growth | C01、C05、C11 |
| ai_llm_fundamentals | C02 |
| eval | C03、C04 |
| rag_search | C02、C03、C07；保留 Search/RAG 专项标签 |
| agent_harness | C08 |
| builder_technical_pm | C06、C09 |
| leadership_org | C09、C10 |
| global_product、mba_profile、shanghai_hukou_offer_dd、personal_brand_network | 保留原能力/约束视图；不得因 12 维转换丢失 |
| Learning Log 的 E / J / L / Evidence | 继续保留原 ID；与 C01–C12 多对多链接，C07/C12 使用真实研究、试错证据 |

每维建议字段：`id, current_level, target_level, gap, previous_level, delta, evidence_refs, jd_refs, confidence, biggest_gap, next_artifact, due_at, rationale`。只有同版本、同范围且两次评分均已核验才计算 delta；目标/current unknown 则 gap 为空。

## Top3 Priority Engine

候选来自上周未完成事项、真实性风险、Project Gap Queue、岗位变化、能力缺口；先合并同一产物，依赖任务打包成一项，避免三个“写报告”占满名额。

优先处理会污染当前正式材料的争议 claim、安全/隐私问题，以及真实截止日前的阻塞依赖。将“隔离错误 claim”与“后续补证”区分；高紧迫性不能自动把无证据材料变成通过。

其余候选每项评 0–4，未知输入标 unknown 并先取证，不假定中高分：

| 因子 | 权重 | 0 / 2 / 4 的锚点 |
|---|---:|---|
| D 目标岗位需求 | 25 | 无目标关联 / 单一已核验目标 JD / 多个独立已核验目标岗位反复要求 |
| G 能力缺口 | 20 | 已满足且无维护必要 / 部分缺口 / 主线岗位关键缺口阻塞 |
| E 证据价值 | 20 | 不能增加证明 / 补一个局部证据 / 能闭环一个关键项目或解除 claim Gate |
| U 截止紧迫性 | 15 | 无近期期限 / 本月 / 本周已确认期限或污染正在使用的材料 |
| F 一周可执行性 | 10 | 无资源/依赖未满足 / 可完成有用切片 / 资源已具备且验收明确 |
| L 后续依赖 | 10 | 无后续使用 / 支撑一个后续产物 / 解锁面试/作品集/验证等多个主线步骤 |

`priority_score = (25D + 20G + 20E + 15U + 10F + 10L) / 4`，范围 0–100，保留各因子理由。1、3 表示相邻锚点中间状态。此分数仅排序行动，不能作为能力/求职成功率。

硬问题先排，再比较分数；同分依次选真实期限更近、能形成完整可证明资产、已有项目切片、耗时更少者。每次选中后复查依赖和剩余时间；未确认时间预算时标 `provisional`，采用最小可验证切片，不虚构用户空闲时间。

恰好三项覆盖最有价值的可执行工作，不强制“一项业务、一项 Eval、一项作品集”。若只有两项成熟候选，第三项应是有必要的最小取证/约束确认，不扩展项目来凑数。未入选的保留原 Gap Queue。

## Stop-Doing Gate

对所有在做事项逐一问：是否推进 Top3 或必要业务承诺？七天内能产生/检验何种证据？资源和 owner 是否可用？是否重复既有研究/系统？

- `stop`：已确认无主线价值、重复建设，或会放大不实成果/隐私风险；写恢复条件。
- `reduce`：价值成立但当前机会成本过高，改成具体的时间/范围上限。
- `continue`：支撑 Top3 或不可取消承诺，说明必要性；不能为了列表漂亮随意砍主业。

释放时间使用用户已有记录或明确标注的估计区间，不虚报节省小时。每项关联一个接收资源的 Top3、owner、复查日；无应停止事项可写“本周无新增，继续上周约束”并给依据。
