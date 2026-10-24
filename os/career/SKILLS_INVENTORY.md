# Career OS - 完整功能清单

> 2026-10-25：统一周检已纳入核心工作流，唯一入口为 [career-weekly-review](skills/career-weekly-review/SKILL.md)。每周自动运行，复用现有 `career-os` 任务（周一 09:00，Asia/Shanghai）。下方旧组件状态为历史登记，不代表本次重新验证了安装、通知或完整 runtime。公开 Skill 与私有运行数据的边界见 [接入说明](skills/career-weekly-review/references/integration.md)。

## 📊 Skills 总览

| # | Skill 名称 | 状态 | 优先级 | 功能描述 | 自动化 |
|---|-----------|------|--------|---------|--------|
| 1 | career-intake | ✅ 已完成 | P0 | 用户档案初始化 | 手动 |
| 2 | career-asset-hub | ✅ 已完成 | P0 | 跨 OS 资产聚合 | 手动 |
| 3 | career-resume-studio | ✅ 已完成 | P0 | 简历生成（nia_style） | 手动 |
| 4 | career-job-radar | ✅ 已完成 | P0 | 职位监控（Chrome扩展） | 每周一 9:00 |
| 5 | career-match-engine | ✅ 已完成 | P0 | 智能匹配引擎 | 自动触发 |
| 6 | career-timeline-manager | ✅ 已完成 | P0 | 时间线管理 | 每天 8:00 |
| 7 | career-orchestrator | 已接入统一周检 | P0 | 复用输入、调度、运行与回写状态 | 自动触发 |
| 8 | career-monthly-review | 已接入统一周检 | P1 | 聚合周报与既有 Registry，不重复建闭环 | 每月 1 号 9:00（沿用） |
| 9 | career-apply-ops | ✅ 已完成 | P1 | 投递追踪 | 手动 |
| 10 | career-email-monitor | ✅ 已完成 | P1 | 邮件监控 | 后台运行 |
| 11 | career-direction-predictor | ✅ 已完成 | P1 | 方向预测 | 手动 |
| 12 | career-interview-lab | ✅ 已完成 | P1 | 面试准备 | 手动 |
| 13 | career-precision-applier | 🚧 新增 | P0 | 精准投递工作流 | 手动 |
| 14 | [career-weekly-review](skills/career-weekly-review/SKILL.md) | 已统一 | P0 核心 | 市场、项目审计、12维能力、Resume Gate、Top3、Stop-Doing、原台账回写 | **每周自动运行：周一 09:00 Asia/Shanghai；复用 career-os** |
| 15 | career-reflection | 已有组件 | P1 | 单个 case 写入原 Career Learning Log，供周检引用 | 按 case 触发 |
| 16 | career-essay-studio | 已有组件 | P1 | 文书资产，消费已核实成果 | 手动 |

**共登记 16 个 Skill；本次统一每周流程，未重新审计所有历史组件运行状态。**

---

## 🎯 核心工作流

### 0. 统一 Career OS 周检（每周自动运行）

唯一 Skill：`career-weekly-review`，口头别名 `career-os-weekly-review`。沿用原 job radar / monthly review / orchestrator；不新建平行 Career OS、Log 或 Registry。

```text
career-orchestrator → career-job-radar（同次快照复用）
    → career-weekly-review（逐项目审计 → 12维 → Resume Asset Gate）
    → Top3 / Stop-Doing → 原 Career Learning Log、Market / Insight / Decision Registry
    → 既有 Gap Matrix / Project Cards / reports/weekly
```

**每周固定输出：** 市场/岗位变化、项目逐项审计、能力缺口变化、新增可证明资产、最危险偏航点、Top3、停止/降投入、待补证据项目。安全、隐私、可靠性、成本、延迟横向贯穿。

