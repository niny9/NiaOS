# 飞书多维表格集成使用说明

## 1. 环境变量
在 `.env` 中配置：

```bash
FEISHU_APP_ID=your_app_id_here
FEISHU_APP_SECRET=your_app_secret_here
FEISHU_BITABLE_APP_TOKEN=your_bitable_app_token_here
```

## 2. 初始化

```bash
python scripts/init_feishu.py
```

该脚本会：
- 创建/校验 5 张业务表及字段
- 从 SQLite 同步当前存量数据
- 输出飞书访问 URL

## 3. 每日与每周同步
- `python scripts/daily_task.py`：自动同步持仓、交易、信号、股票池
- `python scripts/weekly_task.py`：额外同步周度复盘汇总

## 4. 增量同步策略
- 使用 `feishu_sync_state` 记录本地行哈希
- 行内容无变化则跳过
- 已有飞书记录则更新，无记录则创建
- 默认策略：SQLite 为主，飞书为展示与协作视图

## 5. 验证

```bash
python scripts/test_feishu_integration.py
```

## 6. 故障排查
- 检查 app 凭证是否正确
- 检查 `FEISHU_BITABLE_APP_TOKEN` 是否为目标多维表格
- 查看 `logs/daily_task_*.json` 和 `logs/weekly_task_*.json` 中的 `feishu_sync` 字段
