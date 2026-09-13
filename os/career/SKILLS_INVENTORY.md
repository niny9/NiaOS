# Career OS - 完整功能清单

## 📊 Skills 总览

| # | Skill 名称 | 状态 | 优先级 | 功能描述 | 自动化 |
|---|-----------|------|--------|---------|--------|
| 1 | career-intake | ✅ 已完成 | P0 | 用户档案初始化 | 手动 |
| 2 | career-asset-hub | ✅ 已完成 | P0 | 跨 OS 资产聚合 | 手动 |
| 3 | career-resume-studio | ✅ 已完成 | P0 | 简历生成（nia_style） | 手动 |
| 4 | career-job-radar | ✅ 已完成 | P0 | 职位监控（Chrome扩展） | 每周一 9:00 |
| 5 | career-match-engine | ✅ 已完成 | P0 | 智能匹配引擎 | 自动触发 |
| 6 | career-timeline-manager | ✅ 已完成 | P0 | 时间线管理 | 每天 8:00 |
| 7 | career-orchestrator | ✅ 已完成 | P0 | 工作流编排 | 自动触发 |
| 8 | career-monthly-review | ✅ 已完成 | P1 | 月度复盘 | 每月 1 号 9:00 |
| 9 | career-apply-ops | ✅ 已完成 | P1 | 投递追踪 | 手动 |
| 10 | career-email-monitor | ✅ 已完成 | P1 | 邮件监控 | 后台运行 |
| 11 | career-direction-predictor | ✅ 已完成 | P1 | 方向预测 | 手动 |
| 12 | career-interview-lab | ✅ 已完成 | P1 | 面试准备 | 手动 |
| 13 | career-precision-applier | 🚧 新增 | P0 | 精准投递工作流 | 手动 |

**总计：13 个 Skills，12个已完成，1个新增** ✅

---

## 🎯 核心工作流

### 1. 职位监控工作流（每周一 9:00）

```
career-job-radar (扫描职位)
    ↓
career-match-engine (计算匹配度)
    ↓
飞书通知（推送结果）
```

**触发方式：** Cron 定时任务
**输出：** 职位列表 + 匹配度评分

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
**输出：** 月度复盘报告

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
career-resume-studio (生成简历)
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

**最后更新：** 2026-05-27
**Skills 完成度：** 12/12 (100%)
**自动化覆盖：** 3 个核心工作流
**数据资产：** 186 份简历，用户档案已配置
**工具集成：** Chrome 扩展、飞书通知、Cron 定时任务

**系统状态：** ✅ 全部就绪，可正常使用
