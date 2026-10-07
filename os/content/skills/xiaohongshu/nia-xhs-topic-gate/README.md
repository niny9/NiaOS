# NIA 小红书选题 Gate

正式入口：[SKILL.md](SKILL.md)。版本 1.0.0，规则依据用户在“账号分析与定位”中的决定及本次 Work 要求整理（2026-10-07）。规则源文件是 Skill，不依赖聊天记忆是否保留。

## 何时调用

- `用 NIA 选题 Gate 判断：我想讲某个新 Agent 功能。`
- `按 NIA Content OS 判断，这个选题适合我的小红书账号吗？`
- `按我的账号定位做 HTML，沿用 nia-xhs-html 风格。`
- `给这个选题出标题／封面／文案／口播，并用小红书 Skill 校正。`
- `$nia-xhs-topic-gate`，附 Idea、素材或草稿即可；已有截图、数据、月度 Case 与周坑位时一并提供。

默认支持相关请求的自动匹配，不限定为必须显式调用。安装后需在支持本地 Skill 的新会话中确认可发现；GitHub 上有文件不等于任意 ChatGPT 对话都能读取，不能用“已进入长期记忆”代替安装验证。

## 固定规则与输出

定位为 **Nia | AI Product Builder**。四大支柱长期占比为 Build/Case 40%、Product/Eval/Career 25%、Workflow/工具 20%、Business/NEXIS 15%。热点仅占 5 分，不能冲掉真实 Case、需求、证据与资产判断。

100 分权重为 **25 / 20 / 20 / 15 / 15 / 5**。只输出 **直接做／改造后做／不建议做** 三类：80+、60–79、低于 60，真实性和定位缺口可覆盖分数结论。70–79 与 60–69 分别说明轻度或结构性改造。支持只评估、局部内容校验和 HTML 交接。

标准交付：**结论与分数 → 六层 Gate → 用户题改写 → 内容契约 → Build/Eval 与证据表 → 3 个标题 → 内容骨架／所需产物 → 五项校验 → Career/NEXIS/IP 资产 → 周坑位与下一步**。完整可复制模板和 JSON 模式见 [SKILL.md 的标准输出模板](SKILL.md#标准输出模板)。

每周最多 1 篇，每月围绕 1 个主 Case，热点只能替换。内容选题通过与发布证据完备是两个状态；不得把计划写成实测或保证爆款。

## HTML 协同

用户原称 `nia-xhs-html`；本机正式 Skill 为 `nia-xhs-interactive-html`。本 Skill 负责内容基准和证据，HTML Skill 负责浅粉品牌、页面设计、交互和浏览器验收。两者共享人群、问题、承诺、证据、边界和行动。保留 HTML Skill 的视觉规则，不复制或覆盖整套设计 Skill。

在已选定材料的 HTML 请求中，先做简短内容校验，不强行启动选题池。没有 HTML Skill 时，仍可交付选题与内容 brief，并说明尚未完成视觉验收。

## Content OS 目录与调用

遵循本机当前 Content OS 的分类目录：

```text
os/content/skills/xiaohongshu/
├── nia-xhs-topic-gate.skill.md → nia-xhs-topic-gate/SKILL.md
└── nia-xhs-topic-gate/
    ├── SKILL.md
    ├── README.md
    └── agents/openai.yaml
```

`.skill.md` 是兼容旧 Content OS 文本执行器的相对符号链接，与 Codex 使用同一份规则，避免双份正文漂移。执行器的 `load_skill("nia-xhs-topic-gate")` 可发现此入口；该执行器只生成文本，不等于已经做过实验、制作 HTML 或完成发布。

Codex 发现入口可指向上述 Skill 文件夹，例如本机 `~/.codex/skills/nia-xhs-topic-gate` 的链接。安装前应检查同名入口，已有不同内容时保留并合并，不直接覆盖。当前机器 Content OS 根目录为 `/Users/niny/NiaOS/os/content`；旧 `/Users/niny/content-os` 已标为废弃，不作为新产物目标。

GitHub 内容仅包含本次 Skill 与接入文档。不要把本地 Content OS 的素材、账号配置、客户信息或其他未跟踪文件一起提交。
