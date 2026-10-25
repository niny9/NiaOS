# Wealth OS 共同数据契约 v1

## 真源与存储

公开定义属于 `niny9/NiaOS/os/invest/skills`，Wealth OS 复用 Invest OS，不另立重复投资系统。运行数据和用户目标来自明确指定的 `WEALTH_OS_PRIVATE_ROOT`、已有自动任务绑定或用户给定文件；先解析一个 active root，其他旧目录只读。无绑定时报告缺口，不把新模板当已连接账户。

公开仓库只提交 Skills、空模板、验证脚本和工作流。真实持仓、账户号、凭证、资产估值、负债及个人目标金额放私有根；绝不上传 raw exports。查询公开标的可用证券代码，不能将账户、数量、成本一并发给行情服务。不要启动旧脚本的通知、下单或调度副作用。

## 每次运行的公共字段

- `run_id`、`as_of`（含时区）、`timezone=Asia/Shanghai`、`schema_version`。
- `source_ref`（URL/本地文件及记录 ID）、`source_as_of`（事实时间）、`retrieved_at`（读取时间）。来源冲突保留两边，不平均为“真值”。
- `quality`: `verified` / `unverified` / `stale` / `missing` / `disputed` / `estimate`。verified 需要能回溯证据，不能由模型自评置信度替代。
- `market_session`: `premarket` / `open` / `closed` / `non_trading_day` / `unknown`，按交易所日历及具体品种核验，不能仅按星期判断。基金还须核验产品开放日及申赎状态。
- `limitations`、`evidence_ids`、`next_check`、`human_gate=true`。事实、推断、条件建议分别标注。

数据缺失可继续公开市场研究，但组合结论应为 unknown。门禁不通过时不能把未知风险写成低风险、把 null 写为 0、把系统未接入写成空仓。

## 快照 v1

顶层：`schema_version=wealth.snapshot.v1`、唯一 `snapshot_id`、`as_of`、`confirmed_by_user`、`accounts_complete`、`pending_activity`、`empty_positions_confirmed`、`base_currency=CNY`、`source_ref`、`positions`、`cash_cny`、`reported_investable_assets_cny`。

每行：`account_alias`、`symbol`（字符串）、`venue`、`share_class`、`asset_type`（stock/etf/fund）、`currency=CNY`、`quantity`、`available_quantity`、`unit_price`、`price_as_of`、`source_ref`、`quality`。`cost_total_cny` 可为 null；价格是元/股或元/份，数量不得含“万”倍率。

`reported_investable_assets_cny` 的口径是证券市值加账户现金；不含房产，不扣其他家庭负债。与逐项合计的差异须解释为应收、在途等，不能强行抹平。v1 脚本仅处理同币种 CNY、无待处理活动的简单快照；复杂账户须单独对账再放行，不能称该脚本支持融资、多币种或债务全口径。

快照时效与价格时效分开。最新源的源时间为空仍为 unverified；未来时间、错日净值、重复行、对不上账户总额皆阻断。脚本 `ok=true` 只代表所声明字段通过本地检查，不证明文件真实或允许交易。

## 七模块接口

| 模块 | 核心输出 |
|---|---|
| holdings | 快照、validation.ok、missing_fields、用途对应时效 |
| market-intelligence | 可追溯 evidence 列表、影响路径与失效条件 |
| portfolio-diagnosis | 逐项 thesis/反证/变化、组合重复暴露与不确定性 |
| risk | 限额版本、敞口、回撤口径、pass/warn/block/unknown |
| trade-plan | 数据及风险门、条件方案、数量推导或 null、人工确认状态 |
| goals | 全部净资产、可投资资产、目标缺口、现金流和假设场景 |
| daily-brief | 引用上述产物；缺失模块显示 unavailable，不能编造完成 |

交易计划只进入 proposed。用户确认的 decision 和外部已成交 trade 是两个事件；没有成交凭证不得变更持仓。报告“建议买入”不代表委托、委托不代表成交、到账不代表已扣除全部税费。所有模块默认不下单、不自动转账。
