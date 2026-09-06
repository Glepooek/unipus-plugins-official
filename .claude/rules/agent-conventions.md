---
paths:
  - "plugins/*/agents/*.md"
  - "plugins/*/agents/**/*.md"
---

> 文档类规范（CHANGELOG.md、README.md）见 `.claude/rules/doc-conventions.md`；skill 规范见 `.claude/rules/skill-conventions.md`。本篇只承载 agent 自身的约定。

## 何时建 agent 而非 skill

| 判据 | skill | agent |
|---|---|---|
| 上下文 | 注入当前对话，共享历史 | 独立上下文，只收一个 prompt |
| 适合的任务 | 需与用户往复交互、依赖对话历史 | 单次可闭环的推理/审查任务，且**需要与主对话隔离** |
| 是否执行动作 | 常执行（Bash/Write） | 可只读——需要隔离的往往正是"只推理不动手"的判定类任务 |

## 目录结构（硬约束）

```
plugins/<plugin>/
├── agents/<name>.agent.md        ← 只放本体。平铺，禁止子目录，禁止任何辅助文件
└── agent-docs/<name>/
    ├── CHANGELOG.md              ← 版本号真源（最新 `## [x.y.z]`）
    └── README.md                 ← 头部抄录版本号，两处须一致
```

两条禁令各有独立理由：

- **禁止子目录**：插件 agent 的 `agents/` 目录被**递归扫描**，且子目录名会拼进调用标识符——`agents/review/security.md` 在插件 `my-plugin` 中注册为 `my-plugin:review:security`。放子目录会得到 `<plugin>:<name>:<name>` 这样冗余难记的调用名。
- **禁止辅助文件**：`agents/` 下任何 `.md` 都会被注册为可调用 agent。插件级的容错方向与 project/user 级**相反**——frontmatter 无 `name` 或解析失败时，project/user 级跳过该文件，**插件级用文件名当 agent 名加载**。因此 `agents/CHANGELOG.md` 会变成一个叫 `<plugin>:CHANGELOG` 的假 agent，且官方**未提供任何文件名黑名单或豁免机制**。

⚠️ 这条约束与 skill 不同的根源：`agents/` 是「目录内容 = 可调用实体列表」，而 `skills/<name>/` 是「目录内容 = 一个实体的组成部分」。**同一份「配套文档放哪」的约定不能无差别套用到两种产物上**——SKILL.md 旁放 README/CHANGELOG 完全安全。

## 目录与命名

- 位置：**插件根的 `agents/`**，不在 `skills/` 下，不在 `.claude-plugin/` 下
- 命名：`<agent-name>.agent.md`
- **必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**：

```json
{
  "name": "<plugin-name>",
  "version": "x.y.z",
  "agents": ["./agents/<name>.agent.md"]
}
```

为什么显式声明而非依赖自动发现（自动发现确实存在，Anthropic 官方 `code-simplifier` 插件即依赖它）：

1. 官方对 `agents` 字段的语义是 **replaces**（替换默认 `agents/` 扫描），不是 append——声明后默认扫描被完全取代，杜绝后续有人误把文档挪进 `agents/` 而产生假 agent
2. 微软 `dotnet-diag` 与 `dotnet-msbuild` 两个插件**都逐个文件列出** `agents`，是官方生态的既有实践
3. 路径须以 `./` 开头且不得逃出插件根。⚠️ 官方**未说明** `agents` 是否接受目录路径（对比 `commands` / `workflows` 明确写了 "or directories"），因此**只用文件路径数组形态**

⚠️ **`.agent.md` 双扩展名不是 Claude Code 官方约定**，而是 VS Code / Copilot 的自定义 agent 约定（微软 `dotnet/skills` 仓库自己的 `create-custom-agent` skill 描述原文为 "Creates **VS Code** custom agent files (.agent.md)"）。Claude Code 官方文档对 `.agent.md` 零提及，示例全为纯 `.md`。本仓库沿用它是**跟随微软实践**，因其仍以 `.md` 结尾故两侧都能加载——不要误以为官方文档里能查到依据，也不要因查不到依据就去改名。

## frontmatter

只用两个 harness 的**公共交集**字段，多余字段会造成两侧不对等：

```yaml
---
name: agent-name
description: 何时该调用它，须写清与相邻产物的划界
tools: ['read', 'search', 'Read', 'Glob', 'Grep', 'read_file', 'glob', 'grep_search']
license: MIT
---
```

- `tools` **列出跨 harness 别名**（同一能力在两侧工具名不同），据实填写该 agent 真正需要的能力。需要加载 skill 的 agent 必须含 `'skill'` / `'Skill'`
- **不写任何版本字段**（既不写顶层 `version:`，也不写 `metadata.version`）。插件 agent 的 11 个合法字段是 `name`、`description`、`model`、`effort`、`maxTurns`、`tools`、`disallowedTools`、`skills`、`memory`、`background`、`isolation`——**不含 `metadata`**。这与 skill 不同：skill 可用 agentskills.io 规范明确留出的 `metadata` 自由映射承载自定义属性，agent 没有这个口子。agent 的版本号载体是 `agent-docs/<name>/CHANGELOG.md`
- **不写 Claude 侧独有字段**（`model` / `effort` / `maxTurns` / `disallowedTools` / `skills` / `memory` / `background` / `isolation`），写了即产生两侧能力不对等
- **`hooks` / `mcpServers` / `permissionMode` 三字段插件 agent 不支持**（Claude 侧安全限制），不要尝试

⚠️ **不要加官方清单外的键去赌"应该会被忽略"**。官方只文档化了「整个 YAML 解析失败」的行为，**未说明**「能解析但多出未知键」会怎样。而解析失败是**静默降级**：文件名当 name、description 变成 `Agent from <plugin> plugin`、**全部字段被忽略**——肉眼看不出异常。因此每次新增或修改 agent 后**必须**跑：

```bash
claude plugin validate ./plugins/<plugin-name>
```

## 配套文档

| 文档 | 要求 | 位置 |
|---|---|---|
| `CHANGELOG.md` | **必须** | `plugins/*/agent-docs/<name>/`，**不放 `agents/`** |
| `README.md` | **必须** | 同上 |
| `known-issues.md` | **不要求** | — |

格式与章节规范见 `.claude/rules/doc-conventions.md`（README 的「所处层级」与「触发词」两章对 agent 有专门写法）。

## 版本管理

agent **独立版本化，首版 `1.0.0`**，与所属插件的版本号互不相干、不换算。

| 变更类型 | agent 版本升级 |
|---|---|
| 新增能力 / 新增章节 / 扩大适用范围 | **Minor** `x.X.x` |
| 修改已有行为 / 修复措辞 / 优化 description | **Patch** `x.x.X` |
| 删除或重命名 agent、破坏性改变调用契约 | **Major** `X.x.x` |

**版本号真源是 `agent-docs/<name>/CHANGELOG.md` 的最新 `## [x.y.z]`**；README 头部抄录，两处须一致。

**同时须升所属插件版本**——改动 `agents/` 或 `agent-docs/` 下任何文件，都要升该插件两份 `plugin.json` 的 `version`（见 `AGENTS.md` 版本管理规则的触发矩阵）。两个版本号各自独立判定幅度，**可以不同**：给 agent 新增一节 → agent 升 Minor，但插件只是「修改已有内容」→ 插件升 Patch。

⚠️ **agent 版本号不写进 `plugin.json`**——那里的 `version` 是整个插件的版本，不是某个 agent 的。

## darwin-skill 门禁豁免

`darwin-skill` 的 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应评分维度。**agent 的 Minor/Major 升级不跑 darwin-skill**，改为按其 spec 的验收清单人工核验。

⚠️ 这与上面「CHANGELOG/README 必须」**不矛盾**：配套文档要求与评分门禁是两件事——前者是可人工核验的结构要求，后者依赖针对 SKILL.md 的自动化 rubric。因此 `known-issues.md` 对 agent 仍不要求（它是 darwin-skill 循环的输入产物）。
