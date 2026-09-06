---
paths:
  - "**/CHANGELOG.md"
  - "plugins/*/skills/**/README.md"
  - "plugins/*/agent-docs/**/*.md"
---

## 编辑铁律：禁止无关格式化

编辑 SKILL.md / CHANGELOG.md / README.md 时，只改动语义相关的内容，不增删空行、不调整缩进、不做表格对齐等纯格式化改动。仓库已配置 `.prettierignore`（排除 `*.md`）和 `.vscode/settings.json`（禁用 markdown 自动格式化）作为防护，但仍需自查：提交前看 `git diff`，若出现大片纯空白/缩进变化而无实际内容变化，说明格式化工具介入了，应撤销重做。

## CHANGELOG.md 规范

每个 skill 目录**必须**有 `CHANGELOG.md`，提交前必须更新，格式：

```markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增的功能或章节

### Changed
- 修改的内容

### Removed
- 删除的内容

### Fixed
- 修复的问题
```

规则：
- 只写实际发生的类别，无变更的类别可省略
- 新建 skill 时同步创建 CHANGELOG.md，初始版本为 `[1.0.0]`
- **agent 的 CHANGELOG.md 放在 `plugins/*/agent-docs/<name>/` 下，不放 `agents/`**——`agents/` 目录下任何 `.md` 都会被注册为可调用 agent（详见 `agent-conventions.md`）

## README.md 规范

**适用范围**：`plugins/*/skills/` 下新增的 skill（含复合 skill 的子 skill）必须配 README.md；`plugins/*/agents/` 下新增的 agent 同样必须配 README.md 与 CHANGELOG.md，位置在 `plugins/*/agent-docs/<name>/`。`.claude/skills/` 仅供本仓库自用不对外发布，不强制要求。**已有 skill 与已有 agent 均不回填**（agent 当前数为 0，该句为将来预留）。

新增时在对应目录下创建 `README.md`，固定包含以下章节，顺序不可打乱。其中两章 skill 与 agent 写法不同，已在各节标出。

### 标题与元信息

skill：

```markdown
# <skill-name>

> 版本：x.y.z | 分类：<metadata.category 取值>

一句话说明这个 skill 解决什么问题、产出什么。
```

版本号和分类直接抄 SKILL.md 的 `metadata.version` / `metadata.category`，两处必须保持一致。

agent：

```markdown
# <agent-name>

> 版本：x.y.z | 产物类型：agent

一句话说明这个 agent 解决什么问题、产出什么。
```

版本号抄 `agent-docs/<name>/CHANGELOG.md` 的最新 `## [x.y.z]`，两处必须一致。**无分类**——插件 agent 的 frontmatter 没有 `metadata` 字段，因此没有 `category` 可抄。

### 所处层级

- **skill**：用 ASCII box-drawing 图，以 `metadata.category` 的 6 个取值（workflow/quality/generator/tool/platform/decision）为层级，标出本 skill 所处层，及直接上下游 skill（用 `★` 标记本 skill）。复合 skill 的子 skill 标注所属主流程及所在阶段。
- **agent**：⚠️ **改为按「与相邻产物的划界」画图**——标出本 agent 与哪些 skill、哪些官方产物相邻，各自负责什么。agent 无 `category` 字段，6 取值层级无从谈起。

确无上下游依赖时，两者都仍保留本章节，图中注明"无上下游，独立使用"——不允许跳过该章节。

### 触发词 / 调用方式

- **skill**：用户会说什么话触发，顿号分隔关键词。复合 skill 的子 skill（无法被用户直接调用）改写为"内部触发条件"，写明被哪个主流程、在哪个阶段调度。
- **agent**：⚠️ **改为「调用方式与触发面」**——Claude 侧 `@plugin-name:agent-name`，Codex 侧同名触发；并写明 description 里承担跨语言触发的技术标识符。agent 无复合形态，且调用机制与 skill 的 `/` 前缀不同。

### 业务逻辑流程图

Step 1..N 竖排 ASCII 流程框，概述核心执行步骤（不需要照抄正文全部细节，突出主干流程）。skill 与 agent 写法相同。

### 产出物数据流

输入 → 本产物 → 具体产出（文件/数据/报告）→ 下游消费者（人工接手 / 其他 skill 消费 / 无下游）。skill 与 agent 写法相同——agent 的产出是结论文本，下游通常是人工接手。

### 依赖关系图

双向箭头图：谁调度本产物、本产物调度或读取谁。无依赖时写明"无上下游，独立使用"，仍保留本章节标题。agent 须标出它加载的 skill（若 `tools` 含 skill 加载能力）。

**图表约定**：全部用纯 ASCII box-drawing 字符（`┌─┐│└┘├┤▼→↓★`）绘制，不使用 Mermaid、不嵌入图片——保证在任意终端/编辑器/纯文本 diff 里都能正确渲染和阅读。

不要求单独的"安装"章节——本仓库产物通过插件市场随所属插件整体安装，没有独立于插件的安装步骤；skill 的运行依赖已在 SKILL.md 的 `compatibility` 字段声明，无需在 README 重复。
