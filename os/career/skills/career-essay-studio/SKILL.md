---
name: career-essay-studio
description: AI-powered MBA/EMBA application essay writing system - narrative architecture, material selection, and school-specific customization for working professionals
---

# Career Essay Studio

顶级商学院文书写作系统：为在职申请者设计的AI驱动文书工作流

## Purpose

解决MBA/EMBA申请文书写作的核心难题：
1. **不知道写什么** - 把简历经历转化为有灵魂的"成长小说"
2. **素材太多无法取舍** - 基于核心叙事线筛选和裁剪
3. **不知道怎么展现独特性** - 突出工作项目成果和商业影响力
4. **多校申请重复劳动** - 主文书拆分配比，快速适配

## Core Features

### Step 1: 核心叙事线挖掘
- 通过AI对话挖掘真正让你有感触的兴趣点
- 识别"惊讶/愤怒/醍醐灌顶"的关键时刻
- 构建微观+宏观、理论+实践的立体叙事结构
- **在职申请特化**：从工作项目中提炼商业洞察和领导力成长

### Step 2: 素材筛选与裁剪
- 基于核心叙事线评估每段经历的相关性
- 处理"鸡肋"经历的两种策略：
  - 强调通用能力（定量分析、团队协作、领导力）
  - 升华到精神层面（好奇心、创业精神、改变世界的意愿）
- **在职申请特化**：突出项目ROI、团队规模、商业影响

### Step 3: 工作项目STAR改写
- 将工作经历转化为STAR格式（Situation-Task-Action-Result）
- 强化商业成果（收入增长、成本节约、用户增长）
- 展现领导力（跨部门协调、团队管理、战略决策）
- 连接到MBA学习目标

### Step 4: 未来规划落点
- 从过去项目延伸到未来探索方向
- 结合具体学校的课程、教授、项目资源
- 适配不同方向（战略、创业、科技、金融）
- **在职申请特化**：展现职业转型逻辑或行业深耕计划

### Step 5: 主文书生成与拆分
- 生成1000词英文主文书（完整版）
- 根据学校字数要求拆分裁剪
- 适配不同主题（Why MBA, Leadership, Failure, Contribution）
- 引用具体教授研究和项目资源

## MBA/EMBA School-Specific Optimization

### 顶级商学院文书要求（2026）

| 学校 | 字数限制 | 核心主题 | AI使用政策 |
|------|---------|---------|-----------|
| HBS | 900词 | Post-MBA goals + leadership | 允许idea generation，禁止完整生成 |
| Stanford GSB | 1,150词 | What matters most to you | 未明确政策 |
| Wharton | 1,000词 | Career goals + Wharton fit | 未明确政策 |
| Columbia CBS | 500词 | Why MBA now | 允许editing，禁止完整生成 |
| Kellogg | 450词 | Leadership experience | 要求AI disclosure |
| MIT Sloan | Cover letter | Unique perspective | 未明确政策 |
| Chicago Booth | 250-600词 | Personal/professional journey | 未明确政策 |

**重要**：本系统生成的是**初稿素材和结构建议**，必须由申请者本人大幅改写，符合学校AI使用政策。

## Usage

```bash
# Step 1: 核心叙事线挖掘
python3 main.py --mode discover \
  --profile-file ~/Desktop/个人档案.md \
  --output-dir ~/Desktop/MBA文书

# Step 2: 素材筛选
python3 main.py --mode select \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --experience-file ~/Desktop/工作经历.md \
  --output-dir ~/Desktop/MBA文书

# Step 3: 主文书生成
python3 main.py --mode draft \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --material-file ~/Desktop/MBA文书/筛选素材.json \
  --target-school "Harvard Business School" \
  --output-dir ~/Desktop/MBA文书

# Step 4: 学校适配拆分
python3 main.py --mode adapt \
  --master-essay ~/Desktop/MBA文书/主文书_HBS.md \
  --target-school "Stanford GSB" \
  --word-limit 1150 \
  --output-dir ~/Desktop/MBA文书

# 完整流程（一次性执行Step 1-3）
python3 main.py --mode full \
  --profile-file ~/Desktop/个人档案.md \
  --experience-file ~/Desktop/工作经历.md \
  --target-school "Harvard Business School" \
  --output-dir ~/Desktop/MBA文书
```

