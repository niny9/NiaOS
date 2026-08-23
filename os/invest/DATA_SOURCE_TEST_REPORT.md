# Invest OS 数据源测试报告

**测试时间**: 2026-08-19 22:10  
**测试目的**: 验证数据获取能力和稳定性

---

## 测试结果汇总

| 数据源 | 状态 | 可用功能 | 限制 |
|--------|------|---------|------|
| **AKShare** | ⚠️ 部分可用 | 历史K线 ✅ | 实时行情❌（代理问题） |
| **Mootdx** | ⚠️ 待优化 | 连接成功 ✅ | API调用需修复 |
| **对账系统** | ✅ 完全可用 | 5模块全部正常 | 需要数据输入 |

---

## 详细测试结果

### 1. AKShare 测试

#### ✅ 成功的功能
```python
# 历史K线数据 - 完全可用
df = ak.stock_zh_a_hist(symbol='600519', period='daily', adjust='qfq')
# ✅ 成功获取 5986 条K线数据
# ✅ 最新: 2026-08-19  1307.88  +0.76%
```

#### ❌ 失败的功能
```python
# 实时行情列表 - 代理阻塞
stocks = ak.stock_zh_a_spot_em()
# ❌ ProxyError: Unable to connect to eastmoney.com
# 原因: 代理配置阻止访问

# 财务指标 - 数据为空
df = ak.stock_financial_analysis_indicator(symbol='600519')
# ⚠️ 返回空数据（API可能变化）
```

### 2. Mootdx 测试

#### ✅ 连接成功
```
✅ mootdx can connect
✅ 自动选择最快服务器
```

#### ⚠️ API调用需优化
```python
# quotes() 返回 DataFrame 而非预期格式
# 需要修改调用方式
```

---

## 问题分析

### 问题1: 代理配置阻塞东方财富

**现象**: 
- `eastmoney.com` 连接被代理阻塞
- 影响实时行情和部分财务数据

**解决方案**:
```python
# 方案1: 临时禁用代理（推荐用于数据获取）
import os
os.environ['NO_PROXY'] = 'eastmoney.com,*.eastmoney.com'

# 方案2: 使用 mootdx（不依赖东财）
from mootdx.quotes import Quotes
client = Quotes.factory('std')
```

### 问题2: 非交易时间限制

**现象**:
- 测试时间: 22:10（非交易时间）
- 部分实时接口无数据

**建议**:
- 交易时间测试（09:30-15:00）
- 或使用历史数据进行测试

---

## 推荐使用方案

### 方案A: 纯 AKShare（历史数据）

**适用场景**: 日终复盘、历史回测

```python
import akshare as ak

# 历史K线（完全可用）
df = ak.stock_zh_a_hist('600519', period='daily', adjust='qfq')

# 季度财报（需验证）
df = ak.stock_yjbb_em(date='20240930')  # 业绩预告
```

**优点**: 
- ✅ 历史数据完整
- ✅ 免费无限制
- ✅ 社区活跃

**缺点**:
- ❌ 实时数据受代理影响
- ⚠️ 部分API不稳定

### 方案B: AKShare + Mootdx 组合（推荐）

**适用场景**: 完整对账分析

```python
# 历史数据用 AKShare
import akshare as ak
hist = ak.stock_zh_a_hist('600519', period='daily', adjust='qfq')

# 实时行情用 Mootdx（待API修复）
from mootdx.quotes import Quotes
client = Quotes.factory('std')
```

**优点**:
- ✅ 互补性强
- ✅ 不依赖单一源
- ✅ mootdx不受代理影响

**缺点**:
- ⚠️ mootdx API需要适配

### 方案C: 手动输入数据（当前可用）

**适用场景**: 立即测试对账系统

```bash
# 准备数据文件
cat > financial_data.json << EOF
{
  "current": {"revenue": 1000, "net_profit": 100},
  "previous": {"revenue": 900, "net_profit": 90},
  "yoy": {"revenue": 800, "net_profit": 80}
}
EOF

# 运行完整对账
python3 ~/.agents/skills/investment-workflow/runner.py full \
  --symbol 600519 --name 贵州茅台 --quarter 2024Q3 \
  --data financial_data.json
```

---

## 下一步建议

### 立即可做（推荐方案C）

1. **准备真实财报数据**
   - 从公司财报PDF手动提取
   - 或使用已有的2024Q2数据
   
2. **运行实盘对账**
   ```bash
   # 选择3只股票进行测试
   python3 runner.py full --symbol 600519 --name 贵州茅台 --quarter 2024Q2 --data 茅台_Q2.json
   python3 runner.py full --symbol 000858 --name 五粮液 --quarter 2024Q2 --data 五粮液_Q2.json
   python3 runner.py full --symbol 002304 --name 洋河股份 --quarter 2024Q2 --data 洋河_Q2.json
   ```

3. **验证分析质量**
   - 检查承诺漂移检测是否准确
   - 财报异常是否合理
   - 反向验证是否发现真实风险

### 短期优化

1. **修复代理问题**
   ```python
   # 在 engines/__init__.py 中添加
   import os
   os.environ['NO_PROXY'] = 'eastmoney.com,*.eastmoney.com'
   ```

2. **适配 Mootdx API**
   - 修正 quotes() 调用方式
   - 添加错误处理

3. **增加数据源降级**
   - AKShare 失败 → Mootdx
   - Mootdx 失败 → Baostock

### 中期集成

1. **Rockflow MCP 认证**（获取实时财报）
2. **Telegram Bot 配置**（自动推送）
3. **每日自动化工作流**

---

## 结论

**系统状态**: ✅ 对账核心功能完全可用

**数据获取**: ⚠️ 历史数据可用，实时数据需优化

**建议行动**: 
1. 使用方案C（手动数据）立即开始实盘测试
2. 并行优化数据获取（修复代理/适配API）
3. 验证分析质量后推广使用

**核心价值**: 
> 即使数据获取有限制，对账系统的分析逻辑是完整的。
> 手动输入数据也能体验完整的承诺追踪、异常检测、反向验证流程。

---

**创建时间**: 2026-08-19  
**下次测试**: 交易时间段（09:30-15:00）重新测试实时接口
