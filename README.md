# NiaOS - Nia Operating System

个人 AI 驱动的操作系统，包含投资、内容、产品等多个子系统。

## 项目结构

```
NiaOS/
├── os/
│   ├── invest/           # 投资操作系统
│   │   ├── engines/      # 5大对账分析引擎
│   │   ├── data/         # 数据存储
│   │   └── *.md          # 文档和报告
│   ├── content/          # 内容操作系统（待完善）
│   └── product/          # 产品操作系统（待完善）
└── README.md
```

## Invest OS - 投资对账系统

AI 驱动的投资研究"对账"系统，帮助投资者对抗确认偏误，提高决策质量。

### 核心功能

1. **管理层承诺追踪** - 追踪管理层承诺，检测"承诺漂移"
2. **财报异常定位** - AI 粗筛财报变化点，评估收入质量
3. **反向验证引擎** - 主动寻找反面证据，对抗确认偏误
4. **同行交叉验证** - 对比同行表述，识别异常值
5. **企业文化分析** - 分析长期行为模式，评估管理层信用

### 技术栈

- **Python 3.12+**
- **数据库**: SQLite
- **数据源**: AKShare, Mootdx, a-stock-data (54端点/19数据源)
- **量化**: Backtrader, Vectorbt
- **知识库**: Obsidian (Markdown)

### 快速开始

```bash
# 1. 安装依赖
pip install akshare backtrader vectorbt mootdx baostock stockstats

# 2. 运行完整对账分析
python3 ~/.agents/skills/investment-workflow/runner.py full \
  --symbol 600519 \
  --name 贵州茅台 \
  --quarter 2024Q3 \
  --data financial_data.json

# 3. 查看报告
# Obsidian: ~/Library/Mobile Documents/.../Invest OS/reconciliation/
```

### 使用文档

- [架构设计](os/invest/RECONCILIATION_ARCHITECTURE.md)
- [系统集成报告](os/invest/SYSTEM_INTEGRATION_REPORT.md)
- [测试报告](os/invest/RECONCILIATION_TEST_REPORT.md)
- [数据源测试](os/invest/DATA_SOURCE_TEST_REPORT.md)

### 实盘案例

- [永鼎股份深度对账](os/invest/永鼎股份_深度对账报告_20260820.md)

## 系统完成度

- **Invest OS**: 95% ✅
  - 对账分析层: 100%
  - 数据获取层: 100%
  - 量化回测层: 100%
  - 自动化层: 待完善（Rockflow MCP、Telegram Bot）

- **Content OS**: 规划中
- **Product OS**: 规划中

## 开发理念

> **AI 负责整理和查找，人负责最后的判断。**

所有 AI 生成的结论都需要人工确认，重大决策必须人工批准。

## License

MIT License

## 作者

Nia OS Team

---

**版本**: 1.1.0  
**更新**: 2026-08-23
