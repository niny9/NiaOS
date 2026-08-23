# Invest OS "对账"模块架构设计

**版本**: 1.0.0  
**创建日期**: 2026-08-18  
**核心理念**: AI负责整理和查找，人负责最后的判断

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Invest OS 对账系统                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 数据采集层    │  │ 分析引擎层    │  │ 人工审核层    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌─────────────────────────────────────────────────┐       │
│  │          5个核心对账模块                          │       │
│  │  1. 管理层承诺追踪 (management_tracker)           │       │
│  │  2. 财报异常定位 (earnings_analyzer)              │       │
│  │  3. 反向验证引擎 (reverse_validation)             │       │
│  │  4. 同行交叉验证 (peer_analysis)                  │       │
│  │  5. 企业文化分析 (culture_analyzer)               │       │
│  └─────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 五个核心模块设计

### 1. 管理层承诺追踪 (management_tracker.py)

**目标**: 追踪管理层承诺的兑现情况，识别"承诺漂移"

**输入**:
- 财报文本（PDF/HTML）
- 电话会议记录
- 股东信
- 管理层采访

**输出**:
```python
@dataclass
class ManagementPromise:
    promise_id: str
    company_symbol: str
    promised_at: str  # 承诺日期
    promise_content: str  # 承诺内容
    promised_timeline: str  # 承诺的时间表
    status: PromiseStatus  # pending/fulfilled/delayed/broken
    tracking_history: List[PromiseUpdate]  # 历史追踪
    drift_score: float  # 漂移程度 0-1
    
@dataclass
class PromiseUpdate:
    update_date: str
    quarter: str
    update_content: str
    timeline_change: Optional[str]
    explanation: str
```

**关键算法**:
- NLP提取承诺语句（"计划"、"预计"、"将会"）
- 时间线识别（Q1/Q2/H1/H2/年度）
- 跨季度对比
- 漂移检测（时间表推后、解释变化）

**人工审核点**:
- 标记承诺的重要性（关键/一般/次要）
- 判断漂移是否合理
- 决定是否触发警告

---

### 2. 财报异常定位 (earnings_analyzer.py)

**目标**: AI粗筛变化点，人工精读确认

**输入**:
- 本期财报
- 上期财报
- 去年同期财报
- 业绩PPT

**输出**:
```python
@dataclass
class EarningsAnomaly:
    anomaly_id: str
    company_symbol: str
    quarter: str
    category: AnomalyCategory  # revenue/profit/receivable/inventory/cashflow
    metric_name: str
    current_value: float
    previous_value: float
    yoy_value: float
    change_pct: float
    severity: AnomalySeverity  # low/medium/high/critical
    ai_explanation: str
    source_location: str  # 财报页码/章节
    needs_human_review: bool
    
@dataclass
class EarningsComparison:
    symbol: str
    quarter: str
    anomalies: List[EarningsAnomaly]
    key_changes: Dict[str, Any]
    ai_summary: str
```

**关键算法**:
- 同比/环比异常检测（超过阈值）
- 应收账款/库存/现金流关联分析
- 收入质量评分（收入增长 vs 现金流增长）
- 异常项自动标注

**人工审核点**:
- 确认异常是否真实（排除会计调整）
- 判断异常严重性
- 决定是否需要深入研究

---

### 3. 反向验证引擎 (reverse_validation.py)

**目标**: 主动找反面证据，对抗确认偏误

**输入**:
- 用户的投资逻辑（thesis）
- 财报数据
- 行业数据
- 竞争对手数据

**输出**:
```python
@dataclass
class InvestmentThesis:
    thesis_id: str
    symbol: str
    core_logic: str
    key_assumptions: List[str]
    expected_catalysts: List[str]
    created_at: str
    
@dataclass
class CounterEvidence:
    evidence_id: str
    thesis_id: str
    counter_to: str  # 反驳哪个假设
    evidence_type: EvidenceType  # financial/competitive/market/management
    description: str
    data_source: str
    severity: float  # 反驳强度 0-1
    created_at: str
    
@dataclass
class DevilsAdvocateReport:
    thesis_id: str
    symbol: str
    counter_evidences: List[CounterEvidence]
    risk_score: float  # 综合风险评分
    ai_summary: str
    recommendation: str  # hold/reduce/exit
```

