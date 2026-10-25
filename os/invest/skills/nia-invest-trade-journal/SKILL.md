---
name: nia-invest-trade-journal
description: 分开记录 Invest OS 的 AI 信号和真实成交，支持去重、修订追踪和证据核对；只有完整核实的真实成交可交给持仓模块对账。
---

# 双交易日志

使用两本独立私有 JSONL：`ai-signals.jsonl` 与 `actual-trades.jsonl`。模板见 [AI 信号](assets/ai-signal.template.json) 与 [实际成交](assets/actual-trade.template.json)。统一 Schema 和校验器在同级 `invest-os`。用户口头说已卖出但未给价格、数量、费用时，记入私有 `unreconciled-updates.json`，可修正其明确说出的持仓状态，不能伪造完整成交或现金变动。

AI Signal Journal 记录信号 ID/版本、策略版本、证券、方向、时间、依据、触发、失效、不交易条件、有效期、风险、来源、纪律检查和 proposed 状态。首次发布即记录，保留未触发、失败及过期信号，不能事后删除失败建议。修改用新 ID 和 `supersedes`。

Actual Trade Journal 记录成交 ID（券商号或稳定的来源行标识）、账户别名、证券/份额、买卖方向、真实成交时间/价格/数量/费用/净资金变化、来源、用户核实、动机、情绪与 AI 建议是否一致。未知动机/情绪为 null；只能由用户陈述补充。委托、撤单、部分未成交余额、AI 信号和研究模拟各自分离；部分成交只登记实际成交部分。

`python3 scripts/journal.py --kind signal|actual --record RECORD.json --journal PRIVATE.jsonl` 校验并加锁追加；相同 ID 相同内容幂等，冲突拒绝。脚本只写日志，**不自动改持仓**。实际成交完整、核实后交 holdings 按账户/证券/成交 ID 对账，检查是否已包含在较新快照，分红、转账、换汇及基金申赎另行核实，防重复增减。

运行方式有两种：流程开始读取既有日志作为 `journal` 阶段输入；最终方案完成后再追加新信号，作为本次报告交付产物。不要在验收前修改已被工作单哈希固定的输入；先将新的日志行暂存到本次私有运行目录，验收完成后归档，下一次重新 prepare。