**自动化：** 复用现有 Codex `career-os`，每周一 09:00 Asia/Shanghai；从 GitHub 加载唯一 Skill，使用原私有数据根。没有新增 cron，也不把 Skill 文档视为完整运行器；实际成功以每次回写与报告验收为准。

**路由与写回：** [工作流入口](workflows/weekly-career-review.md) · [数据绑定/幂等回写](skills/career-weekly-review/references/integration.md) · [评分与公司池](skills/career-weekly-review/references/targets-and-scoring.md) · [周报合同](skills/career-weekly-review/references/weekly-report.md)。未定位的 Registry 只在主报告列 pending mutation，不创建替代总账。

### 1. 职位监控工作流（统一周检的市场输入）

```
career-job-radar (扫描职位)
    ↓
career-match-engine (计算匹配度)
    ↓
飞书通知（推送结果）
```

**触发方式：** 沿用已有雷达调度/周检编排，同次快照复用；不新增第二次扫描。
**输出：** 有来源的职位列表；个人能力与 Top3 由统一周检审计。旧通知只按已有授权执行。

### 2. 月度复盘工作流（每月 1 号 9:00）

```
career-monthly-review (生成复盘报告)
    ↓
career-asset-hub (聚合资产变化)
    ↓
career-direction-predictor (预测方向)
    ↓
飞书通知（推送报告）
```

**触发方式：** Cron 定时任务
**输出：** 聚合既有周报与 Registry 的月度复盘报告，证据/评分/Gate 沿用统一周检。

### 3. 时间线检查工作流（每天 8:00）

```
career-timeline-manager (检查里程碑)
    ↓
飞书通知（提醒关键节点）
```

**触发方式：** Cron 定时任务
**输出：** 时间线提醒

### 4. 简历生成工作流（手动触发）

```
career-intake (读取用户档案)
    ↓
career-asset-hub (聚合项目经验)
    ↓
career-weekly-review Resume Asset Gate (核验事实、个人归因、公开范围)
    ↓
career-resume-studio (仅消费通过 Gate 的 claims)
    ↓
输出 Markdown + PDF
```

**触发方式：** 手动命令
**输出：** 定制化简历

### 5. 投递追踪工作流（手动触发）

```
career-apply-ops (记录投递)
    ↓
career-interview-lab (准备面试)
    ↓
飞书通知（面试提醒）
```

**触发方式：** 手动命令
**输出：** 投递记录 + 面试准备

### 6. 精准投递工作流（手动触发）🆕

```
career-precision-applier (岗位匹配挖掘)
    ↓
career-precision-applier (STAR简历改写)
    ↓
career-precision-applier (定向物料生成)
    ↓
人工投递 (手动操作)
    ↓
career-precision-applier (投递复盘迭代)
```

**触发方式：** 手动命令
**输出：** TOP10岗位推荐 + STAR简历底稿 + 定制简历PDF + 打招呼话术 + 投递复盘报告
**核心特点：** AI生成投递物料，人工投递（避免封号），一岗一版定制简历

---

## 📁 数据资产

### 用户档案
- **位置：** `data/profiles/nia_001.json`
- **内容：** 王泽, P3@JD, 目标 AI 产品商业化负责人
- **目标时间：** 2027.2

### 简历库
- **位置：** `data/resumes/registry.jsonl`
- **数量：** 186 份真实简历
- **用途：** 学习排版风格、提取项目经验

### 简历模板
- **位置：** `templates/resume_templates/nia_style_ai_pm.md`
- **特点：** 学习了用户的真实简历风格
- **格式：** STAR 格式，加粗关键指标

### 职位数据
- **位置：** `data/jobs/manual_jobs.json`
- **来源：** Chrome 扩展收集
- **更新：** 每周手动收集

### 时间线
- **位置：** `data/timelines/nia_001_timeline.json`
- **里程碑：**
  - 2026.8 - 能力提升阶段
  - 2026.10 - 简历优化
  - 2026.12 - 开始投递
  - 2027.1 - 面试高峰
  - 2027.2 - 入职目标