**关键算法**:
- 假设拆解（将投资逻辑拆成可验证的假设）
- 反向搜索（针对每个假设找反面数据）
- 证据强度评分
- 风险量化

**人工审核点**:
- 判断反面证据是否真实
- 评估反面证据的重要性
- 决定是否调整仓位

---

### 4. 同行交叉验证 (peer_analysis.py)

**目标**: 上下游公司财报对比，发现"特殊"表述

**输入**:
- 目标公司财报
- 同行公司财报（3-5家）
- 上游供应商财报
- 下游客户财报

**输出**:
```python
@dataclass
class PeerStatement:
    company_symbol: str
    company_name: str
    quarter: str
    topic: str  # 市场需求/价格趋势/竞争格局
    statement: str
    sentiment: Sentiment  # positive/neutral/negative
    key_metrics: Dict[str, float]
    
@dataclass
class CrossValidation:
    topic: str
    quarter: str
    target_company: PeerStatement
    peer_statements: List[PeerStatement]
    upstream_statements: List[PeerStatement]
    downstream_statements: List[PeerStatement]
    consensus_view: str
    outliers: List[str]  # 异常公司列表
    ai_analysis: str
    warning_level: WarningLevel  # none/low/medium/high
```

**关键算法**:
- 主题提取（市场需求、价格、竞争）
- 观点聚类（一致/分歧）
- 异常检测（谁的说法特殊）
- 上下游逻辑一致性检查

**人工审核点**:
- 判断异常是否合理（行业地位不同）
- 评估风险
- 决定是否需要调研

---

### 5. 企业文化分析 (culture_analyzer.py)

**目标**: 多年行为模式提取，困难时期决策分析

**输入**:
- 多年财报（5-10年）
- 管理层变动记录
- 困难时期的决策记录

**输出**:
```python
@dataclass
class BehaviorPattern:
    pattern_id: str
    company_symbol: str
    pattern_type: PatternType  # rd_investment/employee_treatment/shareholder_return
    time_span: str  # 观察时间跨度
    normal_behavior: str
    crisis_behavior: str
    pattern_consistency: float  # 0-1，行为一致性
    examples: List[BehaviorExample]
    
@dataclass
class BehaviorExample:
    date: str
    context: str  # 业绩好/业绩差
    decision: str
    outcome: Optional[str]
    
@dataclass
class CultureProfile:
    company_symbol: str
    company_name: str
    patterns: List[BehaviorPattern]
    culture_keywords: List[str]  # 长期主义/短期导向/技术驱动
    crisis_response_quality: float  # 0-1
    management_credibility: float  # 0-1
    ai_summary: str
```

**关键算法**:
- 时间序列分析（研发投入/裁员/分红）
- 困难时期识别（业绩下滑/行业周期）
- 决策模式提取
- 管理层信用评分

**人工审核点**:
- 判断行为模式的重要性
- 评估管理层质量
- 决定长期持有价值

---

## 数据流设计

