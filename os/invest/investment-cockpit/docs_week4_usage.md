# Week-4 使用文档（账户与复盘）

## 1. 初始化
```bash
python scripts/init_database.py
```

## 2. 首次导入真实持仓
支持 CSV/JSON，字段建议：
- `account_type, code, name, quantity, cost_price, market_price, buy_date, buy_reason, holding_type, stop_loss, target_price`

示例：
```bash
python scripts/init_portfolio.py --file your_positions.csv
python scripts/init_portfolio.py --file your_positions.json
```

## 3. 交易同步
交互输入：
```bash
python scripts/sync_trade.py
```

批量导入：
```bash
python scripts/sync_trade.py --import trades.json
```

撤销最近一笔：
```bash
python scripts/sync_trade.py --undo
```

`trades.json` 示例：
```json
[
  {
    "trade_date": "2026-05-25",
    "account_type": "stock",
    "code": "300750",
    "name": "宁德时代",
    "side": "buy",
    "price": 200.5,
    "quantity": 100,
    "reason": "短线突破",
    "executed_by_model": true,
    "holding_type": "short_term"
  }
]
```

## 4. 查看真实持仓
```bash
python scripts/view_portfolio.py
```

## 5. 模拟盘与周度复盘
```bash
python scripts/weekly_task.py
```

可选参数：
```bash
python scripts/weekly_task.py --start 2026-05-19 --end 2026-05-25 --week "2026年第21周"
```

输出：
- 周报：`obsidian/05_交易复盘/xxxx_周度复盘.md`
- 日志：`logs/weekly_task_*.json`

## 6. 数据表说明
- `real_positions`: 真实持仓
- `real_trades`: 真实交易（含 `executed_by_model`、`deviation_reason`、`status`）
- `model_portfolio`: 模型持仓
- `model_trades`: 模型交易流水
- `model_account`: 三组合虚拟资金账户
- `review_log`: 周度复盘明细（1/5/20日收益、归因结论）
