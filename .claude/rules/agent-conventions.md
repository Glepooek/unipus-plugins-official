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
├── agents/<name>.md              ← 只放本体。平铺，禁止子目录，禁止任何辅助文件
└── agent-docs/<name>/
    ├── CHANGELOG.md              ← 版本号真源（最新 `## [x.y.z]`）
    └── README.md                 ← 头部抄录版本号，两处须一致
```

两条禁令各有独立理由：

- **禁止子目录**：插件 agent 的 `agents/` 目录被**递归扫描**，且子目录名会拼进调用标识符——`agents/review/security.md` 在插件 `my-plugin` 中注册为 `my-plugin:review:security`。放子目录会得到 `<plugin>:<name>:<name>` 这样冗余难记的调用名。
- **禁止辅助文件**：`agents/` 下任何 `.md` 都会被注册为可调用 agent。插件级的容错方向与 project/user 级**相反**——frontmatter 无 `name` 或解析失败时，project/user 级跳过该文件，插件级**静默降级加载**：CLI 报错原文即「At runtime this agent loads with its name taken from the filename and every other frontmatter field silently dropped」。因此 `agents/CHANGELOG.md` 会以 `<plugin>:CHANGELOG` 之名进入 agent 列表，而官方**未提供任何文件名黑名单或豁免机制**。所幸这种降级 `claude plugin validate` 能检出（声明 `agents` 与否都能检出），所以它是可拦的失误，不是无声的坑——但前提是每次改动都真的跑了校验。

⚠️ 这条约束与 skill 不同的根源：`agents/` 是「目录内容 = 可调用实体列表」，而 `skills/<name>/` 是「目录内容 = 一个实体的组成部分」。**同一份「配套文档放哪」的约定不能无差别套用到两种产物上**——SKILL.md 旁放 README/CHANGELOG 完全安全。

## 目录与命名

- 位置：**插件根的 `agents/`**，不在 `skills/` 下，不在 `.claude-plugin/` 下
- 命名：**纯 `<agent-name>.md`**（官方文档全部示例形态，如 `agents/reviewer.md`）
- **必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**：

```json
{
  "name": "<plugin-name>",
  "version": "x.y.z",
  "agents": ["./agents/<name>.md"]
}
```

为什么显式声明而非依赖自动发现（自动发现确实存在，Anthropic 官方 `code-simplifier` 插件即依赖它）：

1. 官方对 `agents` 字段的语义是 **replaces**（替换默认 `agents/` 扫描），不是 append——声明后默认扫描被完全取代，杜绝后续有人误把文档挪进 `agents/` 而被静默降级加载成 agent
2. 微软 `dotnet-diag` 与 `dotnet-msbuild` 两个插件**都逐个文件列出** `agents`，是官方生态的既有实践
3. 路径须以 `./` 开头且不得逃出插件根。⚠️ **`agents` 只接受文件路径，不接受目录**——实测目录形态 `["./agents/"]` 被 `claude plugin validate` 判 `agents.0: Invalid input`。官方文档中 `["./commands/", "./extras/"]` 那种「用目录保留默认扫描」的范式**不适用于 `agents`**（其字段描述也无 `commands` / `workflows` 那样的 "or directories" 限定）

⚠️ **不要用 `.agent.md` 双扩展名。** 它是 VS Code / Copilot 的自定义 agent 约定（微软 `dotnet/skills` 仓库自己的 `create-custom-agent` skill 描述原文为 "Creates **VS Code** custom agent files (.agent.md)"），Claude Code 官方文档对它零提及，示例全为纯 `.md`。

⚠️ **注册名取自 frontmatter 的 `name`，不是文件名**（实测：`-p` 无头模式询问可用 agent，声明了 `agents` 的探针插件返回的是 frontmatter 里的 `name`）。文件名只在无 `name` 或 frontmatter 解析失败时作 fallback。

⚠️ **`claude plugin details` 的 Agents 列不可作为加载判据**（两个实测缺陷）：① 声明 `agents` 字段时该列统计为 `0`，即便 agent 实际已正常加载（官方 `dotnet-diag` 同现象）；② 该列显示文件名而非注册名。核验 agent 是否真的可用要用无头模式实调：

```bash
claude --plugin-dir ./plugins/<plugin-name> -p "列出你可用的 agent，只输出 agent 名"
```

## frontmatter

只用两个 harness 的**公共交集**字段，多余字段会造成两侧不对等：

```yaml
---
name: agent-name
description: 何时该调用它，须写清与相邻产物的划界
tools: ['read', 'search', 'Read', 'Glob', 'Grep', 'read_file', 'glob', 'grep_search']
---
```

- `tools` **列出跨 harness 别名**（同一能力在两侧工具名不同），据实填写该 agent 真正需要的能力。需要加载 skill 的 agent 必须含 `'skill'` / `'Skill'`
- **不写任何版本字段**（既不写顶层 `version:`，也不写 `metadata.version`）。插件 agent 的 11 个合法字段是 `name`、`description`、`model`、`effort`、`maxTurns`、`tools`、`disallowedTools`、`skills`、`memory`、`background`、`isolation`——**不含 `metadata`**。这与 skill 不同：skill 可用 agentskills.io 规范明确留出的 `metadata` 自由映射承载自定义属性，agent 没有这个口子。agent 的版本号载体是 `agent-docs/<name>/CHANGELOG.md`
- **不写 Claude 侧独有字段**（`model` / `effort` / `maxTurns` / `disallowedTools` / `skills` / `memory` / `background` / `isolation`），写了即产生两侧能力不对等
- ⚠️ **不写 `license`**：它不在上述 11 字段清单内（只是 `plugin.json` 的顶层字段）。官方 `dotnet-diag` 的 agent 写了 `license: MIT` 属越界，只是 `validate` 不检查未知键而已——不跟随该处实践
- **`hooks` / `mcpServers` / `permissionMode` 三字段插件 agent 不支持**（Claude 侧安全限制），不要尝试

⚠️ **不要加官方清单外的键去赌"应该会被忽略"**。官方只文档化了「整个 YAML 解析失败」的行为，**未说明**「能解析但多出未知键」会怎样。而解析失败是**静默降级**：文件名当 name、description 变成 `Agent from <plugin> plugin`、**全部字段被忽略**——肉眼看不出异常。因此每次新增或修改 agent 后**必须**跑：

```bash
claude plugin validate ./plugins/<plugin-name>
```

⚠️ **但「validate 通过」不等于「frontmatter 写对了」**。它确实会检查 agent frontmatter 能否解析（解析失败时报错原文即上述降级描述，声明 `agents` 与否都能检出），但 YAML 容错很强——`tools: [unclosed` 这类会被解析成合法值，不算失败。字段名拼错、值类型不符一律查不出来，**只能人工核对上面的字段清单**。

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
