# NIA 选题与内容制作接入

内容策略的唯一正文是 [nia-xhs-topic-gate](../skills/xiaohongshu/nia-xhs-topic-gate/SKILL.md)。触发语、输出模板与安装说明见 [Skill README](../skills/xiaohongshu/nia-xhs-topic-gate/README.md)。

## 工作流

```text
用户 Idea／现有材料
→ NIA Gate（已有结论时复用；局部任务简短校验）
→ 主支柱、用户题、内容契约
→ 真实 Build / Eval / Case 与证据
→ 按请求制作 HTML／封面／标题／正文／口播
→ 五项内容校验
→ 可复用资产与周坑位建议
```

每周最多 1 篇，每月围绕 1 个主 Case；此文档不创建自动排期或平台发布任务。已知材料足够时直接推进，缺失实测或截图时先交付可完成部分，并准确标明待补项。

## HTML 双向协同

`nia-xhs-html` 对应现有 `nia-xhs-interactive-html`。Gate 交出人群、问题、承诺、证据、边界、行动和请求范围；HTML Skill 处理视觉与浏览器验证后，按同一内容契约复查标题、封面、前三秒、正文和结果。

在现有 HTML Skill 中接入以下入口规则即可，不需要复制其设计系统：

> For Nia account content, load the installed `nia-xhs-topic-gate/SKILL.md` when available. Apply its account positioning, content contract, practical evidence, and cross-format checks. For material-led or partial requests, reuse the existing Gate or keep the content check concise; do not add a topic pool or force a scoring dialogue. Keep this HTML skill's visual, interaction, and browser QA rules. If the Gate skill is unavailable, state that and use the verified user brief; do not claim that it ran.

配套 `references/content-workflow.md` 的 Material-led 入口保留直接处理原材料，只补充简短的定位、承诺、实操与证据校验，不强加额外选题阶段。

## 使用状态

- 仓库文件：规则可版本化、可迁移。
- 本机 Content OS：分类目录中的 `.skill.md` 相对链接供原文本执行器发现。
- Codex：将 Skill 文件夹注册到本机可发现目录，相关新会话可按描述匹配。
- GitHub 上传、Codex 发现、内容生成、浏览器验收、社交平台发布分别核实；完成其中一步不能代替其他步骤。

旧文本执行器目前只把 Skill 正文与输入交给文本模型。它能做评估和文案建议；执行实验、读取另一个 Skill、采集真实截图、制作文件及浏览器检查，需要有对应工具的 Codex 会话继续完成。