## Output Schema

### Step 1 输出：核心叙事线
```json
{
  "core_narrative": {
    "title": "技术如何重塑商业模式与组织效率",
    "hook_moment": "2024年看到AI工具让外卖运营效率提升30%的震撼",
    "main_thread": "从产品经理视角探索技术驱动的商业创新",
    "micro_macro": {
      "micro": "外卖平台产品优化、AI工具集成",
      "macro": "数字化转型、组织效率革命"
    },
    "theory_practice": {
      "theory": "平台经济、网络效应",
      "practice": "实际项目落地、团队管理"
    }
  },
  "key_moments": [
    {
      "moment": "负责外卖新用户转化优化项目",
      "emotion": "醍醐灌顶",
      "insight": "数据驱动决策的威力",
      "connection_to_narrative": "技术工具如何改变产品决策范式"
    }
  ]
}
```

### Step 2 输出：筛选素材
```json
{
  "selected_experiences": [
    {
      "title": "外卖新用户转化优化项目",
      "relevance_score": 95,
      "reason": "核心叙事线直接相关",
      "highlight": "15%转化率提升，200万GMV增长",
      "leadership": "跨部门协调（运营/技术/设计）",
      "business_impact": "年化收入增长2400万"
    }
  ],
  "filtered_experiences": [
    {
      "title": "大学生心理健康研究",
      "relevance_score": 30,
      "strategy": "强调通用能力",
      "angle": "定量分析能力为后续产品数据分析打基础"
    }
  ]
}
```

### Step 3 输出：主文书
```markdown
# 主文书 - Harvard Business School (900词)

## Opening Hook (100词)
2024年，当我看到Claude AI工具让外卖运营效率提升30%时，我意识到技术不仅改变产品，更在重塑整个商业模式...

## Core Narrative (400词)
### 微观：产品实践
- 外卖新用户转化优化（15%提升，2400万收入）
- AI工具集成项目（30%效率提升）

### 宏观：商业洞察
- 平台经济的网络效应
- 技术驱动的组织变革

## Leadership & Growth (200词)
- 跨部门协调经验
- 从执行者到战略思考者的转变
- 团队管理与授权

## Why HBS Now (150词)
- Prof. XXX的《Platform Strategy》课程
- Digital Initiative项目资源
- 职业转型：从产品经理到产品战略负责人

## Contribution (50词)
- 中国互联网产品经验
- 技术与商业结合的独特视角
```

### Step 4 输出：学校适配版本
```json
{
  "school": "Stanford GSB",
  "word_limit": 1150,
  "theme": "What matters most to you",
  "adapted_structure": {
    "opening": "从产品优化到思考技术如何改变世界",
    "body_focus": "技术赋能商业创新的使命感",
    "gsb_specific": "引用Prof. YYY的创业课程",
    "adjustments": [
      "增强个人价值观叙述",
      "减少技术细节，增加人文关怀",
      "突出改变世界的愿景"
    ]
  }
}
```

## AI Usage Compliance

### 学校AI政策分类（2026）

**🔴 严格禁止完整生成（必须disclosure）**
- Harvard Business School
- Columbia Business School
- Kellogg School of Management
- Michigan Ross
- London Business School

**🟡 允许辅助但需谨慎**
- Stanford GSB
- Wharton
- MIT Sloan
- Chicago Booth

### 合规使用方式

1. **✅ 允许的用途**
   - Brainstorming（头脑风暴）
   - Idea generation（创意激发）
   - Outline creation（大纲生成）
   - Editing & proofreading（编辑校对）
   - Structure suggestions（结构建议）

2. **❌ 禁止的用途**
   - Direct essay generation（直接生成全文）
   - Copy-paste AI output（复制粘贴AI输出）
   - Replacing personal reflection（替代个人思考）

