# AI产业链投资驾驶舱 - 项目总结

## 项目概述

本项目是一个完整的个人投资研究工作流系统，专注于A股AI产业链的跟踪、分析和决策辅助。系统结合了主观研究和量化策略，维护真实账户和模型模拟账户，并将所有研究成果沉淀到Obsidian知识库。

**核心原则：** 先工作流，后Agent；先账本，后智能；先模拟盘，后真实盘；先风控，后收益

## 开发进度

### ✅ Week 1: 基础架构搭建（已完成）
- 完整的项目目录结构
- SQLite数据库设计（10张核心表）
- 配置管理系统（YAML）
- 日志系统
- 数据库管理类

**交付物：**
- 项目目录和文件结构
- 数据库schema和初始化脚本
- 配置文件（universe.yaml, factor_config.yaml, risk_config.yaml）
- README.md和开发文档

### ✅ Week 2: 数据层实现（已完成）
- AKShare数据接入
- 股票基础信息获取
- AI产业链股票池（66只种子股票）
- 日线行情数据获取
- 技术因子计算（趋势、动量、成交量）

**交付物：**
- 数据获取模块（fetch_stock_basic, fetch_prices, fetch_index）
- 股票池管理（ai_chain_pool, pool_manager）
- 因子计算模块（trend, momentum, volume factors）
- 数据更新脚本（update_data.py）

### ✅ Week 3: 策略与输出（已完成）
- 三类策略打分系统（短线/波段/稳健）
- 风控检查模块
- 每日投资日报生成
- Obsidian导出功能

**交付物：**
- 策略评分模块（score_short_term, score_swing, score_stable）
- 风控模块（position_check, stop_loss_check, risk_checker）
- 报告生成模块（daily_report, obsidian_export）
- 完整的每日任务流程（daily_task.py）

### ✅ Week 4: 账户与复盘（已完成）
- 真实持仓管理
- 交易同步功能
- 模型模拟盘（三个独立组合）
- 周度复盘分析

**交付物：**
- 持仓管理模块（real_portfolio, trade_sync, portfolio_manager）
- 模拟盘模块（model_portfolio, backtest_engine）
- 复盘分析模块（review_analyzer, weekly_review）
- 交易同步脚本（sync_trade.py, init_portfolio.py）
- 周度任务脚本（weekly_task.py）

## 系统架构

```
investment-cockpit/
├── data/                    # 数据存储
│   ├── database/           # SQLite数据库
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
├── src/                    # 源代码
│   ├── config/             # 配置管理
│   ├── database/           # 数据库管理
│   ├── data_ingestion/     # 数据获取
│   ├── universe/           # 股票池管理
│   ├── factors/            # 因子计算
│   ├── scoring/            # 策略评分
│   ├── risk/               # 风控检查
│   ├── portfolio/          # 持仓管理
│   ├── reporting/          # 报告生成
│   └── utils/              # 工具函数
├── scripts/                # 可执行脚本
├── obsidian/              # Obsidian输出
└── logs/                  # 日志文件
```

## 核心功能

### 1. 数据管理
- ✅ A股行情数据获取（AKShare）
- ✅ 股票基础信息管理
- ✅ AI产业链股票池（66只初始股票）
- ✅ 技术因子计算（趋势、动量、成交量）
- ⏳ 新闻/公告抓取（预留接口）
- ⏳ 研报蒸馏（预留接口）

### 2. 策略系统
- ✅ 短线策略（1-5日持有）
- ✅ 波段策略（2-8周持有）
- ✅ 稳健策略（3个月以上持有）
- ✅ 综合评分系统（0-100分）
- ✅ Top候选输出

### 3. 风控系统
- ✅ 单票仓位限制检查
- ✅ 行业集中度检查
- ✅ 止损触发检查
- ✅ 高位追涨检查
- ✅ 流动性检查
- ✅ 风险等级评定

### 4. 持仓管理
- ✅ 真实持仓CRUD
- ✅ 交易同步（交互式/批量）
- ✅ 盈亏计算
- ✅ 仓位比例管理
- ✅ 交易撤销功能

### 5. 模拟盘
- ✅ 三个独立组合（短线/波段/稳健）
- ✅ 严格按信号执行
- ✅ 交易成本计算（手续费+印花税+滑点）
- ✅ 绩效指标（收益、回撤、夏普、胜率、盈亏比）

### 6. 复盘系统
- ✅ 推荐表现分析（1日/5日/20日收益）
- ✅ 执行偏离分析
- ✅ 归因分析（模型对/错、人对/错、市场变化）
- ✅ 周度复盘报告
- ✅ 改进建议生成

### 7. 输出系统
- ✅ 每日投资日报（Markdown）
- ✅ 周度复盘报告（Markdown）
- ✅ Obsidian知识库集成
- ✅ 日志记录系统

## 数据库设计

