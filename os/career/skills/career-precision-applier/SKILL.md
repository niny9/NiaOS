---
name: career-precision-applier
description: AI-powered precise job application workflow - job matching, STAR resume rewriting, and customized application materials generation (greeting messages + tailored PDF resumes)
---

# Career Precision Applier

AI驱动的精准投递工作流：岗位匹配挖掘 → STAR简历改写 → 定向物料生成 → 投递复盘迭代

## Purpose

解决求职投递中的三大痛点：
1. **岗位选择迷茫** - 不知道自己适合什么岗位
2. **简历千篇一律** - 用同一份简历投所有岗位，匹配度低
3. **投递效率低** - 手动定制每份简历和打招呼话术，耗时长

## Core Features

### Step 1: 岗位匹配挖掘
- 基于原始简历 + 求职约束，AI推荐TOP10匹配岗位
- 拆解每个岗位的硬技能（工具/技术栈/证书）和软技能（协作/推进能力）
- 标注高薪赛道和所属行业

### Step 2: STAR简历改写
- 使用STAR法则（情境S、任务T、行动A、结果R）重构每段经历
- 自然植入岗位关键词，不堆砌
- 生成两份内容：
  - **通用STAR简历底稿**（可导出PDF）
  - **STAR素材库**（每条案例单独拆分，方便按需抽取）

### Step 3: 定向岗位物料生成
- 人工筛选岗位，复制JD
- AI生成：
  - **岗位匹配度评分**（0-100分 + 打分理由）
  - **定制附件简历**（基于JD关键词微调，一岗一版PDF）
  - **打招呼话术**（80字以内，突出1个核心匹配项目）
- 人工投递（避免平台封号风险）

### Step 4: 投递复盘迭代
- 记录投递3天后的结果：是否已读、是否获得面试邀约
- 统计分析：哪类岗位邀约率高、哪类STAR案例更有效
- 持续优化简历素材库和匹配关键词

## Usage

```bash
# Step 1: 岗位匹配挖掘
python3 main.py --mode match \
  --resume-file "<原始简历路径>" \
  --constraints-file "<求职约束路径>" \
  --output-dir "<输出目录>"

# Step 2: STAR简历改写
python3 main.py --mode rewrite \
  --resume-file "<原始简历路径>" \
  --keywords-file "<Step1关键词文件>" \
  --output-dir "<输出目录>"

# Step 3: 定向物料生成（单岗位）
python3 main.py --mode generate \
  --jd-file "<岗位JD文件>" \
  --resume-base "<STAR简历底稿>" \
  --output-dir "<输出目录>"

# Step 4: 投递复盘
python3 main.py --mode review \
  --ledger-file "<岗位台账文件>" \
  --output-dir "<输出目录>"

# 完整流程（一次性执行Step 1-2）
python3 main.py --mode full \
  --resume-file "<原始简历路径>" \
  --constraints-file "<求职约束路径>" \
  --output-dir "<输出目录>"
```

## Output Schema

### Step 1 输出：岗位匹配表
```json
{
  "top_positions": [
    {
      "position_name": "AI产品经理",
      "industry": "互联网",
      "high_salary_track": true,
      "hard_skills": ["Python", "Prompt工程", "Claude API", "数据分析"],
      "soft_skills": ["跨部门协作", "项目推进", "用户洞察"]
    }
  ]
}
```

### Step 2 输出：STAR简历底稿 + 素材库
```markdown
# 通用STAR简历底稿

## 工作经历

### 京东 - 产品经理（2023.06 - 至今）
**S（情境）**：负责外卖前台产品优化...
**T（任务）**：提升新用户转化率...
**A（行动）**：设计并落地A/B测试...
**R（结果）**：新用户转化率提升15%，GMV增长200万/月

---

# STAR素材库

## 案例1：外卖新用户转化优化
- **适用岗位**：增长产品、用户产品
- **STAR回答**：...
- **关键数据**：15%转化率提升、200万GMV增长
```

### Step 3 输出：岗位台账
```json
{
  "position": "字节跳动_AI产品经理",
  "company": "字节跳动",
  "jd_link": "https://...",
  "match_score": 85,
  "match_reason": "AI产品经验强、缺少toB经验",
  "customized_resume": "<定制简历markdown>",
  "greeting_message": "您好，我是王泽。看到贵司AI产品经理岗位，我在京东负责过用户增长AI应用（Claude API集成），实现15%转化率提升，希望能聊聊。",
  "applied_date": "2026-09-13",
  "is_read": false,
  "got_interview": false
}
```