3. **本系统的定位**
   - 生成**结构框架**和**素材建议**
   - 提供**改写方向**和**优化建议**
   - 最终文书必须由申请者**完全重写**，融入个人语言风格

### Disclosure模板

如果学校要求AI disclosure，使用以下模板：

```
I used AI tools (Claude) to:
1. Brainstorm narrative themes based on my career experiences
2. Organize my work experiences into a structured outline
3. Receive feedback on essay structure and flow
4. Proofread and edit my final draft

All core ideas, reflections, and personal stories are entirely my own. 
The AI served only as a thinking partner and editing assistant.
```

## Integration with Career OS

### 数据输入
- **从 career-asset-hub 读取**：工作经历、项目成果
- **从 career-resume-studio 读取**：STAR格式简历
- **人工提供**：核心兴趣点、申请动机、职业目标

### 数据输出
- **输出位置**：`/Users/niny/Asset/Career OS/MBA文书/`
  - `01_核心叙事线.md`
  - `02_筛选素材.json`
  - `03_主文书_初稿/`
  - `04_学校适配版本/`
  - `05_改写建议.md`

### 与现有Skills协作
- **career-asset-hub**：提供工作项目经历
- **career-resume-studio**：提供STAR格式素材
- 本Skill专注于**文书叙事结构**和**学校适配**

## Workflow Example

### 场景：在职PM申请HBS MBA

```bash
# 准备输入材料（30分钟）
# 1. 个人档案.md：基本信息、教育背景、职业经历
# 2. 工作经历.md：详细项目列表（包含数据）
# 3. 申请动机.txt：为什么要读MBA

# Step 1: 挖掘核心叙事线（AI对话15分钟）
python3 main.py --mode discover \
  --profile-file ~/Desktop/个人档案.md

# AI会提问：
# - 哪个项目让你最有成就感？为什么？
# - 工作中最大的frustration是什么？
# - 你最想解决的商业/社会问题是什么？
# 输出：核心叙事线.md

# Step 2: 筛选素材（AI处理5分钟）
python3 main.py --mode select \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --experience-file ~/Desktop/工作经历.md

# 输出：筛选素材.json（按相关性排序）

# Step 3: 生成HBS主文书初稿（AI处理10分钟）
python3 main.py --mode draft \
  --narrative-file ~/Desktop/MBA文书/核心叙事线.md \
  --material-file ~/Desktop/MBA文书/筛选素材.json \
  --target-school "Harvard Business School"

# 输出：主文书_HBS_初稿.md（900词）

# Step 4: 人工大幅改写（2-3小时）
# - 去除AI腔调
# - 融入个人语言风格
# - 补充具体细节和情感
# - 引用具体HBS资源

# Step 5: 适配其他学校（AI处理5分钟/校）
python3 main.py --mode adapt \
  --master-essay ~/Desktop/MBA文书/主文书_HBS_改写版.md \
  --target-school "Stanford GSB" \
  --word-limit 1150

# 输出：主文书_Stanford_初稿.md
```

## Best Practices for Working Professionals

### 1. 突出商业成果
- ❌ "负责外卖产品优化"
- ✅ "通过A/B测试和数据分析，将新用户转化率提升15%，年化收入增长2400万"

### 2. 展现领导力
- ❌ "参与跨部门项目"
- ✅ "协调运营、技术、设计3个团队（15人），推动AI工具集成，将运营效率提升30%"

### 3. 连接MBA学习目标
- ❌ "想学习更多商业知识"
- ✅ "希望系统学习平台战略（HBS Prof. XXX课程），为未来打造B2B SaaS产品做准备"

### 4. 处理职业转型
- 如果想转行：清晰解释Why now、Why this field、How MBA helps
- 如果想深耕：展现行业洞察深度，说明需要MBA提升什么维度

## Common Pitfalls to Avoid

### ❌ 最常见错误

1. **简历扩写症**
   - 罗列所有项目，堆砌数字和名词
   - 文书应该展现"人"的独特性，不是performance review