### 核心表（10张）
1. **stock_basic** - 股票基础信息
2. **stock_daily_bar** - 日线行情数据
3. **watchlist** - AI产业链股票池
4. **factor_scores** - 因子得分
5. **daily_signals** - 每日推荐信号
6. **real_positions** - 真实持仓
7. **real_trades** - 真实交易记录
8. **model_portfolio** - 模型持仓
9. **model_trades** - 模型交易记录
10. **review_log** - 复盘记录

## 使用流程

### 每日工作流
```bash
# 1. 运行每日任务
python scripts/daily_task.py

# 流程：
# - 更新行情数据
# - 计算技术因子
# - 策略评分
# - 风控检查
# - 生成日报
# - 导出到Obsidian
```

### 交易同步
```bash
# 交互式同步
python scripts/sync_trade.py

# 批量导入
python scripts/sync_trade.py --import trades.json

# 撤销最近一笔
python scripts/sync_trade.py --undo
```

### 周度复盘
```bash
# 周末运行
python scripts/weekly_task.py

# 输出：
# - 模型组合表现
# - 真实组合表现
# - 执行偏离分析
# - 策略有效性分析
# - 改进建议
```

## 技术栈

- **语言：** Python 3.9+
- **数据库：** SQLite
- **数据处理：** Pandas
- **数据源：** AKShare
- **配置：** PyYAML
- **输出：** Markdown (Obsidian)

## 项目特色

### 1. 双账户设计
- **真实账户：** 记录用户实际交易，用于复盘
- **模型账户：** 严格按信号执行，用于验证策略有效性
- **偏离分析：** 长期判断人工决策 vs 模型决策的有效性

### 2. 可解释性
- 每个推荐都有明确的逻辑说明
- 提供买入触发条件和止损位
- 风险提示优先展示

### 3. 风控优先
- 风控检查结果优先级最高
- 触发风险的股票自动降级或剔除
- 明确的仓位限制和止损规则

### 4. 知识沉淀
- 所有研究成果导出到Obsidian
- 结构化的知识库组织
- 便于长期回顾和学习

### 5. 模块化设计
- 清晰的模块划分
- 便于后续扩展
- 预留Agent化接口

## 当前状态

### 已实现功能
- ✅ 完整的数据获取和存储
- ✅ 技术因子计算
- ✅ 三类策略评分
- ✅ 风控检查系统
- ✅ 真实持仓管理
- ✅ 模型模拟盘
- ✅ 每日日报生成
- ✅ 周度复盘分析
- ✅ Obsidian集成

### 待完善功能（预留接口）
- ⏳ 新闻/公告抓取和结构化
- ⏳ 研报蒸馏
- ⏳ 分析师画像
- ⏳ 舆情分析
- ⏳ 基本面评分
- ⏳ 行业景气度跟踪
- ⏳ Agent化改造

## 下一步计划

### 第二阶段：主观研究增强（Week 5-8）
1. 新闻/公告结构化抓取
2. 公司卡片和行业卡片生成
3. 研报蒸馏系统
4. 舆情与分析师画像

### 第三阶段：Agent化（Week 9+）
1. 行业研究Agent
2. 公司研究Agent
3. 量化Agent
4. 风控Agent
5. 复盘Agent
6. 总控Agent

## 重要提示

### 使用前准备
1. 确保Python 3.9+环境
2. 安装依赖：`pip install -r requirements.txt`
3. 初始化数据库：`python scripts/init_database.py`
4. 配置环境变量：复制`.env.example`到`.env`

### 首次使用
1. 运行数据更新：`python scripts/update_data.py`
2. 导入真实持仓：`python scripts/init_portfolio.py --file your_positions.json`
3. 运行每日任务：`python scripts/daily_task.py`

### 网络要求
- 需要访问AKShare数据源
- 如果网络不通，系统会自动跳过数据更新
- 离线模式下仍可使用已有数据生成报告

### 数据安全
- 真实持仓数据存储在本地SQLite
- 建议定期备份`data/database/investment.db`
- 敏感信息不要提交到版本控制

## 免责声明

本系统仅用于个人投资研究、量化策略记录和复盘，不构成任何确定性投资建议。系统不会自动下单，所有真实交易均由用户本人独立决策。市场有风险，策略表现不代表未来收益。

## 项目文档

- **README.md** - 快速开始指南
- **PROJECT_SUMMARY.md** - 本文档，项目总结
- **docs_week4_usage.md** - Week 4详细使用文档
- **PRD原文** - 完整的产品需求文档

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目目录：`/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit`
- 文档目录：`/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit/obsidian`

---

**开发完成时间：** 2026-05-25  
**MVP版本：** v1.0  
**开发周期：** 4周  
**代码行数：** 约5000+行  
**测试状态：** 已通过基础验证  
**生产就绪：** 可用于个人投资研究
