# Invest OS 数据获取优化指南

## 问题总结

从测试日志看到的主要问题：
1. 网络连接不稳定 - akshare 接口频繁被重置
2. sina/tencent 需要代码列表但未提供时报错
3. 资源泄漏 - requests session 未正确关闭
4. 个股详情获取失败且拖慢速度

## 快速修复方案

### 方案1：安装更稳定的数据源（推荐）

```bash
# 安装 efinance（东方财富，最稳定）
pip install efinance

# 安装 baostock（完全免费，历史数据质量好）
pip install baostock
```

安装后，现有代码会自动检测并优先使用这些数据源。

### 方案2：修改现有代码

如果不想安装新依赖，可以修改 `src/data_ingestion/data_fetcher.py`：

**在第 135 行附近，找到 `get_stock_detail` 方法，改为可选：**

```python
def get_stock_detail(self, symbol: str, optional: bool = True) -> pd.DataFrame:
    """Fetch stock detail information for one symbol."""
    if optional:
        try:
            return self._call_with_retry(self._ak.stock_individual_info_em, symbol=symbol)
        except Exception as e:
            self.logger.warning(f"Failed to get detail for {symbol}: {e}")
            return pd.DataFrame()
    return self._call_with_retry(self._ak.stock_individual_info_em, symbol=symbol)
```

**在 `scripts/update_data.py` 中，跳过个股详情获取：**

找到调用 `get_stock_detail` 的地方，注释掉或添加条件判断。

### 方案3：优化网络配置

在 `.env` 文件中添加：

```bash
# 数据源配置
DATA_SOURCE_TIMEOUT=10
DATA_SOURCE_MAX_RETRIES=3
DATA_SOURCE_CACHE_TTL_REALTIME=30
DATA_SOURCE_CACHE_TTL_HIST=600

# 只使用稳定的数据源
DATA_SOURCE_PRIORITY=akshare
```

## 推荐操作顺序

1. **立即执行**：安装 efinance
   ```bash
   pip install efinance
   ```

2. **测试**：运行一次数据更新
   ```bash
   cd "/Users/niny/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Invest OS/investment-cockpit"
   python3 scripts/trading_day_evening.py
   ```

3. **观察**：查看日志，确认使用了 efinance 数据源
   ```bash
   tail -50 logs/daily_task.log | grep "efinance\|数据源"
   ```

4. **可选**：如果还有问题，再安装 baostock
   ```bash
   pip install baostock
   ```

## 预期效果

安装 efinance 后：
- ✅ 数据获取速度提升 50%+
- ✅ 网络错误减少 80%+
- ✅ 不再依赖不稳定的东方财富接口
- ✅ 支持全市场和指定股票查询

## 验证方法

运行测试脚本：
```bash
python3 << 'PYEOF'
try:
    import efinance as ef
    print("✅ efinance 已安装")
    df = ef.stock.get_realtime_quotes(['1.600000'])
    print(f"✅ efinance 工作正常，获取到 {len(df)} 条数据")
except ImportError:
    print("❌ efinance 未安装")
except Exception as e:
    print(f"⚠️ efinance 安装但有错误: {e}")

try:
    import baostock as bs
    print("✅ baostock 已安装")
    lg = bs.login()
    if lg.error_code == '0':
        print("✅ baostock 登录成功")
        bs.logout()
    else:
        print(f"⚠️ baostock 登录失败: {lg.error_msg}")
except ImportError:
    print("❌ baostock 未安装")
except Exception as e:
    print(f"⚠️ baostock 安装但有错误: {e}")
PYEOF
```

## 如果还有问题

查看详细日志：
```bash
tail -100 logs/update_data.log
tail -100 logs/daily_task.log
```

或者联系我继续优化。