```
┌──────────────────────────────────────────────────────────┐
│                      数据采集层                            │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 财报PDF   │  │ 电话会议  │  │ 公告文本  │  │ 新闻报道  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│       │             │              │              │       │
│       └─────────────┴──────────────┴──────────────┘       │
│                         │                                  │
│                         ▼                                  │
│              ┌────────────────────┐                       │
│              │  文档预处理引擎     │                       │
│              │  - PDF解析         │                       │
│              │  - 文本清洗         │                       │
│              │  - 结构化提取       │                       │
│              └────────────────────┘                       │
│                         │                                  │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                      分析引擎层                            │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              5个对账模块并行处理                      │ │
│  │  管理层追踪 │ 财报异常 │ 反向验证 │ 同行对比 │ 文化分析│ │
│  └─────────────────────────────────────────────────────┘ │
│                         │                                  │
│                         ▼                                  │
│              ┌────────────────────┐                       │
│              │   结果聚合引擎      │                       │
│              │   - 风险评分       │                       │
│              │   - 优先级排序      │                       │
│              │   - 报告生成        │                       │
│              └────────────────────┘                       │
│                         │                                  │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                      人工审核层                            │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ 飞书卡片推送  │  │ Obsidian报告 │  │ 邮件/Telegram│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                  │                  │           │
│         └──────────────────┴──────────────────┘           │
│                         │                                  │
│                         ▼                                  │
│              ┌────────────────────┐                       │
│              │   人工审核界面      │                       │
│              │   - 标记重要性      │                       │
│              │   - 添加批注        │                       │
│              │   - 触发警告        │                       │
│              └────────────────────┘                       │
│                         │                                  │
│                         ▼                                  │
│              ┌────────────────────┐                       │
│              │  决策记录存储       │                       │
│              │  SQLite + Obsidian │                       │
│              └────────────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

---

## 技术栈

### 核心依赖
- **NLP**: OpenAI API / Claude API（文本分析、摘要）
- **数据获取**: Rockflow MCP / AKShare / 自建爬虫
- **PDF解析**: PyPDF2 / pdfplumber
- **数据存储**: SQLite（结构化数据）+ Obsidian（知识库）
- **通知**: 飞书 Webhook / Telegram Bot

### 新增依赖
```txt
pdfplumber>=0.9.0
openai>=1.0.0
anthropic>=0.18.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
```

---

## 数据库设计

### management_promises 表
```sql
CREATE TABLE management_promises (
    promise_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    promised_at TEXT NOT NULL,
    promise_content TEXT NOT NULL,
    promised_timeline TEXT,
    status TEXT,
    drift_score REAL,
    created_at TEXT,
    updated_at TEXT
);
```

### promise_updates 表
```sql
CREATE TABLE promise_updates (
    update_id TEXT PRIMARY KEY,
    promise_id TEXT NOT NULL,
    update_date TEXT NOT NULL,
    quarter TEXT,
    update_content TEXT,
    timeline_change TEXT,
    explanation TEXT,
    FOREIGN KEY (promise_id) REFERENCES management_promises(promise_id)
);
```

### earnings_anomalies 表
```sql
CREATE TABLE earnings_anomalies (
    anomaly_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    quarter TEXT NOT NULL,
    category TEXT,
    metric_name TEXT,
    current_value REAL,
    previous_value REAL,
    yoy_value REAL,
    change_pct REAL,
    severity TEXT,
    ai_explanation TEXT,
    source_location TEXT,
    human_reviewed BOOLEAN DEFAULT 0,
    created_at TEXT
);
```

### investment_theses 表
```sql
CREATE TABLE investment_theses (
    thesis_id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    core_logic TEXT NOT NULL,
    key_assumptions TEXT,  -- JSON array
    expected_catalysts TEXT,  -- JSON array
    created_at TEXT
);
```

### counter_evidences 表
```sql
CREATE TABLE counter_evidences (
    evidence_id TEXT PRIMARY KEY,
    thesis_id TEXT NOT NULL,
    counter_to TEXT,
    evidence_type TEXT,
    description TEXT,
    data_source TEXT,
    severity REAL,
    human_reviewed BOOLEAN DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY (thesis_id) REFERENCES investment_theses(thesis_id)
);
```

### peer_validations 表
```sql
CREATE TABLE peer_validations (
    validation_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    quarter TEXT NOT NULL,
    target_company TEXT,
    peer_companies TEXT,  -- JSON array
    consensus_view TEXT,
    outliers TEXT,  -- JSON array
    warning_level TEXT,
    created_at TEXT
);
```

### behavior_patterns 表
```sql
CREATE TABLE behavior_patterns (
    pattern_id TEXT PRIMARY KEY,
    company_symbol TEXT NOT NULL,
    pattern_type TEXT,
    time_span TEXT,
    normal_behavior TEXT,
    crisis_behavior TEXT,
    pattern_consistency REAL,
    examples TEXT,  -- JSON array
    created_at TEXT
);
```

---

## 工作流集成

### 每日工作流（交易日）
```
09:00 - 盘前准备
  └─ 检查昨日发布的财报
  └─ 运行财报异常检测
  └─ 推送异常提醒

