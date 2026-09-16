# Invest OS 健康检查报告

**检查时间**: 2026-06-04 22:24:58

---

## 总体状态: ❌ 错误

### ✅ ENV 配置
**状态**: ok
- **file_exists**: True
- **db_path_configured**: True
- **db_path**: data/database/investment.db
- **feishu_configured**: True

### ❌ 数据库
**状态**: error
- **file_exists**: True
- **file_size**: 2977792
- **holdings_count**: 0
- **active_holdings**: 0

**问题**:
- 数据库查询失败: no such table: holdings

### ✅ Python 环境
**状态**: ok
- **python_version**: 3.12.2 | packaged by conda-forge | (main, Feb 16 2024, 20:54:21) [Clang 16.0.6 ]
- **python_path**: /opt/anaconda3/bin/python3
- **missing_modules**: []

### ✅ 输出文件
**状态**: ok
- **reports_dir_exists**: True
- **logs_dir_exists**: True
- **recent_reports**: 4 项
