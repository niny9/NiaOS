# 同一运行的阶段产物

每个阶段一个私有 JSON 文件，文件名与 stage_id 一致。必需字段：

- `schema_version=invest.stage.v1`
- `run_id`、`plan_hash`：原 work order 中的值，不重新生成。
- `stage_id`：注册表 ID。
- `status`：complete / degraded / blocked / skipped。complete 表示该阶段所需证据及分析齐备，不等于通过风控。
- `generated_at`：含时区 ISO 时间；不得早于计划 as_of。
- `summary`：真实结果或具体降级原因。
- `evidence`：来源列表，每项含 `source_ref` 和 `source_as_of`；complete 阶段不可空。没有外部证据时，blocked 可引用预检中的本地数据缺失事实，不伪造 URL。
- `consumed_stages`：该阶段读取过的全部上游 ID，必须与依赖表一致。上游被跳过/阻断也要读到其状态。
- `output`：模块自己的结构化内容。

特殊 output：holdings 必须有 `validation_ok`；risk 必须有 `gate=pass/warn/block/unknown` 和 `policy_confirmed`；market 必须有 `market_rules_verified`；trade_plan 必须有 `plans` 数组，且每项 `state=proposed`、`executable=false`、`quantity`、`amount_cny`（未知为 null）。

v1.8 新阶段：journal 需 `signals_reviewed`、`trades_reviewed`（未知 null）；handoff 需 `connection_status=manual_copy/verified_export/unavailable`，verified_export 另需 `connection_evidence_verified=true` 和实际证据；behavior 需 `gate`；evaluation 需 `reviews` 数组。opportunities 需 `comparisons` 和 `reallocation` 数组，complete 时六类去向逐项有 conclusion。模板见各 owner Skill 的 assets。

每项 trade_plan 采用 [计划模板](../assets/trade-plan.template.json)，保留十项决策字段、horizon、个人 discipline_check 和数量/金额区间；来源有 source_ref/source_as_of。数值区间同受持仓/规则/风险/纪律门禁约束。sell/reduce/exit 的 reallocation_id 必须在 opportunities 中找到同 source_plan_id 的去向及条件；明确暂持现金有效。最终个别计划的纪律不是 pass，即使总风险通过仍不能输出数值动作。

无持仓或风险/规则不足时，trade_plan 的数值数量和金额均为 null；条件与缺口可写在 summary。brief 可以 complete（简报已完整披露缺口），而整体仍 degraded。`check-results` 会将有缺口的全流程维持 degraded，绝不返回交易权限。

quantity/amount_cny 数值必须为有限正数；通过本地格式和依赖门禁仍需实际核验价格、费率、可用资金及产品限制。结果验收不连接券商、不批准交易。禁止在摘要中藏着绕过结构化门禁的数值操作建议。

Work order 对注册表、已解析 Skill 和私有输入文件存 SHA-256。验收发现输入/Skill 改变，需重新 prepare，防止用旧计划配新证据。缺少任务结果、版本不一致、失败被标 complete 时返回 incomplete/error，不因末尾有一份简报就宣称全部完成。
