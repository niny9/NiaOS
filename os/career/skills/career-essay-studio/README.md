# Career Essay Studio - 使用指南

MBA/EMBA文书写作系统 - 为在职申请者设计

## 核心理念

**文书不是简历扩写，而是展现个人独特性的"成长小说"**

基于浙大→哈佛学姐的方法论：
1. 找到核心叙事线（真正让你有感触的兴趣点）
2. 用主线筛选和裁剪素材
3. 处理"鸡肋"经历（强调通用能力 or 升华到精神层面）
4. 写好落点（从过去延伸到未来）
5. 先写主文书再拆分配比

## 快速开始

### 前置准备

准备两个文件：

1. **个人档案.md** - 你的基本信息和背景

```markdown
# 个人档案

## 基本信息
- 姓名：王泽
- 教育背景：国内985本科，计算机科学
- 工作经历：京东P3产品经理，3年工作经验
- 申请目标：2027年秋季MBA

## 职业背景
- 当前职位：外卖前台产品经理
- 主要职责：页面优化、营销活动、拉新、渠道运营
- 核心成果：新用户转化率提升15%，GMV增长2400万/年

## 申请动机
想系统学习商业战略和组织管理，未来目标是...
```

2. **工作经历.md** - 详细的项目列表

```markdown
# 工作经历

## 项目1：外卖新用户转化优化
- 时间：2024.03 - 2024.08
- 团队规模：跨部门15人（运营/技术/设计）
- 背景：新用户首单转化率低于行业水平
- 行动：设计A/B测试框架，优化落地页和优惠券策略
- 成果：转化率从12%提升到15%，GMV增长200万/月
- 领导力：协调3个团队，推动技术方案落地

## 项目2：AI工具集成
- 时间：2024.09 - 至今
- ...
```

### Step 1: 核心叙事线挖掘（15分钟AI对话）

```bash
cd /Users/niny/career-os/skills/career-essay-studio

python3 main.py --mode discover \
  --profile-file ~/Desktop/个人档案.md \
  --output-dir ~/Desktop/MBA文书
```

**输出**：`01_挖掘问题.json`

AI会生成5-7个挖掘性问题，例如：
- 哪个项目让你最有成就感？为什么？
- 工作中最大的frustration是什么？
- 你最想解决的商业/社会问题是什么？

**你的任务**：认真回答这些问题，保存为 `核心叙事线.md`

示例回答：
```markdown
# 核心叙事线

## 主线：技术如何重塑商业模式与组织效率

## Hook瞬间
2024年，当我看到Claude AI让外卖运营效率提升30%时，我意识到技术不仅改变产品，更在重塑商业模式和组织协作方式。

## 微观+宏观
- 微观：外卖产品优化、AI工具集成
- 宏观：数字化转型、平台经济

## 理论+实践
- 理论：平台经济、网络效应
- 实践：实际项目落地、跨部门协调

## 为什么这条线让我有感触
因为我亲眼看到技术如何改变一线运营人员的工作方式...
```

### Step 2: 素材筛选（AI处理5分钟）

```bash
python3 main.py --mode select \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --experience-file ~/Desktop/工作经历.md \
  --output-dir ~/Desktop/MBA文书
```

**输出**：`02_筛选素材.json`

AI会：
- 评估每段经历与叙事线的相关性（0-100分）
- 对核心素材提炼highlight（商业成果、领导力）
- 对次要素材提供处理策略

### Step 3: 生成主文书初稿（AI处理10分钟）

```bash
python3 main.py --mode draft \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --material-file ~/Desktop/MBA文书/02_筛选素材.json \
  --target-school "Harvard Business School" \
  --output-dir ~/Desktop/MBA文书
```

**输出**：
- `03_主文书_Harvard_Business_School_初稿.md`（900词框架）
- `03_改写建议_Harvard_Business_School.md`（改写指南）

### ⚠️ Step 4: 人工大幅改写（2-3小时，最关键！）

**这是最重要的步骤！AI生成的是框架，你必须完全重写！**

改写检查清单：
- [ ] 删除AI buzzword（leverage、synergy、utilize）
- [ ] 改用你平时的表达方式
- [ ] 补充具体细节（时间、地点、对话、情感）
- [ ] 每个数字必须真实可验证
- [ ] 引用具体HBS教授姓名和研究
- [ ] 增加个人思考和洞察

### Step 5: 适配其他学校（AI处理5分钟/校）

```bash
python3 main.py --mode adapt \
  --master-essay ~/Desktop/MBA文书/主文书_HBS_改写版.md \
  --target-school "Stanford GSB" \
  --word-limit 1150 \
  --output-dir ~/Desktop/MBA文书
```

**输出**：`04_适配版本_Stanford_GSB.md`

## 支持的商学院（2026）

| 学校 | 字数 | 主题 | AI政策 | Disclosure |
|------|------|------|--------|-----------|
| Harvard Business School | 900 | Goals + leadership | 🔴严格 | ✅需要 |
| Stanford GSB | 1150 | What matters most | 🟡中等 | ❌不需要 |
| Wharton | 1000 | Career goals + fit | 🟡中等 | ❌不需要 |
| Columbia CBS | 500 | Why MBA now | 🔴严格 | ✅需要 |
| Kellogg | 450 | Leadership | 🔴严格 | ✅需要 |
| MIT Sloan | 600 | Unique perspective | 🟡中等 | ❌不需要 |
| Chicago Booth | 600 | Personal journey | 🟡中等 | ❌不需要 |

