# NIA Wealth OS 每日研究工作流

Wealth OS 沿用 NiaOS 的 `os/invest` 投资子系统。

统一入口：[invest-os](../skills/invest-os/SKILL.md)。使用已有自动任务，不新建调度。调用图与阶段证据契约由 [工作流注册表](../skills/invest-os/references/workflow.json) 定义，原 [invest_workflow.json](invest_workflow.json) 已指向此入口。

实际顺序：持仓/市场/旧量化 → 原五类对账 → 持仓诊断 → 风控 → 财富目标 → 条件预案 → 每日简报。中金财富六项按需作为市场和对账的数据提供模块，避免重复取数。

仓库预检入口：`python3 os/invest/runners/invest_os.py prepare --bindings PRIVATE_BINDINGS --as-of ISO时间 --max-age-hours N --probe-quant`。Agent 按预检返回的任务和 Skill 路径执行研究，最后使用 `check-results` 验收。预检本身不伪装成研究完成。

| 顺序 | Skill | 作用 |
|---|---|---|
| 1 | [nia-wealth-holdings](../skills/nia-wealth-holdings/SKILL.md) | 持仓快照、数据与完整性校验 |
| 2 | [nia-wealth-market-intelligence](../skills/nia-wealth-market-intelligence/SKILL.md) | A 股/基金情报与来源证据 |
| 3 | [nia-wealth-portfolio-diagnosis](../skills/nia-wealth-portfolio-diagnosis/SKILL.md) | 逐项逻辑与组合重叠诊断 |
| 4 | [nia-wealth-risk](../skills/nia-wealth-risk/SKILL.md) | 仓位、现金、集中度、回撤门禁 |
| 5 | [nia-wealth-trade-plan](../skills/nia-wealth-trade-plan/SKILL.md) | 条件化交易预案及人工确认 |
| 6 | [nia-wealth-goals](../skills/nia-wealth-goals/SKILL.md) | 2026–2032 按每项目标独立口径跟踪 |
| 7 | [nia-wealth-daily-brief](../skills/nia-wealth-daily-brief/SKILL.md) | 汇总、去重、保存本次简报 |

上表为保留的七个 Wealth 模块。v1.8 另接机会发现、行为纪律、双日志、策略评测和同花顺交接，完整映射见 [集成清单](../skills/invest-os/references/v1.8-integration.md)，当前 14 阶段以注册表为准。

Skill 是 Agent 操作规范，不是自动行情服务。统一入口、七个 Wealth 与五个新增模块应同级安装。已有 finance-quant、investment-workflow 和中金财富 Skills 保留原计算/查询功能，统一入口解析路径并分派。

运行时读取私有目标、持仓和风险政策。未知持仓不能生成卖出数量，未知现金不能生成买入数量，基金估算净值不能当成交价；缺失数据时输出可核验的公开市场研究和缺口清单。真实交易由用户执行。

验证：各 Skill 通过 skill-creator 的 quick_validate；运行 `python3 -m unittest discover -s os/invest/tests -p 'test_wealth_*.py'` 检查持仓门禁与目标数学。测试使用临时构造的明确测试数据，不写真实账户。
