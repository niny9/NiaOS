# Career Precision Applier - 使用指南

## 快速开始

### 前置准备

1. 准备两个文本文件：
   - **原始简历**：你的完整简历（markdown格式）
   - **求职约束**：目标城市、期望薪资、可到岗时间、避雷公司等

```bash
# 求职约束示例 (constraints.txt)
目标城市：上海、北京
期望薪资：年薪40-60万
可到岗时间：2027年2月
避雷行业：外包、教育培训
是否接受996：否
```

### Step 1: 岗位匹配挖掘

生成TOP10最适合你的岗位推荐，并拆解每个岗位的能力要求：

```bash
cd /Users/niny/career-os/skills/career-precision-applier

python3 main.py --mode match \
  --resume-file ~/Desktop/我的简历.md \
  --constraints-file ~/Desktop/求职约束.txt \
  --output-dir ~/Desktop/精准投递
```

**输出**：`~/Desktop/精准投递/01_岗位匹配表.json`

### Step 2: STAR简历改写

基于岗位关键词，将你的简历改写为STAR格式（情境-任务-行动-结果），生成通用底稿和可复用素材库：

```bash
python3 main.py --mode rewrite \
  --resume-file ~/Desktop/我的简历.md \
  --keywords-file ~/Desktop/精准投递/01_岗位匹配表.json \
  --output-dir ~/Desktop/精准投递
```

**输出**：
- `~/Desktop/精准投递/02_STAR简历底稿.md`
- `~/Desktop/精准投递/03_STAR素材库/` （多个案例文件）

### Step 3: 批量生成定向物料

手动去BOSS直聘筛选岗位，把感兴趣的岗位JD复制到文本文件，然后批量生成：

```bash
# 创建JD文件夹
mkdir -p ~/Desktop/JDs

# 把每个岗位的JD保存为单独的txt文件
# 例如：字节跳动_AI产品经理.txt

# 批量生成定制简历和打招呼话术
for jd_file in ~/Desktop/JDs/*.txt; do
  python3 main.py --mode generate \
    --jd-file "$jd_file" \
    --resume-base ~/Desktop/精准投递/02_STAR简历底稿.md \
    --output-dir ~/Desktop/精准投递
done
```

**输出**：
- `~/Desktop/精准投递/04_岗位台账.jsonl` （所有岗位的汇总信息）
- `~/Desktop/精准投递/定制简历_*.md` （每个岗位的定制简历）

### Step 4: 手动投递

1. 查看岗位台账，找到匹配度高的岗位
2. 将定制简历导出为PDF（用Typora、Obsidian等工具）
3. 去BOSS直聘手动投递：
   - 附件上传PDF简历
   - 复制打招呼话术，稍作修改后发送

**重要**：必须手动投递，不要用脚本自动投递，否则会被封号！

### Step 5: 投递复盘

投递3天后，更新台账中的`is_read`和`got_interview`字段，然后生成复盘报告：

```bash
# 编辑台账文件，更新投递结果
# 例如：将 "is_read": false 改为 "is_read": true

python3 main.py --mode review \
  --ledger-file ~/Desktop/精准投递/04_岗位台账.jsonl \
  --output-dir ~/Desktop/精准投递
```

**输出**：`~/Desktop/精准投递/05_投递复盘报告.json`

## 完整流程（一键执行Step 1-2）

```bash
python3 main.py --mode full \
  --resume-file ~/Desktop/我的简历.md \
  --constraints-file ~/Desktop/求职约束.txt \
  --output-dir ~/Desktop/精准投递
```

执行完成后，你会得到：
- TOP10岗位推荐
- STAR简历底稿
- STAR素材库

然后继续执行Step 3开始批量生成物料。

## 环境变量配置

需要配置Claude API Key：

```bash
# 方法1：设置环境变量
export ANTHROPIC_API_KEY="sk-ant-..."

# 方法2：写入配置文件
echo '{"ANTHROPIC_API_KEY": "sk-ant-..."}' > ~/career-os/config/api_keys.json
```

## 输出目录结构

```
~/Desktop/精准投递/
├── 01_岗位匹配表.json              # Step 1输出
├── 02_STAR简历底稿.md              # Step 2输出
├── 03_STAR素材库/                  # Step 2输出
│   ├── 案例01_外卖新用户转化优化.json
│   ├── 案例02_AI工具集成项目.json
│   └── ...
├── 04_岗位台账.jsonl               # Step 3输出（追加写入）
├── 05_投递复盘报告.json            # Step 4输出
├── 定制简历_字节跳动_AI产品经理.md  # Step 3输出
├── 定制简历_腾讯_用户增长PM.md      # Step 3输出
└── ...
```

## 常见问题

### Q: 可以自动投递吗？
A: 不可以！BOSS直聘没有开放API，用脚本自动发消息会被封号。本工具只生成投递物料，投递动作必须手动完成。

### Q: 生成的简历包含虚假信息怎么办？
A: AI严格遵守真实性原则，只会重组你提供的真实经历。如果发现虚假内容，说明AI理解有误，请手动修正并反馈。

### Q: 一岗一版简历会不会被HR发现？
A: 定制简历只用于PDF附件，不要修改BOSS平台的在线简历。这样之前投递的HR看到的还是旧版，不会发现。

### Q: 打招呼话术太模板化怎么办？
A: 生成后必须手动微调，改几个词，调整语序，降低模板感。

### Q: 如何提高面试邀约率？
A: 执行Step 4投递复盘，分析哪类岗位效果好，哪个STAR案例更受欢迎，持续迭代优化简历素材库。

## 与Career OS其他Skill的协作

- **career-match-engine**：本Skill专注岗位推荐，match-engine专注匹配度计算
- **career-resume-studio**：本Skill生成一岗一版简历，resume-studio生成通用简历
- **career-apply-ops**：本Skill生成投递物料，apply-ops负责投递状态追踪

## 注意事项

⚠️ **真实性红线**：绝对禁止虚构项目、业绩数据，所有经历必须真实可核验

⚠️ **账号安全**：不使用爬虫/自动投递，避免平台封号

⚠️ **简历版本管理**：定制简历只用PDF附件，不修改平台在线简历

⚠️ **投递节奏**：控制投递密度，避免短时间批量海投触发风控

## 技术支持

如有问题，请查看：
- Skill文档：`/Users/niny/career-os/skills/career-precision-applier/SKILL.md`
- Career OS主文档：`/Users/niny/career-os/README.md`
