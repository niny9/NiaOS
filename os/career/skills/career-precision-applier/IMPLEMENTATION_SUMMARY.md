# Career Precision Applier - 补充总结

## 已完成工作

### 1. 创建新Skill：career-precision-applier

**位置**：`/Users/niny/career-os/skills/career-precision-applier/`

**核心文件**：
- `SKILL.md` - Skill完整文档（功能说明、集成方式、使用场景）
- `main.py` - 可执行的Python实现（支持4个模式：match/rewrite/generate/review）
- `README.md` - 用户使用指南（从安装到复盘的完整流程）

### 2. 更新Career OS文档

**修改文件**：`/Users/niny/career-os/SKILLS_INVENTORY.md`

**变更内容**：
- 新增第13个Skill：career-precision-applier（标记为🚧新增，优先级P0）
- 新增工作流6：精准投递工作流（4步流程图）
- 更新Skills总数：13个（12个已完成，1个新增）

## 功能定位

### 填补的空缺

1. **岗位匹配挖掘**
   - 现有：career-match-engine计算单个岗位匹配度
   - 新增：基于简历推荐TOP10岗位 + 能力拆解（硬技能/软技能）

2. **STAR简历改写**
   - 现有：career-resume-studio生成通用简历
   - 新增：STAR格式重构（情境-任务-行动-结果） + 可复用素材库

3. **定向物料生成**
   - 现有：career-apply-ops记录投递状态
   - 新增：一岗一版定制简历 + 打招呼话术 + 岗位台账

4. **投递复盘迭代**
   - 现有：无
   - 新增：分析投递效果（已读率、面试率、最佳案例）

### 与现有Skills的协作

```
career-asset-hub（项目经历） ─────┐
                                  ├──> career-precision-applier (Step 1-2)
career-resume-studio（通用简历）──┘      ↓
                                    岗位匹配表 + STAR简历底稿
                                         ↓
                用户手动筛选BOSS岗位，复制JD
                                         ↓
                           career-precision-applier (Step 3)
                                         ↓
                           定制简历 + 打招呼话术
                                         ↓
                              用户手动投递
                                         ↓
                           career-precision-applier (Step 4)
                                         ↓
                    career-apply-ops（状态追踪）+ 投递复盘报告
```

## 核心特性

### 1. 安全第一
- ❌ 不使用爬虫抓取岗位（避免封号）
- ❌ 不自动发送消息（避免封号）
- ✅ AI生成物料，人工投递
- ✅ 定制简历只用PDF附件，不改平台在线简历

### 2. 真实性保障
- ✅ AI只重组真实经历，不虚构项目/数据
- ✅ 所有经历必须可核验
- ✅ 量化数据必须真实，无数据就写客观成果

### 3. 高效批量处理
- ✅ 一天可生成几十份定制简历
- ✅ STAR素材库可复用，按需抽取
- ✅ 岗位台账统一管理，便于复盘

## 工作流示例

### 场景：应届生/转行求职AI产品经理

```bash
# 周末：准备基础材料（30分钟）
# 1. 整理原始简历：~/Desktop/我的简历.md
# 2. 写求职约束：~/Desktop/求职约束.txt

# 周一：生成岗位推荐和STAR简历（10分钟AI处理）
cd /Users/niny/career-os/skills/career-precision-applier
python3 main.py --mode full \
  --resume-file ~/Desktop/我的简历.md \
  --constraints-file ~/Desktop/求职约束.txt \
  --output-dir ~/Desktop/精准投递

# 周二-周三：筛选岗位（1-2小时）
# 去BOSS直聘，根据TOP10推荐搜索岗位
# 把感兴趣的20个岗位JD复制到 ~/Desktop/JDs/*.txt

# 周四：批量生成定制简历（10分钟AI处理）
for jd_file in ~/Desktop/JDs/*.txt; do
  python3 main.py --mode generate \
    --jd-file "$jd_file" \
    --resume-base ~/Desktop/精准投递/02_STAR简历底稿.md \
    --output-dir ~/Desktop/精准投递
done

# 周五：手动投递（2-3小时）
# 1. 查看岗位台账，找匹配度>80分的岗位
# 2. 用Typora将定制简历导出PDF
# 3. 去BOSS投递：上传PDF + 复制话术（微调后发送）
# 注意：分批投递，避免短时间大量投递

# 下周一：投递复盘（5分钟）
# 更新台账中的is_read和got_interview字段
python3 main.py --mode review \
  --ledger-file ~/Desktop/精准投递/04_岗位台账.jsonl \
  --output-dir ~/Desktop/精准投递

# 查看复盘报告，优化策略：
# - 哪类岗位面试率高？多投这类
# - 哪个STAR案例效果好？放到简历前面
# - 需要补充什么案例？找项目补充素材库
```

## 技术实现

### 依赖
- Python 3.8+
- anthropic SDK
- Career OS现有utils（feishu_notifier）

### API调用
- 使用Claude Sonnet 4.6
- 支持自定义base_url（兼容cc-vibe等代理）
- 从环境变量或config文件读取API Key

### 数据格式
- 输入：Markdown简历、纯文本求职约束、纯文本JD
- 输出：JSON（岗位匹配表、台账）+ Markdown（简历、素材库）

## 后续优化方向

### P0（必须做）
- [ ] 添加单元测试
- [ ] 错误处理优化（API调用失败重试、JSON解析异常）
- [ ] 添加日志记录

### P1（建议做）
- [ ] 集成到career-orchestrator自动化工作流
- [ ] 添加飞书通知（任务完成提醒）
- [ ] 支持批量模式（一次处理多个JD）

### P2（可选做）
- [ ] 添加简历模板选择（不同风格）
- [ ] 支持英文简历生成
- [ ] 集成PDF导出功能

## 使用建议

### 适合人群
1. **应届生/转行**：不知道自己适合什么岗位
2. **海投疲劳**：手动定制每份简历太累
3. **面试率低**：简历千篇一律，没有针对性

### 不适合人群
1. **已有明确目标岗位**：直接用career-resume-studio生成定制简历即可
2. **只投几个岗位**：手动定制即可，不需要批量工具
3. **经历较少**：STAR案例不足3个，难以形成素材库

### 最佳实践
1. **先质后量**：Step 1-2做好基础，Step 3才能批量提效
2. **持续迭代**：每周复盘，优化简历素材库
3. **人工把关**：AI生成内容必须人工审核，去除AI腔
4. **控制节奏**：不要短时间大量投递，避免平台风控

## 文件清单

```
/Users/niny/career-os/skills/career-precision-applier/
├── SKILL.md           # Skill完整文档
├── README.md          # 用户使用指南  
└── main.py            # Python实现（可执行）

/Users/niny/career-os/
└── SKILLS_INVENTORY.md  # 已更新：新增Skill条目和工作流
```

## 总结

这个Skill完整实现了视频中的AI求职投递工作流，但做了关键的安全取舍：

✅ **保留**：岗位匹配、STAR简历改写、定向物料生成、投递复盘  
❌ **舍弃**：自动爬岗位、自动投递（高风险，会封号）  
✨ **改进**：AI生成物料 + 人工投递，兼顾效率和账号安全

现在Career OS从"自动化求职准备"扩展到"精准投递全流程"，覆盖从岗位发现到投递复盘的完整链路。
