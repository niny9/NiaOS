# Invest OS 数据获取优化总结

优化时间：2026-06-01

## 已完成的优化

### 1. 多数据源集成 ✅

**新增数据源**：
- **efinance (东方财富)** - 优先级最高
  - 优点：数据全面、更新及时、无需注册
  - 支持：实时行情、历史数据、板块数据
  - 安装：`pip install efinance`

- **baostock** - 优先级第二
  - 优点：完全免费、数据质量好、稳定
  - 缺点：实时性稍差（延迟5分钟）
  - 安装：`pip install baostock`

**数据源优先级**：
```
efinance > baostock > akshare > sina > tencent
```

### 2. 资源泄漏修复 ✅

**问题**：
- requests session 未正确关闭
- baostock 登录后未登出

**修复**：
- 添加 `__del__` 析构函数，确保 baostock 自动登出
- 使用 context manager 模式管理资源

### 3. 可选依赖处理 ✅

**改进**：
- efinance 和 baostock 改为可选依赖
- 缺失时记录警告但不影响其他数据源
- 动态构建可用数据源列表

### 4. 数据源选择优化 ✅

**问题**：
- sina 和 tencent 需要代码列表，但未提供时会报错
- akshare 获取指定股票时效率低

**修复**：
- 当未提供代码列表时，只使用支持全市场查询的数据源
- 优化 akshare 的股票查询逻辑

## 使用说明

### 安装依赖

```bash
# 必需依赖
pip install akshare requests pandas

# 可选依赖（推荐安装）
pip install efinance baostock
```

### 使用示例

```python
from src.data_ingestion.multi_source_fetcher import MultiSourceFetcher

# 创建获取器
fetcher = MultiSourceFetcher()

# 查看可用数据源
print(fetcher.get_available_sources())

# 获取全市场行情
df = fetcher.fetch_spot_data()

# 获取指定股票行情
df = fetcher.fetch_spot_data(['000001', '600000'])
```

## 性能对比

| 数据源 | 全市场查询 | 指定股票查询 | 实时性 | 稳定性 |
|---|---|---|---|---|
| efinance | ✅ 快 | ✅ 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| baostock | ❌ 不支持 | ✅ 中 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| akshare | ✅ 中 | ⚠️ 慢 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| sina | ❌ 不支持 | ✅ 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| tencent | ❌ 不支持 | ✅ 快 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 下一步

手动将 `src/data_ingestion/multi_source_fetcher_new.py` 重命名为 `multi_source_fetcher.py`
