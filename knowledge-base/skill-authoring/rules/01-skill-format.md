# 01 · SKILL.md 格式规约

> 更新历史：2026-08-22 创建。
>
> 来源：[Agent Skills 规范](https://agentskills.io/specification)。本篇是格式层面的**硬约束**——违反会导致 skill 无法被跨 runtime 识别或校验失败。仓库专属约定（版本号、author、category、allowed-tools 写法）见 `.claude/rules/skill-conventions.md`，配套文档（CHANGELOG / README）格式见 `.claude/rules/doc-conventions.md`，本篇均不重复。

## 1. 目录结构

一个 skill 是一个目录，**必须**包含 `SKILL.md`。其余内容按约定组织：

```
skill-name/
├── SKILL.md          # 必须：frontmatter 元数据 + 指令
├── scripts/          # 可选：可执行代码
├── references/       # 可选：附加文档
├── assets/           # 可选：模板、资源
└── ...               # 任意其他文件或目录
```

- **必须**：skill 目录名与 `SKILL.md` frontmatter 的 `name` 字段一致
- **应该**：按 `scripts/`（可执行代码）、`references/`（文档）、`assets/`（模板/资源）分类组织附加内容，不混放
- **禁止**：在 `SKILL.md` 目录下散放无归类说明的文件（agent 无法判断其用途）

## 2. Frontmatter 字段

`SKILL.md` 必须包含 YAML frontmatter（`---` 包裹）后接 Markdown 正文。frontmatter 只允许六个顶层字段，出现其他顶层字段会导致跨 runtime 严格校验器报 `Unexpected fields in frontmatter`：

| 字段 | 必填 | 约束 |
|---|---|---|
| `name` | 必须 | ≤64 字符；仅小写字母、数字、连字符；不得以连字符开头/结尾；不得含连续连字符；须与目录名一致 |
| `description` | 必须 | ≤1024 字符；非空；描述 skill 做什么 + 何时用 |
| `license` | 可选 | 许可证名或指向捆绑许可证文件的引用，保持简短 |
| `compatibility` | 可选 | ≤500 字符；运行环境要求（目标产品、系统包、网络访问等） |
| `metadata` | 可选 | 任意键值映射（字符串→字符串），用于扩展属性 |
| `allowed-tools` | 可选 | 空格分隔的预授权工具列表（实验性） |

- **必须**：`name` 只含小写字母、数字、连字符，符合 `pdf-processing` 这类 kebab-case，不用 `PDF-Processing`
- **必须**：`description` 描述"做什么 + 何时用"，不用 `Helps with PDFs` 这类空泛描述（见 `02` 章）
- **应该**：`metadata` 的键名尽量唯一，避免与未来标准字段冲突
- **禁止**：为没有特定环境要求的 skill 声明 `compatibility`（多数 skill 不需要）

## 3. 正文内容

frontmatter 之后的 Markdown 正文是 skill 指令，无格式限制——写能帮助 agent 完成任务的一切。

推荐章节：
- 分步指令（step-by-step instructions）
- 输入输出示例（examples of inputs and outputs）
- 常见边界情况（common edge cases）

- **必须**：正文聚焦 agent 不知道的信息，不解释通用常识（见 `05` 章"上下文预算"）
- **应该**：正文按"任务该怎么一步步做"组织，而非平铺知识点
- **应该**：长正文拆分为可引用的文件，不在 `SKILL.md` 里堆全部细节

## 4. Progressive disclosure（渐进式披露）

Agent 按三阶段渐进加载 skill，控制上下文占用：

| 阶段 | 加载内容 | 触发时机 |
|---|---|---|
| Discovery | 仅 `name` + `description`（约 100 tokens） | 启动时，所有 skill |
| Activation | 完整 `SKILL.md` 正文（建议 < 5000 tokens） | 任务匹配 description 时 |
| Resources | `scripts/`、`references/`、`assets/` 中的文件 | 按需读取 |

- **必须**：`SKILL.md` 正文控制在 500 行以内
- **必须**：详细参考材料拆到独立文件（`references/` 等），由正文按需引导加载
- **禁止**：在 `SKILL.md` 正文堆砌只在少数场景才需要的完整参考

## 5. 文件引用

- **必须**：引用同 skill 内文件用**相对路径**，基准是 skill 目录根
- **必须**：文件引用尽量保持**一级深度**（`references/REFERENCE.md`），避免深层引用链
- **必须**：正文明确告知 agent **何时**加载哪个文件（如"若 API 返回非 200 状态码，读 `references/api-errors.md`"），而非泛泛的"详见 references/"
- **应该**：在正文列出可用脚本清单，便于 agent 知道存在哪些脚本（见 `04` 章）

## 6. 校验

- **必须**：交付前用 [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) 校验 frontmatter 与命名规范：

```bash
skills-ref validate ./my-skill
```

- **应该**：校验通过后，按 `.claude/rules/skill-conventions.md` 补齐 SKILL.md 侧要求（版本号、author、category），按 `.claude/rules/doc-conventions.md` 补齐 CHANGELOG.md 与 README.md

## 权威参考

- [Agent Skills 规范 — 完整版](https://agentskills.io/specification)