### Step 4 输出：投递复盘报告
```json
{
  "total_applied": 20,
  "total_read": 12,
  "total_interview": 5,
  "read_rate": 60,
  "interview_rate": 25,
  "insights": {
    "best_position_type": "用户增长产品",
    "best_star_case": "外卖新用户转化优化",
    "suggested_optimization": "增加toB案例，提升大客户产品匹配度"
  }
}
```

## Integration

### 数据输入
- **从 career-asset-hub 读取**：项目经历、技能清单
- **从 career-resume-studio 读取**：原始简历文档
- **人工提供**：求职约束（目标城市、期望薪资、避雷公司）

### 数据输出
- **写入 career-apply-ops**：岗位台账、投递记录
- **输出位置**：`/Users/niny/Asset/Career OS/精准投递/`
  - `01_岗位匹配表.json`
  - `02_STAR简历底稿.md`
  - `03_STAR素材库/`
  - `04_岗位台账.jsonl`
  - `05_投递复盘报告.json`

### 与现有Skill协作
- **career-match-engine**：提供岗位匹配度计算能力，本Skill专注于**基于简历的岗位推荐**
- **career-resume-studio**：生成通用简历，本Skill专注于**一岗一版定制简历PDF**
- **career-apply-ops**：追踪投递状态，本Skill专注于**定向物料生成和投递复盘**

## Safety Rules（强制风险检查清单）

✅ **真实性红线**：AI仅做内容重组润色，严禁虚构项目、业绩数据，所有经历必须真实可核验  
✅ **账号安全**：不使用爬虫/脚本抓取岗位、自动发送消息，规避封号风险  
✅ **简历版本管理**：差异化简历只使用PDF附件，不改动平台在线简历  
✅ **AI腔去除**：所有输出必须人工核验，保证经历真实、去除AI腔  
✅ **投递节奏控制**：控制投递密度，拒绝短时间批量海投  
✅ **关键词自然融入**：关键词自然融入简历，禁止强行堆砌，减少AI简历特征

## Workflow Boundaries

- **可以做的**：岗位筛选、简历定制、物料生成、批量处理（一天几十个岗位物料）
- **必须人工做的**：投递、浏览岗位、发送消息（避免平台风控）
- **不保证的**：固定的面试邀约转化率（受个人背景、市场供需影响）

## Example Use Case

```bash
# 场景：用户想找AI产品经理岗位

# Step 1: 生成岗位推荐
python3 main.py --mode match \
  --resume-file ~/Asset/Career\ OS/01_简历库/通用简历/王泽_AI产品经理_通用简历_CH.md \
  --constraints-file ~/Desktop/求职约束.txt

# 输出：TOP10岗位 + 能力拆解

# Step 2: STAR简历改写
python3 main.py --mode rewrite \
  --resume-file ~/Asset/Career\ OS/01_简历库/通用简历/王泽_AI产品经理_通用简历_CH.md \
  --keywords-file ~/Asset/Career\ OS/精准投递/01_岗位匹配表.json

# 输出：STAR简历底稿 + 素材库

# Step 3: 用户手动去BOSS筛选岗位，复制JD，批量生成物料
for jd_file in ~/Desktop/JDs/*.txt; do
  python3 main.py --mode generate \
    --jd-file "$jd_file" \
    --resume-base ~/Asset/Career\ OS/精准投递/02_STAR简历底稿.md
done

# 输出：岗位台账（含定制简历 + 打招呼话术）

# Step 4: 用户手动投递，3天后更新台账，生成复盘
python3 main.py --mode review \
  --ledger-file ~/Asset/Career\ OS/精准投递/04_岗位台账.jsonl

# 输出：投递复盘报告（哪类岗位邀约率高、如何优化）
```

## Next Steps

1. **实现main.py核心逻辑**：4个模式的调度和AI Prompt
2. **集成Claude API**：使用career-os已有的API配置
3. **添加到career-orchestrator**：作为可选工作流模块
4. **用户测试**：用真实简历测试完整流程，优化Prompt
