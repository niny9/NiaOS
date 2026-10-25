# 研究工具核验：2026-10-25

核验官方 GitHub 仓库、许可证、默认分支最新提交和最新 release；下述“适用性”是基于其文档作出的集成判断，不是实测接通结论。四者均未 archived。此次不新增依赖、不导入第三方代码、不配置实盘接口。

| 工具 | 核验事实 | 在本系统的适用范围与限制 |
|---|---|---|
| [AKShare](https://github.com/akfamily/akshare) | MIT；release-v1.19.3，2026-10-23；[提交 2ea08ff](https://github.com/akfamily/akshare/commit/2ea08ff44512a9b0c008cd4ff77463b940959c7e) | 数据采集候选。更新活跃不保证每条上游接口可用；逐接口检查来源、授权/使用条件、更新时间、复权/单位、缺失和限流，并与交易所/公告交叉验证。非持仓或实时交易连接证明。 |
| [Backtrader](https://github.com/mementum/backtrader) | [GPL-3.0](https://github.com/mementum/backtrader/blob/master/LICENSE)；默认分支最新提交 2023-04-19，[b853d7c](https://github.com/mementum/backtrader/commit/b853d7c90b6721476eb5a5ea3135224e33db1f14)；GitHub latest release 未返回记录 | 可做事件驱动回测。维护节奏较慢，先验证当前 Python/依赖兼容；数据自备，A 股 T+1、涨跌停不可成交、停牌、费用与基金确认需专门建模。复制/分发代码需评估 GPL 义务；本次仅引用，不并入代码。 |
| [Qlib](https://github.com/microsoft/qlib) | MIT；v0.9.8，2026-10-08；[提交 5435523](https://github.com/microsoft/qlib/commit/54355232463878d2eebb91fe0ee5fa7fa1f5976c) | 机器学习因子/模型研究候选，优先复用 Finance Quant 已有实验。数据集需检查 point-in-time、幸存者偏差、复权、样本外与交易成本；开源样例数据不等于当前行情。当前发布含安全迁移，不直接加载不可信模型/配置产物。 |
| [VeighNa/vn.py](https://github.com/vnpy/vnpy) | MIT；4.5.0，2026-10-06；[提交 c6e231c](https://github.com/vnpy/vnpy/commit/c6e231caf32b7fc97e6459817fff66458cf7e7c4) | 可作事件驱动平台/网关研究参考。框架支持网关不等于用户证券账户、行情授权、资产类型与同花顺已连通；需逐网关核验，当前只保留研究评估，broker_access=false。 |

许可证事实来自各仓库 GitHub license 元数据及源文件；并不覆盖上游行情、第三方网关或数据再分发权利。未来实际选用时重新核查版本和变更，先做缺数、延迟、异常价格、复权一致性、停牌/涨跌停、时区及费用样本验证，再讨论接入；没有成功样本只标候选。