---

## 🛠️ 工具集成

### Chrome 扩展
- **名称：** Career OS 职位收集助手
- **功能：** 一键收集 Boss直聘、拉勾网职位
- **位置：** `chrome-extension/`
- **状态：** ✅ 已安装

### 飞书通知
- **Webhook：** 已配置
- **通知类型：**
  - 职位监控更新
  - 月度复盘报告
  - 时间线提醒
  - 任务执行失败

### Cron 定时任务
- **配置文件：** `scripts/install_cron.sh`
- **状态：** ✅ 已安装
- **任务：**
  - 每周一 9:00 - 职位监控
  - 每月 1 号 9:00 - 月度复盘
  - 每天 8:00 - 时间线检查

### Obsidian 集成
- **Vault 位置：** `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Career OS`
- **文档结构：** 8 个主文件夹（00_Inbox 到 08_资源）
- **模板：**
  - 职位模板 - 用于记录和分析职位信息
  - 面试文字稿模板 - 用于记录面试对话
  - 面试复盘模板 - 用于生成结构化复盘
- **自动化功能：**
  - 基于 JD 生成定制简历（`utils/resume_generator.py`）
  - AI 驱动的面试复盘（`utils/interview_reviewer.py`）
- **详细文档：** `docs/OBSIDIAN_STRUCTURE_DESIGN.md`

---

## 📖 使用指南

### 快速开始
```bash
# 查看快速开始指南
cat ~/career-os/docs/QUICK_START.md

# 查看 Chrome 扩展使用
cat ~/career-os/chrome-extension/README.md
```

### 常用命令

**职位监控：**
```bash
cd ~/career-os/skills/career-job-radar
python3 main.py --mode scan --profile-id nia_001
```

**生成简历：**
```bash
cd ~/career-os/skills/career-resume-studio
python3 main.py --profile-id nia_001 --template nia_style --output ~/Desktop/
```

**针对 JD 生成定制简历：**
```bash
python3 ~/career-os/utils/resume_generator.py \
  --profile-id nia_001 \
  --job-file "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Career OS/02_职位管理/活跃职位/字节跳动_AI产品负责人.md"
```

**面试复盘自动化：**
```bash
python3 ~/career-os/utils/interview_reviewer.py \
  --transcript-file "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Assets/Career OS/00_Inbox/面试文字稿/2026-05-27_字节跳动_一面.md"
```

**月度复盘：**
```bash
cd ~/career-os/skills/career-monthly-review
python3 main.py --mode review --profile-id nia_001 --format md
```

**查看时间线：**
```bash
cd ~/career-os/skills/career-timeline-manager
python3 main.py --mode check --profile-id nia_001
```

---

## 🎯 下一步计划

### 短期优化（1-2 周）
- [ ] 优化 Chrome 扩展自动同步
- [ ] 增强简历生成的 AI 优化
- [ ] 添加更多简历模板

### 中期优化（1-2 月）
- [ ] 集成 LinkedIn 职位
- [ ] 自动投递功能
- [ ] 面试题库扩充

### 长期优化（3-6 月）
- [ ] AI 智能推荐
- [ ] 薪资谈判助手
- [ ] Offer 对比分析

---

## 📊 系统状态

**本次更新：** 2026-10-25
**核心入口：** career-weekly-review；工作流复用既有 radar、reflection、monthly review、orchestrator 与简历生成组件。
**自动化频率：** 每周一 09:00 Asia/Shanghai，沿用 ACTIVE 的 career-os 任务；未来运行结果需逐次验证。
**数据边界：** 公开仓库保存 Skill/接入合同；既有私有 Log、Registry、Project Cards、证据库继续作为事实来源。
**已知限制：** GitHub 当前未包含完整本地 runtime；Career Insight Registry 的独立同名文件未定位，运行时应解析既有 Log/台账绑定，失败写入待补项，不新建平行系统。
