# Invest OS 免费数据源使用指南

## 🎯 完全免费、无需Token的数据源

所有这些数据源都**不需要注册、不需要token、不需要付费**！

---

## 1. Baostock（强烈推荐！）

### 特点
- ✅ **完全免费，无需注册**
- ✅ 数据最全面：日K、分钟K、财务、公告、分红等
- ✅ 稳定可靠，API不会突然变化
- ⚠️ 无实时数据（最新到上一个交易日）

### 安装
```bash
pip install baostock
```

### 使用示例
```python
from engines.data_sources.baostock_fetcher import BaostockFetcher

fetcher = BaostockFetcher()

# 获取历史K线
df = fetcher.fetch_history_k_data("600519", start_date="2024-01-01")

# 获取财务数据
financial = fetcher.fetch_financial_data("600519", 2024, 2)

# 获取分红数据
dividends = fetcher.fetch_dividend_data("600519", 2023)
```

### 官方文档
http://baostock.com/

---

## 2. easyquotation（实时行情）

### 特点
- ✅ 完全免费
- ✅ 实时行情（15秒延迟）
- ✅ 支持新浪财经、腾讯财经
- ⚠️ 可能被限流

### 安装
```bash
pip install easyquotation
```

### 使用示例
```python
from engines.data_sources.realtime_quote_fetcher import RealtimeQuoteFetcher

# 新浪财经
fetcher = RealtimeQuoteFetcher(source="sina")
quote = fetcher.fetch_single_quote("600519")

# 腾讯财经（支持港股）
fetcher_tencent = RealtimeQuoteFetcher(source="tencent")
```

### GitHub
https://github.com/shidenggui/easyquotation

---

## 3. Ashare（双核心）

### 特点
- ✅ 新浪+腾讯双核心
- ✅ **自动故障切换**
- ✅ 简单易用

### 安装
```bash
pip install Ashare
```

### 使用示例
```python
from engines.data_sources.realtime_quote_fetcher import AshareFetcher

fetcher = AshareFetcher()
data = fetcher.fetch_realtime_data("600519")
```

### GitHub
https://github.com/mpquant/Ashare

---

## 4. AKShare（综合数据）

### 特点
- ✅ 数据种类丰富
- ✅ 持续更新维护
- ⚠️ 部分接口不稳定

### 安装
```bash
pip install akshare
```

### 使用
已集成在现有系统中，会在Baostock失败时自动降级使用。

---

## 🚀 推荐组合策略

### 场景1：历史数据分析
**使用 Baostock**
- 最稳定可靠
- 数据最全面
- 完全免费

### 场景2：实时监控
**使用 easyquotation 或 Ashare**
- 实时价格
- 自动切换源

### 场景3：综合分析
**使用降级机制**
```python
from engines.data_sources import FallbackFetcher

fetcher = FallbackFetcher()

# 自动降级：Baostock → AKShare → easyquotation → 本地 → 手动
data = fetcher.fetch_with_fallback("600519", "prices")
```

---

## 📊 数据对比

| 数据源 | 历史K线 | 实时行情 | 财务数据 | 稳定性 | Token |
|--------|---------|---------|---------|--------|-------|
| **Baostock** | ✅ 全 | ❌ | ✅ | ⭐⭐⭐⭐⭐ | 无需 |
| **easyquotation** | ❌ | ✅ | ❌ | ⭐⭐⭐⭐ | 无需 |
| **Ashare** | ✅ | ✅ | ❌ | ⭐⭐⭐⭐ | 无需 |
| **AKShare** | ✅ | ✅ | ⚠️ | ⭐⭐⭐ | 无需 |

---

## ⚡ 快速开始

### 1. 安装所有免费数据源
```bash
pip install baostock easyquotation Ashare akshare
```

### 2. 测试数据获取
```bash
cd /Users/niny/NiaOS/os/invest

# 测试Baostock
python engines/data_sources/baostock_fetcher.py

# 测试实时行情
python engines/data_sources/realtime_quote_fetcher.py

# 测试降级机制
python engines/data_sources/fallback_fetcher.py
```

### 3. 运行完整测试
```bash
python tests/test_data_sources.py
```

---

## 🎉 优势总结

1. **完全免费** - 无需任何付费
2. **无需Token** - 不用注册账号
3. **多源降级** - 一个失败自动切换
4. **数据全面** - 覆盖历史和实时
5. **稳定可靠** - Baostock官方维护

---

## 📚 参考资源

- [Baostock官网](http://baostock.com/)
- [easyquotation GitHub](https://github.com/shidenggui/easyquotation)
- [Ashare GitHub](https://github.com/mpquant/Ashare)
- [AKShare文档](https://akshare.akfamily.xyz/)

---

## 💡 使用建议

1. **优先使用Baostock** - 历史数据最稳定
2. **实时行情用easyquotation** - 简单可靠
3. **配置降级机制** - 确保数据获取不中断
4. **定期更新库** - 保持最新版本

---

最后更新：2026-09-13