2. **AI腔调过重**
   - 使用"leverage"、"synergy"等buzzword
   - 必须用自己的语言重写，保留口语化表达

3. **缺乏具体细节**
   - "我很有领导力" → 说出具体场景
   - "我对技术充满热情" → 说出触发热情的moment

4. **选校理由套话**
   - "贵校历史悠久、声誉卓著" ❌
   - "Prof. XXX的《YYY》研究和我的ZZZ项目高度相关" ✅

5. **忽视学校文化差异**
   - HBS：领导力、case method
   - Stanford GSB：change the world、创业
   - Wharton：金融、量化分析
   - Kellogg：团队合作、marketing

## Technical Implementation

### 依赖
- Python 3.8+
- anthropic SDK (Claude API)
- Career OS现有utils

### AI Prompt Engineering

#### 核心叙事线挖掘Prompt
```
你是顶级商学院招生官，帮助申请者挖掘真实独特的文书主题。

规则：
1. 不要从"最大公约数"出发凑话题
2. 寻找让申请者真正有感触的moment（惊讶/愤怒/醍醐灌顶）
3. 构建微观+宏观、理论+实践的立体结构
4. 特别关注工作项目中的商业洞察和领导力成长

对话流程：
1. 询问最有成就感的项目
2. 挖掘背后的"为什么"
3. 连接到更大的商业/社会问题
4. 形成连贯的叙事线

申请者背景：
{profile}

开始对话。
```

## Safety & Ethics

### 真实性保障
✅ AI只能基于真实经历生成素材，严禁虚构项目和数据  
✅ 所有商业成果必须可验证  
✅ 必须由申请者本人大幅改写，融入个人风格  

### AI使用透明
✅ 明确告知用户学校AI政策  
✅ 提供disclosure模板  
✅ 强调AI只是辅助工具，不能替代个人思考  

### 数据隐私
✅ 个人档案和工作经历仅本地处理  
✅ 不上传到第三方服务  
✅ 敏感商业信息可匿名化处理  

## Next Steps

### P0（必须实现）
- [ ] 实现核心叙事线挖掘对话流程
- [ ] 实现素材筛选评分系统
- [ ] 实现主文书生成（HBS 900词模板）
- [ ] 添加学校AI政策checker

### P1（建议实现）
- [ ] 集成10所顶级商学院模板
- [ ] 添加AI腔调检测和改写建议
- [ ] 支持中英文双语输出
- [ ] 集成到career-orchestrator

### P2（可选实现）
- [ ] 添加peer review功能（对比其他申请者）
- [ ] 支持视频essay脚本生成
- [ ] 集成推荐信写作建议

## Sources & References

### 开源工具参考
- [Claude (Anthropic)](https://claude.ai) - 最佳长文写作AI (2026)
- [Paperguide AI](https://paperguide.ai) - 学术写作引用管理

### MBA文书最佳实践
- [MBA Applicant's Guide To AI (2026)](https://poetsandquants.com/2026/05/26/the-mba-applicants-guide-to-ai-in-2026-whats-allowed-whats-risky-and-what-to-avoid/)
- [AI & MBA Essays - Fortuna Admissions](https://fortunaadmissions.com/mba/ai-mba-essays/)
- [MBA Applications and AI - Menlo Coaching](https://menlocoaching.com/mba-applications-and-admissions-guide/mba-admissions-and-ai/)

### SOP写作框架
- [Statement of Purpose Writing Guide](https://www.karangupta.com/guides/statement-of-purpose-sop-writing-guide)
- [Stanford Statement of Purpose Guide](https://online.stanford.edu/how-write-compelling-statement-purpose-graduate-school)
- [MIT Graduate School Personal Statement](https://mitcommlab.mit.edu/be/commkit/graduate-school-personal-statement/)

---

**重要提醒**：本系统生成的是结构框架和素材建议，最终文书必须由申请者本人大幅改写，符合学校AI使用政策。AI不能替代个人思考和真实经历的表达。
