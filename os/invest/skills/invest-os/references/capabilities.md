# 新旧投资能力接线

## 唯一编排入口

自然语言入口 `$invest-os`；仓库 CLI `os/invest/runners/invest_os.py`；注册入口 `os/invest/workflows/invest_workflow.json`。CLI 处理发现、预检与验收，Agent 执行研究模块。旧 workflow 的概念步骤保留在 `legacy_steps` 以便追溯，不作为当前运行状态。

| 既有能力 | 继续负责 | 交给新流程的内容 |
|---|---|---|
| finance-quant-closed-loop | Claw 数据/因子/策略/回测/衰减/量化风险计算 | market/diagnosis/risk 消费其证据与时间，不直接采纳建议仓位 |
| investment-workflow | 管理层承诺、财报异常、反向验证、同行对比、企业文化 | reconciliation 的 thesis 与反证，交 diagnosis 融合 |
| ciccwm-market-analysis | 行情、资金流、历史序列、关联板块 | market 的二级数据与交叉核验 |
| ciccwm-hot-news-analysis | 热点和专题资讯 | market 的线索，不替代公告证据 |
| ciccwm-etf-ranking-analysis | ETF 排行与资金信息 | market/diagnosis 的 ETF 背景，不按排名直接交易 |
| ciccwm-fund-product-info | 基金档案、费率、净值、持仓披露 | market/diagnosis 的基金事实与规则 |
| ciccwm-stock-finance-analysis | 财务报表 | reconciliation 的原始财务证据 |
| ciccwm-tiger-list-analysis | 盘后异动与席位 | 仅相关事件进入 reconciliation，非每日必跑 |
| 七个 nia-wealth-* | 快照、情报、诊断、条件决策、组合风险、财富目标、简报 | 决策与报告层，复用上述取数及计算 |

## 输入适配，不擅自改 schema

Finance Quant 常见产物：`quotes_snapshot.json`、`quant_report.json`、`factor_effectiveness.json`、`factor_decay.json`、`daily_hybrid_recommendation.json`、`risk_exposure.json`、`finance_report.json`、`fund_holdings_snapshot.json`。以当前实际配置和 status 返回路径为准；不根据旧说明就假设存在。

market 的 evidence 记录原产物文件/URL、字段、source_as_of 和 retrieved_at。Finance 的 `freshness=fresh` 可能只基于文件 mtime，还需核对内容内源时间、truth_level 和真实源；不得仅凭文件新就提升为实时可信。基金持仓期末数据不当实时暴露。

旧对账的 ManagementPromise、EarningsAnomaly、CounterEvidence、PeerStatement、CultureProfile 保留原 ID、报告期及证据位置，转换为新 diagnosis 的支持/反证条目。旧数值评分不是新组合风险阈值。

旧 holdings 导出必须先映射到 `wealth.snapshot.v1`、保留字段映射和用户确认，不因名称为 holdings 就成为真实持仓。paper_* 永远独立，不进入真实快照。

中金返回原始字段与单位由各数据 Skill 解释；本工作流不维护第二套 API 协议。无凭证、源时间缺失、冲突、估算净值保持降级，并可转查官方公开资料。数据提供模块无需加载完整个人账户。

## 已有入口的双向连接

`scripts/connect_existing.py` 给本地 finance-quant 和 investment-workflow 插入有限范围的路由块：完整综合任务进入 invest-os，已分派的 stage 不递归，原细分操作保留。脚本默认只检查，`--apply --backup-dir PRIVATE_DIR` 才安装路由并备份原文件。它不上传旧 Skill 原文，不修改旧 Python runner，不触碰通知配置或凭证。

新 daily-brief 也路由到统一入口；被作为 brief 阶段调用时只汇总。数据 Skills 继续保持单一查询职责，避免任何查询都重新生成整份简报。