12:00 - 午间分析
  └─ 运行同行交叉验证（如有新财报）
  └─ 更新管理层承诺追踪

20:00 - 收盘后
  └─ 完整对账分析
  └─ 生成每日对账报告
  └─ 推送飞书卡片
```

### 周度工作流（周末）
```
周六 10:00 - 深度研究
  └─ 运行企业文化分析（针对持仓）
  └─ 运行反向验证（针对所有持仓）
  └─ 生成周度风险报告

周日 20:00 - 下周准备
  └─ 预览下周财报发布日历
  └─ 准备对账清单
```

---

## 输出格式

### 飞书卡片示例
```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": "⚠️ 对账异常提醒：贵州茅台 (600519)",
      "template": "red"
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**管理层承诺漂移检测**\n2024Q1承诺：海外市场H2放量\n2024Q2更新：推迟到2025Q1\n2024Q3更新：继续优化渠道\n**漂移评分**: 0.78（高风险）"
        }
      },
      {
        "tag": "action",
        "actions": [
          {
            "tag": "button",
            "text": "查看详情",
            "url": "obsidian://..."
          },
          {
            "tag": "button",
            "text": "标记已读",
            "type": "default"
          }
        ]
      }
    ]
  }
}
```

### Obsidian 报告示例
```markdown
# 对账报告 - 贵州茅台 (600519)
**日期**: 2026-08-18  
**综合风险评分**: 7.2/10 (中高风险)

## 1. 管理层承诺追踪
- ⚠️ **海外市场扩张**: 时间表已推迟3次
- ✅ **渠道改革**: 按计划推进
- 🔍 **新品发布**: 无明确时间表

## 2. 财报异常检测
- 🚨 **应收账款**: 同比增长45%，远超收入增长15%
- ⚠️ **库存周转**: 下降至1.2次/年（行业平均1.8次）

## 3. 反向验证
找到3条反面证据：
1. 竞争对手五粮液价格战加剧
2. 经销商库存高企
3. 高端消费需求放缓

## 4. 同行交叉验证
- 茅台：市场需求旺盛
- 五粮液：竞争激烈，价格承压
- 泸州老窖：渠道去库存
**结论**: 茅台说法相对乐观

## 5. 企业文化分析
- 困难时期行为：保价不保量（2015年经验）
- 管理层稳定性：高
- 长期主义得分：8.5/10

## 人工审核建议
- [ ] 关注下季度应收账款变化
- [ ] 调研经销商库存情况
- [ ] 考虑降低仓位至15%（当前20%）
```

---

## 实施优先级

### P0（立即开始）
1. 设计数据库表结构
2. 实现文档预处理引擎
3. 实现管理层承诺追踪模块
4. 集成飞书卡片推送

### P1（本周完成）
1. 实现财报异常检测模块
2. 实现反向验证引擎
3. 创建 Obsidian 报告模板
4. 配置 Telegram 通知

### P2（下周完成）
1. 实现同行交叉验证模块
2. 实现企业文化分析模块
3. 集成 Rockflow MCP
4. 完整工作流测试

---

## 关键原则

1. **AI是助手，不是决策者**
   - 所有分析结果都需要人工审核
   - 重大决策必须人工确认

2. **数据驱动，不是猜测**
   - 所有结论必须有数据支持
   - 标注数据来源和置信度

3. **持续迭代，不是一次性**
   - 从简单模块开始
   - 逐步增加复杂度
   - 根据实际使用反馈调整

4. **保护隐私，不泄露持仓**
   - 敏感数据本地存储
   - API调用不携带持仓信息
   - 飞书推送使用加密channel

---

**下一步**: 从管理层承诺追踪模块开始实现
