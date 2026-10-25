---
name: nia-invest-tonghuashun-bridge
description: 规范同花顺 AI 与 Invest OS 的持仓、成交、委托、行情、预警和纪律数据交接；提供北京时间 15:30 交接报告及人工复制方案，不假设接口已连接。
---

# 同花顺数据交接

职责：同花顺侧仅报告平台实际支持且当前授权可访问的行情、真实持仓/成交、条件预警和盘中信号。NIA 侧做资产配置、策略第二意见、财富目标、交易纪律、复盘与评测。能力逐项标 supported/unavailable/unknown，并附本次观察或官方依据；平台宣传不等于当前账户已开通。

统一协议为 [handoff.schema.json](../invest-os/assets/schemas/handoff.schema.json)，填写 [空白交接模板](assets/handoff.template.json)，使用 [15:30 报告与复制指令](references/handoff-guide.md)。包含数据时间、账户持仓、现金、真实成交、未成交委托、市场信号、风险事件、候选机会、纪律偏差、数据质量。行情和事件各有源时间/获取时间/来源。

没有确认可用的导出/API 时默认 manual_copy。保留原摘要并核对证券代码、份额、账户别名、数量和现金范围。禁止声称两个 AI 自动连通，禁止索取/保存交易密码，也不尝试绕过平台限制。自动导出只有验证到实际接口、权限、字段和成功样本后才标 verified_export；此协议不实现账户访问或下单。

北京时间 15:30 作为每日交接的报告时点：有现有可调用环境则生成当日报告；否则用户在此时复制摘要给 NIA。本 Skill 不新增/修改任何调度，未被触发就没有报告。非交易日标休市快照/无新增交易；跨境/QDII 报告该时点可获得的最近净值，不能宣称其海外市场已收盘。

用 `invest-os/scripts/validate_record.py handoff PRIVATE.json --as-of ISO --max-age-hours N` 验证。格式通过仍不代表来源真实或当前账户完整；`data_quality.status!=verified`、缺账户/时间/现金/行情均不得升级为可执行快照。经人工核实后由 holdings 映射为既有 `wealth.snapshot.v1`，保留映射及源文件，不自动把交接写入账本。
