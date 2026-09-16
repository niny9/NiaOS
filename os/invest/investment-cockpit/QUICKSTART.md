# 快速启动指南

## 5分钟上手

### 1. 环境准备

```bash
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

### 2. 初始化数据库

```bash
python scripts/init_database.py
```

**预期输出：**
```
数据库初始化成功
已创建10张核心表
```

### 3. 首次数据更新

```bash
python scripts/update_data.py
```

**流程说明：**
- 获取股票基础信息
- 初始化AI产业链股票池（66只）
- 获取日线行情数据
- 计算技术因子

**预期时间：** 3-5分钟（取决于网络速度）

### 4. 生成第一份日报

```bash
python scripts/daily_task.py
```

**输出位置：**
- 日报：`obsidian/01_每日简报/YYYY-MM-DD_AI产业链投资日报.md`
- 总览：`obsidian/00_总览/日报总览.md`
- 日志：`logs/daily_task.log`

### 5. 查看日报

```bash
# 使用任意Markdown编辑器打开
open obsidian/01_每日简报/$(date +%Y-%m-%d)_AI产业链投资日报.md

# 或使用Obsidian打开整个obsidian目录
```

## 日常使用流程

### 每日工作流（5分钟）

```bash
# 激活环境
cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"
source .venv/bin/activate

# 运行每日任务
python scripts/daily_task.py

# 查看日报
open obsidian/01_每日简报/$(date +%Y-%m-%d)_AI产业链投资日报.md
```

### 交易同步（2分钟）

```bash
# 方式1：交互式输入
python scripts/sync_trade.py

# 方式2：批量导入
python scripts/sync_trade.py --import trades.json

# 查看持仓
python scripts/view_portfolio.py
```

### 周度复盘（周末，10分钟）

```bash
# 运行周度任务
python scripts/weekly_task.py

# 查看复盘报告
open obsidian/05_交易复盘/$(date +%Y年第%V周)_周度复盘.md
```

## 常见场景

### 场景1：首次导入现有持仓

```bash
# 准备持仓文件（JSON格式）
cat > my_positions.json << EOF
[
  {
    "account_type": "股票",
    "code": "300750",
    "name": "宁德时代",
    "quantity": 100,
    "cost_price": 200.50,
    "buy_date": "2026-05-01",
    "buy_reason": "看好新能源车产业链",
    "holding_type": "稳健",
    "stop_loss": 180.00,
    "target_price": 250.00
  }
]
EOF

# 导入
python scripts/init_portfolio.py --file my_positions.json
```

### 场景2：同步一笔买入交易

```bash
python scripts/sync_trade.py

# 按提示输入：
# 日期：2026-05-25
# 代码：300750
# 名称：宁德时代
# 操作：买入
# 价格：205.30
# 数量：100
# 原因：突破前高
# 是否按模型建议：是
```

### 场景3：同步一笔卖出交易

```bash
python scripts/sync_trade.py

# 按提示输入：
# 日期：2026-05-25
# 代码：300750
# 名称：宁德时代
# 操作：卖出
# 价格：215.80
# 数量：100
# 原因：达到目标价
# 是否按模型建议：是
```

### 场景4：撤销错误的交易

```bash
# 撤销最近一笔交易
python scripts/sync_trade.py --undo
```

### 场景5：查看当前持仓和盈亏

```bash
python scripts/view_portfolio.py

# 输出示例：
# 真实持仓：
# 300750 宁德时代 | 100股 | 成本200.50 | 现价205.30 | 盈亏+2.39%
# 总市值：20,530元 | 总盈亏：+480元 (+2.39%)
```

## 定时任务设置（可选）

### 使用cron自动运行每日任务

```bash
# 编辑crontab
crontab -e

# 添加以下行（每个交易日下午3:30运行）
30 15 * * 1-5 cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit" && "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/.venv/bin/python" scripts/daily_task.py >> logs/cron.log 2>&1
```

### 使用launchd（macOS推荐）

创建文件：`~/Library/LaunchAgents/com.investment.daily.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.investment.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/.venv/bin/python</string>
        <string>/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/scripts/daily_task.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>15</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/logs/daily_task.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/logs/daily_task_error.log</string>
</dict>
</plist>
```

加载任务：
```bash
launchctl load ~/Library/LaunchAgents/com.investment.daily.plist
```

## 故障排查

### 问题1：网络连接失败

**症状：** 数据更新失败，提示DNS解析错误

**解决：**
```bash
# 检查网络连接
ping push2his.eastmoney.com

# 如果无法连接，系统会自动跳过数据更新
# 可以使用已有数据继续生成报告
```

### 问题2：数据库锁定

**症状：** 提示"database is locked"

**解决：**
```bash
# 检查是否有其他进程在使用数据库
lsof data/database/investment.db

# 如果有，等待其完成或终止进程
```

### 问题3：依赖安装失败

**症状：** pip install失败

**解决：**
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题4：日报为空

**症状：** 日报生成但候选列表为空

**原因：**
- 数据库中没有行情数据
- 因子计算失败
- 评分阈值过高

**解决：**
```bash
# 检查数据
python scripts/validate_week2.py

# 重新更新数据
python scripts/update_data.py

# 查看日志
cat logs/daily_task.log
```

## 数据备份

### 手动备份

```bash
# 备份数据库
cp data/database/investment.db data/database/investment_backup_$(date +%Y%m%d).db

# 备份Obsidian笔记
tar -czf obsidian_backup_$(date +%Y%m%d).tar.gz obsidian/
```

### 自动备份脚本

创建文件：`scripts/backup.sh`

```bash
#!/bin/bash
BACKUP_DIR="/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp data/database/investment.db $BACKUP_DIR/investment_$DATE.db

# 备份Obsidian
tar -czf $BACKUP_DIR/obsidian_$DATE.tar.gz obsidian/

# 保留最近7天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成：$DATE"
```

添加到crontab（每天凌晨2点备份）：
```bash
0 2 * * * "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/scripts/backup.sh"
```

## 性能优化

### 加速数据更新

```bash
# 只更新股票池中的股票（不更新全市场）
python scripts/update_data.py --watchlist-only

# 只更新最近N天的数据
python scripts/update_data.py --days 5
```

### 减少日志输出

编辑`.env`：
```
LOG_LEVEL=WARNING
```

## 下一步

- 📖 阅读完整文档：`README.md`
- 📊 查看项目总结：`PROJECT_SUMMARY.md`
- 🔧 详细使用指南：`docs_week4_usage.md`
- 📝 查看PRD原文：了解系统设计理念

## 获取帮助

```bash
# 查看脚本帮助
python scripts/daily_task.py --help
python scripts/sync_trade.py --help
python scripts/weekly_task.py --help
```

---

**祝投资顺利！记住：系统只是辅助工具，最终决策权在你手中。**