## AI使用合规指南

### ✅ 允许的用途
- Brainstorming（头脑风暴）
- Idea generation（创意激发）
- Outline creation（大纲生成）
- Editing & proofreading（编辑校对）
- Structure suggestions（结构建议）

### ❌ 禁止的用途
- Direct essay generation（直接生成全文）
- Copy-paste AI output（复制粘贴AI输出）
- Replacing personal reflection（替代个人思考）

### Disclosure模板（如需要）

如果学校要求AI disclosure：

```
I used AI tools (Claude) to:
1. Brainstorm narrative themes based on my career experiences
2. Organize my work experiences into a structured outline
3. Receive feedback on essay structure and flow
4. Proofread and edit my final draft

All core ideas, reflections, and personal stories are entirely my own.
The AI served only as a thinking partner and editing assistant.
```

## 在职申请者特别建议

### 突出工作项目成果
- ❌ "负责产品优化"
- ✅ "通过A/B测试将转化率提升15%，年化收入增长2400万"

### 展现领导力
- ❌ "参与跨部门项目"
- ✅ "协调运营/技术/设计3个团队（15人），推动AI工具集成"

### 连接MBA学习目标
- ❌ "想学习更多商业知识"
- ✅ "希望系统学习平台战略（HBS Prof. XXX课程），为打造B2B SaaS产品做准备"

## 常见错误避免

### ❌ 简历扩写症
罗列所有项目，堆砌数字和名词。文书应该展现"人"的独特性。

### ❌ AI腔调过重
使用"leverage"、"synergy"等buzzword。必须用自己的语言重写。

### ❌ 缺乏具体细节
"我很有领导力" → 说出具体场景、对话、冲突、决策过程

### ❌ 选校理由套话
"贵校历史悠久" ❌  
"Prof. XXX的《YYY》研究和我的ZZZ项目高度相关" ✅

## 输出目录结构

```
~/Desktop/MBA文书/
├── 01_挖掘问题.json              # Step 1输出
├── 核心叙事线.md                 # 你手动创建
├── 02_筛选素材.json              # Step 2输出
├── 03_主文书_HBS_初稿.md         # Step 3输出
├── 03_改写建议_HBS.md            # Step 3输出
├── 主文书_HBS_改写版.md          # 你手动改写
├── 04_适配版本_Stanford_GSB.md  # Step 5输出
└── ...
```

## 完整工作流时间估算

| 步骤 | 时间 | 说明 |
|------|------|------|
| 准备材料 | 30分钟 | 整理个人档案和工作经历 |
| AI挖掘叙事线 | 15分钟 | AI生成问题 + 你回答 |
| AI筛选素材 | 5分钟 | AI自动处理 |
| AI生成初稿 | 10分钟 | AI生成结构框架 |
| **人工改写** | **2-3小时** | **最关键！完全重写** |
| Native speaker校对 | 1-2小时 | 润色语言 |
| MBA校友review | 1小时 | 获取反馈 |
| 适配其他学校 | 30分钟/校 | AI快速拆分 |

**总计**：第一所学校约5-7小时，后续学校约1小时/校

## 环境变量配置

```bash
# 配置Claude API Key
export ANTHROPIC_API_KEY="sk-ant-..."

# 或写入配置文件
echo '{"ANTHROPIC_API_KEY": "sk-ant-..."}' > ~/career-os/config/api_keys.json
```

## 注意事项

### ⚠️ 真实性红线
- AI只能基于真实经历生成素材
- 严禁虚构项目和数据
- 所有商业成果必须可验证

### ⚠️ AI使用透明
- 了解目标学校的AI政策
- 严格禁止的学校只能用AI做brainstorming
- 需要disclosure的学校必须声明

### ⚠️ 人工改写必须
- AI生成的是框架，不是final draft
- 必须融入你的个人语言风格
- 增加具体细节和情感

## 技术支持

如有问题，请查看：
- Skill文档：`SKILL.md`
- Career OS主文档：`../../README.md`

## Sources

本系统基于以下最佳实践设计：
- [MBA Applicant's Guide To AI (2026)](https://poetsandquants.com/2026/05/26/the-mba-applicants-guide-to-ai-in-2026-whats-allowed-whats-risky-and-what-to-avoid/)
- [AI & MBA Essays - Fortuna Admissions](https://fortunaadmissions.com/mba/ai-mba-essays/)
- [MBA Applications and AI - Menlo Coaching](https://menlocoaching.com/mba-applications-and-admissions-guide/mba-admissions-and-ai/)
- [Statement of Purpose Writing Guide](https://www.karangupta.com/guides/statement-of-purpose-sop-writing-guide)
- [Stanford Statement of Purpose Guide](https://online.stanford.edu/how-write-compelling-statement-purpose-graduate-school)
