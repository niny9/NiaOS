# NIA Wealth OS 每日研究工作流

Wealth OS 沿用 NiaOS 的 `os/invest` 投资子系统。

入口：[nia-wealth-daily-brief](../skills/nia-wealth-daily-brief/SKILL.md)。使用已有自动任务，不新建调度。

| 顺序 | Skill | 作用 |
|---|---|---|
| 1 | [nia-wealth-holdings](../skills/nia-wealth-holdings/SKILL.md) | 持仓快照、数据与完整性校验 |
| 2 | [nia-wealth-market-intelligence](../skills/nia-wealth-market-intelligence/SKILL.md) | A 股/基金情报与来源证据 |
| 3 | [nia-wealth-portfolio-diagnosis](../skills/nia-wealth-portfolio-diagnosis/SKILL.md) | 逐项逻辑与组合重叠诊断 |
| 4 | [nia-wealth-risk](../skills/nia-wealth-risk/SKILL.md) | 仓位、现金、集中度、回撤门禁 |
| 5 | [nia-wealth-trade-plan](../skills/nia-wealth-trade-plan/SKILL.md) | 条件化交易预案及人工确认 |
| 6 | [nia-wealth-goals](../skills/nia-wealth-goals/SKILL.md) | 2026–2032 全部净资产目标跟踪 |
| 7 | [nia-wealth-daily-brief](../skills/nia-wealth-daily-brief/SKILL.md) | 汇总、去重、保存本次简报 |

Skill 是 Agent 操作规范，不是自动执行整个流程的行情服务。七模块应一起安装；各目录均含可独立发现的 SKILL.md。已有 finance-quant 和中金财富 Skills 可按需复用，不重复复制或宣称实时接通。

运行时读取私有目标、持仓和风险政策。未知持仓不能生成卖出数量，未知现金不能生成买入数量，基金估算净值不能当成交价；缺失数据时输出可核验的公开市场研究和缺口清单。真实交易由用户执行。

验证：各 Skill 通过 skill-creator 的 quick_validate；运行 `python3 -m unittest discover -s os/invest/tests -p 'test_wealth_*.py'` 检查持仓门禁与目标数学。测试使用临时构造的明确测试数据，不写真实账户。
