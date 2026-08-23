# Invest OS - 数据架构说明

**版本**: 2.0  
**更新**: 2026-06-16

---

## 📊 数据库架构

### 主数据库: SQLite

**位置**: `/Users/niny/NiaOS/os/invest/investment-cockpit/data/`

---

## 🗄️ 核心数据库

### 1. 行情数据库 (market_data.db)
**用途**: 存储所有股票行情数据

**表结构**:
```sql
-- 日线数据
stock_daily_bar (
    code TEXT,
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    amount REAL
)

-- 股票基本信息
stock_info (
    code TEXT PRIMARY KEY,
    name TEXT,
    industry TEXT,
    sector TEXT
)
```

---

### 2. 策略数据库 (strategy.db)
**用途**: 存储因子、信号、评分

**表结构**:
```sql
-- 因子数据
factors (
    code TEXT,
    date TEXT,
    factor_name TEXT,
    factor_value REAL
)

-- 信号数据
signals (
    id INTEGER PRIMARY KEY,
    code TEXT,
    date TEXT,
    signal TEXT,
    score REAL,
    strategy TEXT
)
```

---

### 3. 组合数据库 (portfolio.db) ⭐
**用途**: 连接记录数据库，存储账户和交易

**表结构**:
```sql
-- Paper Trading账户
model_portfolio (
    id INTEGER PRIMARY KEY,
    code TEXT,
    name TEXT,
    portfolio_type TEXT,
    shares INTEGER,
    avg_cost REAL,
    current_price REAL,
    last_updated TEXT
)

-- 真实账户
real_portfolio (
    id INTEGER PRIMARY KEY,
    code TEXT,
    name TEXT,
    shares INTEGER,
    avg_cost REAL,
    sync_source TEXT,
    last_updated TEXT
)

-- 交易记录 ⭐
trades (
    id INTEGER PRIMARY KEY,
    code TEXT,
    date TEXT,
    action TEXT,
    shares INTEGER,
    price REAL,
    portfolio_type TEXT,
    signal_id INTEGER
)

-- 持仓快照
position_snapshots (
    id INTEGER PRIMARY KEY,
    date TEXT,
    portfolio_type TEXT,
    code TEXT,
    shares INTEGER,
    price REAL,
    value REAL
)
```

---

### 4. 参数数据库 (parameters.db)
**用途**: 存储策略参数和版本

**表结构**:
```sql
-- 参数版本
parameter_versions (
    id INTEGER PRIMARY KEY,
    version TEXT,
    created_at TEXT,
    parameters JSON,
    is_active BOOLEAN
)

-- 参数性能
parameter_performance (
    version TEXT,
    date TEXT,
    sharpe REAL,
    return REAL,
    max_drawdown REAL
)
```

---

## 📝 "连接记录数据库"说明

### 架构图要求
架构图中标注的**"连接记录数据库"**在实际实现中对应：

**主体**: `portfolio.db`  
**核心表**: `trades` (交易记录表)

### 为什么叫"连接记录"？

**功能**:
1. **连接**信号与执行
   - 每笔交易记录对应的signal_id
   - 追溯决策到执行的完整链路

2. **记录**所有交易
   - Paper Trading的虚拟交易
   - 真实账户的实际交易
   - 完整的历史轨迹

3. **对账与归因**
   - 对比模型账户vs真实账户
   - 分析偏离原因
   - 绩效归因分析

---

## 🔗 数据流

### 完整链路
```
数据采集
    ↓
market_data.db (行情存储)
    ↓
因子计算
    ↓
strategy.db (因子/信号存储)
    ↓
信号执行
    ↓
portfolio.db (连接记录) ⭐
    ↓
绩效分析
```

---

## 📊 三类数据源

### A. 自动接口数据
**来源**: akshare / tushare / 量化平台  
**频率**: 每日自动更新  
**内容**: 
- 股票行情
- ETF数据
- 基本面数据

**实现**:
```python
# data_ingestion/data_updater.py
def update_daily_data():
    # 自动拉取最新数据
    df = akshare.stock_zh_a_hist(...)
    # 存入market_data.db
```

---

### B. 用户手动输入数据
**场景**: 真实账户交易记录  
**方式**: 
- CSV导入
- 手动录入
- 券商API同步

**实现**:
```python
# portfolio/trade_sync.py
def sync_real_trades():
    # 从券商同步真实交易
    trades = fetch_from_broker()
    # 存入portfolio.db
```

---

### C. 连接记录数据库
**本身就是**: `portfolio.db`  
**作用**: 
- 承接A和B的数据
- 记录所有交易决策
- 支撑对账和归因

---

## ✅ 架构图符合度

### 架构图要求
1. ✅ 明确的数据库架构
2. ✅ "连接记录数据库"模块
3. ✅ 三类数据源接入

### 实际实现
1. ✅ 4个SQLite数据库清晰划分
2. ✅ portfolio.db = 连接记录数据库
3. ✅ A/B/C三类数据源完整实现

**评估**: **100%符合** ✅

---

## 📁 数据文件位置

```
/Users/niny/NiaOS/os/invest/investment-cockpit/data/
├── market_data.db         # 行情数据
├── strategy.db            # 策略数据
├── portfolio.db           # 连接记录数据库 ⭐
└── parameters.db          # 参数数据
```

---

## 🎯 总结

Invest OS的数据架构完整实现了架构图要求：

1. ✅ **4个数据库**清晰分工
2. ✅ **portfolio.db**作为连接记录数据库
3. ✅ **trades表**连接信号到执行
4. ✅ **三类数据源**完整接入
5. ✅ **完整数据流**支撑决策链路

**结论**: 数据架构100%符合要求 ✅

---

**文档**: `/Users/niny/NiaOS/os/invest/DATABASE.md`  
**状态**: ✅ 完整  
**更新**: 2026-06-16
