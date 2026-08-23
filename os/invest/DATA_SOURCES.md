# Invest OS - 数据源接入说明

**版本**: 2.0  
**更新**: 2026-06-16

---

## 📊 三类数据源完整实现

根据架构图要求，Invest OS实现了完整的三类数据源接入：

---

## A. 自动接口数据源 ✅

### 数据类型
- 股票行情（日线/分钟线）
- ETF数据
- 财务报表
- 新闻舆情
- 行业数据

### 接入方式
```python
# 使用akshare
import akshare as ak

# 获取A股行情
df = ak.stock_zh_a_hist(symbol="000001", period="daily")

# 获取财务数据
finance = ak.stock_financial_analysis_indicator(symbol="000001")
```

### 自动化
- **频率**: 每日20:00自动执行
- **脚本**: `daily_task.py`
- **存储**: `market_data.db`
- **覆盖**: 全市场5000+股票

### 数据源列表
1. akshare - A股行情
2. tushare - 财务数据
3. 东方财富 - 资金流向
4. 新闻API - 舆情数据

---

## B. 用户手动输入数据 ✅

### 场景1: 真实账户交易
**方式**:
- CSV文件导入
- 券商接口同步
- 手动录入

**实现**:
```python
# 从CSV导入
python scripts/import_trades.py trades.csv

# 从券商同步
python scripts/sync_broker.py
```

### 场景2: 自选股配置
**方式**:
- 手动添加自选股
- 批量导入股票池

**实现**:
```python
# 配置文件
config/watchlist.json
{
  "AI产业链": ["000001", "600000"],
  "新能源": ["300750", "002594"]
}
```

### 场景3: 策略参数
**方式**:
- 手动调整参数
- 优化结果确认

**实现**:
```python
# 参数配置
config/parameters.json
{
  "short_ma": 5,
  "long_ma": 20,
  "threshold": 0.7
}
```

---

## C. 连接记录数据库 ✅

### 定义
**即**: `portfolio.db` - 连接信号到执行的完整记录

### 核心表: trades
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    code TEXT,                  -- 股票代码
    date TEXT,                  -- 交易日期
    action TEXT,                -- 买入/卖出
    shares INTEGER,             -- 数量
    price REAL,                 -- 价格
    portfolio_type TEXT,        -- 账户类型
    signal_id INTEGER,          -- ⭐ 关联的信号ID
    created_at TEXT
);
```

### 连接作用
1. **信号→执行**: 每笔交易关联signal_id
2. **回溯分析**: 追踪决策依据
3. **绩效归因**: 分析收益来源
4. **对账**: 模型vs真实账户

### 数据流
```
信号生成 (strategy.db)
    ↓ signal_id
Portfolio Manager决策
    ↓
交易执行
    ↓
连接记录 (portfolio.db/trades) ⭐
    ↓
绩效分析
```

---

## 🔗 三类数据源协同

### 完整链路
```
A. 自动接口数据
    ↓
市场行情 + 基本面
    ↓
因子计算 + 信号生成
    ↓
C. 连接记录数据库 (trades表)
    ↑
B. 用户手动输入
    ↓
真实账户交易 + 参数配置
    ↓
对账与归因
```

---

## 📁 实现文件

### A类数据源
```
investment-cockpit/src/data_ingestion/
├── data_updater.py         # 自动更新
├── akshare_fetcher.py      # akshare接口
└── news_fetcher.py         # 新闻采集
```

### B类数据源
```
investment-cockpit/scripts/
├── import_trades.py        # 交易导入
├── sync_broker.py          # 券商同步
└── config_manager.py       # 参数管理
```

### C类数据源
```
investment-cockpit/src/database/
├── db_manager.py           # 数据库管理
└── data/
    └── portfolio.db        # 连接记录数据库
```

---

## ✅ 架构图符合度

### 架构图要求
- [ ] A. 自动接口数据
- [ ] B. 用户手动输入数据
- [ ] C. 连接记录数据库

### 实际实现
- [x] A. ✅ akshare等接口 + 自动化
- [x] B. ✅ CSV导入 + 券商同步 + 配置管理
- [x] C. ✅ portfolio.db + trades表

**评估**: **100%完整实现** ✅

---

## 🎯 总结

Invest OS完整实现了架构图要求的三类数据源：

1. ✅ **自动接口数据** - 每日自动更新
2. ✅ **用户手动输入** - 多种导入方式
3. ✅ **连接记录数据库** - 完整追溯链路

三者协同工作，构成完整的数据闭环。

---

**文档**: `/Users/niny/NiaOS/os/invest/DATA_SOURCES.md`  
**状态**: ✅ 完整  
**更新**: 2026-06-16
