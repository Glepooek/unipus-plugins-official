# rules 拆分、版本真源下移与 agent 配套文档 设计规约

> 日期：2026-09-06
> 状态：设计中
> 产物形态：`.claude/rules/` 规则文件重组 + **版本真源下移至每插件 `plugin.json`** + `plugins/*/agent-docs/` 新目录约定
> 关联：`2026-09-05-dotnet-diagnose-agent-design.md`（本仓首个 agent，是本规范的首个适用对象）

## 1. 背景与动因

本 spec 解决三个相互关联的问题。

### 1.1 拆分的真实驱动力：加载精度而非文件长度

`.claude/rules/skill-conventions.md` 现为单文件 248 行，`paths` 声明四条 glob：

```yaml
paths:
  - "**/SKILL.md"
  - "**/CHANGELOG.md"
  - "plugins/*/skills/**/README.md"
  - "plugins/*/agents/**/*.agent.md"
```

248 行不算长，问题在 `**/CHANGELOG.md` 这条**极宽的 glob**——编辑任何一个 CHANGELOG（全仓 50+ 个）都会把 248 行全量注入上下文，其中约 190 行（Skill frontmatter 规范 64 行 + Agent 规范 57 行 + 执行前置校验 28 行 + 需求预告 12 行 + 持续优化 7 行）与「写 CHANGELOG」这个动作无关。

**按 `paths` 加载的规则文件，切分粒度应对齐「什么动作触发它」，而非「概念归属谁」。** 这是本次拆分的判据。

### 1.2 agent 缺配套文档

首个 agent 即将落地，但现有规范把 agent 的 CHANGELOG / README 列为「不适用」。用户要求 agent 也具备配套文档与独立版本号，需按官方文档核实可行性后落地——核实结果见 § 2。

### 1.3 版本真源与官方回退链错位（本次新增范围）

现状实测（§ 2.11 详述）：AGENTS.md 声明 `marketplace.json` 顶层 `version` 为唯一真源，但按官方版本解析回退链，**Claude 侧实际读到的是 git commit SHA**（回退链前两级本仓都空着），而 Codex 侧读 `.codex-plugin/plugin.json` 的语义化版本。**两个 harness 看到的版本标识形态完全不同。**

用户决策：**版本真源从「marketplace 顶层一个值」下移为「每插件 plugin.json 各自一个值」**，并配套一套「什么改动升哪一层」的触发矩阵（§ 7）。

## 2. 官方文档核实结论（本节全部为实测与文档引用，非推断）

### 2.1 插件 agent 的 frontmatter 合法字段

插件 agent 支持 11 个字段：`name`、`description`、`model`、`effort`、`maxTurns`、`tools`、`disallowedTools`、`skills`、`memory`、`background`、`isolation`。其中 `name` 与 `description` 必填。

安全原因禁用三个字段：`hooks`、`mcpServers`、`permissionMode`。

来源：`https://code.claude.com/docs/en/plugins-reference`、`https://code.claude.com/docs/en/sub-agents`

**无任何版本字段。** 官方文档全篇不存在 agent 级版本号概念，出现的「版本」均指 Claude Code 产品版本。

⚠️ **文档空白**：frontmatter 能正常解析、但多出官方清单外的键（如顶层 `version:` 或嵌套 `metadata.version`）时的行为，官方**未作说明**。已文档化的只有「整个 YAML 解析失败」的情形。因此**不得假设未知键会被静默忽略**。

### 2.2 `agents/` 目录递归扫描，且子目录名进调用标识符

> "Plugin `agents/` directories are also scanned recursively. Unlike project and user scopes, a subfolder inside a plugin's `agents/` directory becomes part of the scoped identifier: a file at `agents/review/security.md` in plugin `my-plugin` registers as `my-plugin:review:security`."

来源：`https://code.claude.com/docs/en/sub-agents`

**后果**：`agents/dotnet-diagnose/dotnet-diagnose.agent.md` 的调用名会变成 `optimus-devops-plugin:dotnet-diagnose:dotnet-diagnose`——冗余且难记。**因此 agent 本体必须平铺，不建子目录。**

### 2.3 关键约束：`agents/` 是排他性命名空间

插件 agent 的容错方向与 project/user 级**相反**：

| 情形 | project / user / managed 级 | **插件级** |
|---|---|---|
| frontmatter 无 `name` | 跳过该文件（当旁置文档） | **用文件名当 agent 名加载** |
| frontmatter 解析失败 | 跳过，写调试日志 | **用文件名加载，description 变成 `Agent from <plugin> plugin`，全部字段被忽略** |

来源：`https://code.claude.com/docs/en/plugins-reference`

**后果**：`agents/CHANGELOG.md` 会被注册成一个名为 `<plugin>:CHANGELOG` 的假 agent。官方**未提供任何文件名黑名单或豁免机制**。

**这条约束推出一个通用规则**：凡「目录内容 = 可调用实体列表」的机制（`agents/`、`commands/`），配套文档必须放在目录外；而 `skills/<name>/` 是「目录内容 = 一个实体的组成部分」，SKILL.md 旁放 README/CHANGELOG 完全安全。**同一份「配套文档」约定不能无差别套用到两种产物上。**

⚠️ **两份官方文档在此处措辞不一致，须按作用域区分**：`sub-agents` 页有一句「无 `name` 的文件被 treated as documentation kept beside your agents」，读起来像是允许旁置文档；但该句的作用域是 **project / user / managed 级**。`plugins-reference` 页对**插件级**的规定是明确的相反行为（无 `name` → 按文件名加载）。**本 spec 按插件级规定处理**——我们的 agent 全部在 `plugins/` 下。

### 2.4 `plugin.json` 的 `agents` 字段可替换默认扫描

`agents` 字段类型 `string|array`，官方描述为 "Custom agent files (**replaces** default `agents/`)"。示例全部是**单个文件路径**。

⚠️ 官方**未说明**该字段是否接受目录路径——对比之下 `workflows` 明确写 "script files **or directories**"、`commands` 明确写 "or directories"，而 `agents` 只写 "Custom agent files"。**因此本 spec 只用文件路径数组形态。**

来源：`https://code.claude.com/docs/en/plugins-reference`

### 2.5 三个官方插件的实证（本机缓存，可复现）

| 观察点 | Anthropic `code-simplifier` | 微软 `dotnet-diag` | 微软 `dotnet-msbuild` |
|---|---|---|---|
| agent 结构 | 平铺 `agents/code-simplifier.md` | 平铺 `*.agent.md` | 平铺 `*.agent.md` × 3 |
| `agents/` 内辅助文件 | 无 | 无 | 无 |
| `plugin.json` 的 `agents` | **不声明**（走自动发现） | 逐个文件列出 | 逐个文件列出 |
| agent 版本号 | 无 | 无 | 无 |
| skill 目录内 CHANGELOG/README | — | **无**（只有 `SKILL.md` + `references/`） | 无 |
| SKILL.md 的 `metadata.version` | — | **无** | 无 |
| 清单层级 | 每插件 `.claude-plugin/plugin.json` | 同 + `.codex-plugin/plugin.json` | 同 |

**两点结论**：

1. **官方连 skill 也不独立版本化。** 本仓库 skill 的 `metadata.version` + CHANGELOG + README 六章节全属**本仓自创约定**——其中 `metadata.version` 有官方留的合法载体（见 § 2.9），CHANGELOG / README 则是纯自创。这不是缺陷（自创约定服务于本仓维护需要），但记录清楚可避免后续误以为在遵循官方规范。
2. 微软是「仓库级 marketplace + 每插件 `plugin.json`」**双层共存**，与本 spec 要引入的结构一致，有先例可依。

### 2.6 ⚠️ `plugin.json` 的 version 会静默覆盖 marketplace（直接影响本设计）

官方明确警告：

> "Avoid setting `version` in both `plugin.json` and the marketplace entry. Claude Code **always uses the `plugin.json` value without warning**, so a stale marketplace version can mask a version you set in `marketplace.json`."

完整版本解析回退链（`plugins-reference`）：

1. 插件 `plugin.json` 的 `version`
2. `marketplace.json` 中该插件条目的 `version`
3. git commit SHA（github / url / git-subdir / 相对路径源）
4. SHA-256 digest（archive 源）
5. `unknown`（npm 源或非 git 目录）

**这条警告曾被当成地雷，现在成了本设计的依据**：AGENTS.md 原声明 `.claude-plugin/marketplace.json` 为版本号唯一真源，因此最初的设计（§ 3.2 初版）规定新建的 `plugin.json` **不得**写 `version`，以免静默覆盖。§ 7 推翻了这个前提——真源下移到 `plugin.json` 后，「静默胜过 marketplace」正是期望行为。

**处置（见 § 7.1）**：每插件 `.claude-plugin/plugin.json` **写 `version`**，marketplace 插件条目**永不填写** `version`。两者不同时写，官方警告的「陈旧 manifest 掩盖 marketplace 版本」情形因此不可能发生。

⚠️ 顺带发现的既有隐患（§ 7.6 已给出处置）：本仓库要求每插件 `.codex-plugin/plugin.json` 的 `version` 从 marketplace 抄录。按上述回退链，Codex 侧读 `.codex-plugin/plugin.json`、Claude 侧原本落到 commit SHA——**两个 harness 看到的版本形态本就不同**。§ 7.6 把「抄录」改为「两份同步升级」顺带修掉这一点，但需配一道同值的自动校验（§ 7.6.1）。

### 2.7 `skills` 字段是追加，`agents` 字段是替换

`plugin.json` 的两个字段语义不同：`skills` 对默认扫描做**追加**，`agents` 对默认 `agents/` 做**替换**。路径须以 `./` 开头且不得逃出插件根。

这正是 § 3.3 双保险机制成立的原因——声明 `agents` 后默认目录扫描被完全取代。

### 2.8 官方对 CHANGELOG / README 的唯一表态：仅插件根，SHOULD 语气

| 文档 | 原文 | 作用域 | 级别 |
|---|---|---|---|
| `plugins-reference` | "Document changes in a `CHANGELOG.md`" | **插件根**（目录树中 `└── CHANGELOG.md  # Version history`） | SHOULD |
| `plugins` | "Include a `README.md` with installation and usage instructions" | **插件根**，属「分享插件」清单项 | SHOULD |

**skill 目录内与 agent 目录内的 CHANGELOG / README：两份文档零提及。** agentskills.io 规范只强制 `SKILL.md`，可选目录仅推荐 `scripts/` / `references/` / `assets/`，CHANGELOG 与 README 全文 0 命中。

### 2.9 agentskills.io 的 `metadata` 是官方留的自由映射口子

规范对 `metadata` 的定义："Clients can use this to store additional properties **not defined by** the Agent Skills spec"，且规范示例恰好演示了：

```yaml
metadata:
  author: example-org
  version: "1.0"
```

**这修正了 § 2.5 的一处表述**：本仓库 skill 的 `metadata.version` 不是「违反官方规范的自创约定」，而是**用官方明确留出的自由映射承载自定义属性**——规范未定义其语义，但明确允许存放。代价是没有任何 harness 会读取它，纯供人工与本仓脚本消费。

⚠️ 但 agent frontmatter **没有** `metadata` 这个口子——插件 agent 的 11 个合法字段里不含 `metadata`（§ 2.1）。这是 skill 与 agent 在版本号载体上的实质差异，也是 § 3.3 选择 CHANGELOG 而非 frontmatter 的第二个理由。

### 2.10 微软 dotnet/skills 全量实测（16 插件 / 254 skill）

| 观察项 | 实测 |
|---|---|
| `plugins/*/skills/*/` 与 `plugins/*/agents/` 下的 README / CHANGELOG | **0 个** |
| 全仓库 CHANGELOG 命中数 | **0** |
| `agents/` 目录内文件 | 全部为 `<name>.agent.md`，**无任何其他文件** |
| 插件根 | `skills/` 16、`plugin.json` 16、`.claude-plugin/` 16、`.codex-plugin/` 16、`agents/` 16、`version.json` **16**、`README.md` 仅 5 |
| per-skill / per-agent 版本号 | **无** |

其 `CONTRIBUTING.md` 的 skill 与 agent checklist 都只要求文档写在**文件自身内部**（skill 六节、agent 五节），不要求任何配套文件。

**版本机制（可借鉴但不在本次范围）**：用 Nerdbank.GitVersioning 做插件级自动版本化——`version.json` 声明 major/minor base，patch 由内容 diff 自动推导并 stamp 进三份 manifest；`pathFilters` 排除 manifest 自身，避免「只改元数据也升版」。规则原文：「**Don't hand-edit the `version` field** in any of the manifests… The only version field you may change is the base in `version.json`」。

⚠️ **`.agent.md` 双扩展名的来源已查明**：它不是 Claude Code 约定，而是 **VS Code / Copilot 的自定义 agent 约定**（dotnet/skills 自己的 `create-custom-agent` skill 描述原文为 "Creates **VS Code** custom agent files (.agent.md)"）。Claude Code 官方文档两页对 `.agent.md` 零提及，示例全为纯 `.md`。因其仍以 `.md` 结尾，在 Claude Code 中同样能加载。**本仓库沿用 `.agent.md` 是跟随微软实践，不是跟随 Claude Code 官方**——这点须在 agent 规范里写明，避免后续误认为官方要求。

### 2.11 本仓版本号现状实测（本次范围变更的依据）

| 层级 | 是否有版本号 | 实测值 | 谁消费它 |
|---|---|---|---|
| `marketplace.json` **顶层** | ✅ | `14.0.0`，单个仓库级值 | ⚠️ **官方文档只有一行描述「Marketplace manifest version」，未说明触发任何行为**（见 § 2.11.3） |
| `marketplace.json` **插件条目内** | ❌ **10 个条目全部没有** | — | 官方回退链**第 2 级**，目前空着 |
| `.claude-plugin/plugin.json`（每插件） | ❌ **本仓不存在该文件** | — | 官方回退链**第 1 级**，目前空着 |
| `.codex-plugin/plugin.json`（每插件） | ✅ 9 个都有 | **12.1.8 / 12.1.9 / 12.3.1 / 13.1.2 / 14.0.0 各不相同** | Codex 读 |
| `SKILL.md` 的 `metadata.version` | ⚠️ **38 / 47 有，9 个缺** | 1.0.0 ~ 1.5.5 | **无任何 harness 读取** |

⚠️ **「10 个条目 vs 9 个 plugin.json」的差额已查明**：第 10 个条目 `cangjie-skill` 是外部 git url 引用，不在 `plugins/` 目录下，本来就不该有本仓的清单文件（详见 § 7.7.1）。**本仓自有插件是 9 个**，下文凡说「全部插件」均指这 9 个。

**缺 `metadata.version` 的 9 个 skill**（实测）：`optimus-backend-api-connect`、`weekly-report`、以及 qa 插件全部 6 个（`feishu-project-sync` / `feishu-project-xmind` / `jmeter-scripts` / `test-design` / `test-report` / `ui-consistency-check` / `ui-scripts`）。规则实际执行率 81%。

#### 2.11.1 现状机制已查明：「全仓统一编号 + 各插件停在自己最后一次改动的号」

各插件版本号看似混乱，实则严格合规。逐个验证其 `.codex-plugin/plugin.json` 最后一次改动的那个 commit，取同 commit 的 marketplace 顶层值：

| 插件 | plugin.json | 同 commit 的 marketplace 顶层 | 最后改于 |
|---|---|---|---|
| `optimus-mcp-servers` | 12.1.8 | **12.1.8** ✅ | 2026-08-28 |
| `optimus-office-plugin` | 12.1.8 | **12.1.8** ✅ | 2026-08-28 |
| `optimus-backend-plugin` | 12.1.9 | **12.1.9** ✅ | 2026-08-29 |
| `optimus-media-plugin` | 13.1.2 | **13.1.2** ✅ | 2026-09-01 |

**四个全部精确吻合。** 所以「从 marketplace 抄录同值」这条规则被严格执行了——只是它产生的效果不是「全仓同步一个值」，而是**每个插件带着自己最后一次改动时的全仓编号快照**。号各不相同不是失误，是这套机制的必然结果。

#### 2.11.2 但这套机制有两个真实问题

**问题一：版本号语义为空。** `optimus-office-plugin` 的 `12.1.8` 里，`12` 与 `1` 与 `8` 都来自其他插件的改动累积——它无法回答「这个插件自己迭代了几次」。语义化版本的 MAJOR/MINOR/PATCH 三段在这里全部失去意义。

**问题二：Claude 侧读不到任何语义化版本。** 按官方回退链（§ 2.6），第 1、2 级本仓都空着，Claude 侧实际落到**第 3 级 git commit SHA**；Codex 侧读 `.codex-plugin/plugin.json` 的语义版本。**两个 harness 的版本标识形态不同**——这比 § 2.6 登记的「抄漏会漂移」更彻底：不是可能漂移，是本来就不一致。

顺带一个后果：AGENTS.md 声明 marketplace 顶层为「两个 harness 共用的版本号真源」，而 Claude 侧压根不读它（顶层 `version` 不在回退链里，见 § 2.6）。**这句声明目前不成立。**

#### 2.11.3 顶层 `version` 的官方语义已核实：存在但无行为

来源 `https://code.claude.com/docs/en/plugin-marketplaces` 的 "Marketplace schema" 章节，Optional fields 表里只有一行：

> | `version` | string | Marketplace manifest version |

外加一句向后兼容说明：「`description` and `version` are also accepted under `metadata` for backward compatibility」。

**官方未说明它触发任何行为**——没有缓存失效、没有更新提示、没有任何比对逻辑。同页所有「更新检测」的讨论都只针对**插件版本**：

> "Plugin versions determine cache paths and update detection: if the resolved version matches what a user already has, `/plugin update` and auto-update skip the plugin."

而 marketplace 目录自身的更新机制是 git pull，不是版本号比对：

> "Users refresh their local copy with `/plugin marketplace update`."

⚠️ 顺带核实两点，以免后续误判：

- **没有 `schemaVersion` 字段**。唯一与 schema 相关的顶层键是 `$schema`，且官方注明「Claude Code **ignores this field at load time**」
- **官方对「marketplace 仓库自身如何版本化」的建议全在 git 层，不涉及这个字段**：用户侧用 `@ref` 固定分支/tag（`claude plugin marketplace add acme-corp/claude-plugins@v2.0`，注意 marketplace 源支持 `ref` 但**不支持 `sha`**，与插件源不同）；维护者做 stable/latest 双通道的推荐做法是「两个 marketplace 指向同仓库不同 ref」；插件改名/下线用 `renames` 追加式记录

**因此 § 7.1 把顶层 `version` 的语义收窄为纯描述性、且 § 7.4 进一步收窄到「仅增删插件时升」，都是与官方一致的**——它本来就不承担任何机制职责。保留它的唯一理由是本仓自己需要一个记录「集合里有哪些插件」的号，不是因为 harness 要读。

**另一条与本设计直接相关的官方校验行为**：

> "For each entry whose `source` is a local path, it also validates that plugin's own `plugin.json` and warns when the entry's `version` doesn't match the one in `plugin.json`."

本仓插件条目的 `source` 均为本地相对路径，因此**该校验对我们生效**。这进一步支持 § 7.1 的「marketplace 插件条目永不填写 `version`」——填了就必须与 `plugin.json` 逐一同步，否则触发警告；不填则无从冲突。

## 3. 决策与目录结构

### 3.1 已确认的三项决策

| # | 决策 | 依据 |
|---|---|---|
| 1 | **方案 A**：`agents/` 只放本体（平铺）+ 同级 `agent-docs/<name>/` 放配套文档 + 新建每插件 `.claude-plugin/plugin.json` 显式声明 `agents` | § 2.2 子目录污染标识符、§ 2.3 排他命名空间、§ 2.4 显式声明可替换扫描 |
| 2 | agent 版本号**独立起算，首版 1.0.0**，与插件版本号互不相干 | 与 skill 一致（各自 1.0.0 起算） |
| 3 | **版本真源从「marketplace 顶层一个值」下移为「每插件 `plugin.json` 各自一个值」**，并配触发矩阵 | § 2.11.2 顶层声明不成立、§ 2.11.3 官方未赋予顶层任何行为、§ 7 全节 |

**待拍板的一项**：各插件的起始版本号取 A（全部重置 1.0.0）还是 B（沿用当前值），见 § 7.3。

### 3.2 目标目录结构

```
plugins/optimus-devops-plugin/
├── .claude-plugin/
│   └── plugin.json              ← 新建（本仓首例）。写 name + version + agents（§ 7.1）
├── .codex-plugin/
│   └── plugin.json              ← 已存在，同步声明 agents；version 与 `.claude-plugin` 同步升级、同值（§ 7.6）
├── agents/
│   └── dotnet-diagnose.agent.md ← 只放本体，平铺，无任何辅助文件
├── agent-docs/
│   └── dotnet-diagnose/
│       ├── CHANGELOG.md         ← agent 自身版本号真源（`## [1.0.0]`），与插件版本无关
│       └── README.md            ← 头部抄录 agent 版本号，两处须一致
└── skills/
    └── <name>/                  ← 现状不变：SKILL.md + CHANGELOG + README 同目录
```

新建的 `.claude-plugin/plugin.json` 完整内容：

```json
{
  "name": "optimus-devops-plugin",
  "version": "1.0.0",
  "agents": ["./agents/dotnet-diagnose.agent.md"]
}
```

**三个字段各自的职责**（详见 § 7）：`name` 标识插件、`version` 承担 Claude 侧版本真源、`agents` 替换默认目录扫描。

**为什么不写 `description` 等字段**：这些已在 marketplace 条目声明，重复维护会产生第二真源。

### 3.3 为什么版本号载体是 CHANGELOG 而非 frontmatter

两条理由：

1. **agent frontmatter 没有承载自定义属性的合法字段**。插件 agent 的 11 个合法字段里不含 `metadata`（§ 2.1）——这与 skill 不同，skill 可用 agentskills.io 规范明确留出的 `metadata` 自由映射（§ 2.9）。
2. **加未知键是在赌文档空白**。官方只规定了「整个 YAML 解析失败 → 全部字段被忽略、agent 仍以文件名加载」，未说明「能解析但多个未知键」的行为；而 Claude 侧解析失败为**静默降级**，肉眼看不出 agent 已失效。

CHANGELOG 的 `## [x.y.z]` 是版本号的规范载体，官方对插件根 CHANGELOG 亦有 SHOULD 级表态（§ 2.8），语义等价且零风险。

**双保险机制**：即便 `agent-docs/` 已在 `agents/` 之外、天然不被扫描，仍在 `plugin.json` 显式声明 `agents` 文件路径——官方明确该字段 **replaces**（而非 append，见 § 2.7）默认扫描，杜绝后续有人误把文档挪进 `agents/`。

### 3.4 `.agent.md` 命名的来源须写明

`.agent.md` 双扩展名**不是 Claude Code 官方约定**，而是 VS Code / Copilot 的自定义 agent 约定（§ 2.10）。Claude Code 官方示例全为纯 `.md`。

本仓库沿用 `.agent.md`，理由是**跟随微软 dotnet/skills 的实践**（该仓库 16 个插件的 agents 目录全部采用），且因其仍以 `.md` 结尾，在 Claude Code 中同样能加载。

**agent 规范中须写明这一来源**，避免后续维护者误认为是 Claude Code 官方要求而不敢改，或反过来误以为官方文档里能查到依据。

## 4. 拆分后的文件布局

### 4.1 三个文件与各自的 `paths`

`skill-conventions.md` **保留原名**（用户确认）——全仓 28 处引用该路径，其中 5 处为活引用（`AGENTS.md` 3 处、`knowledge-base/README.md` 1 处、`skill-authoring/README.md` 2 处 + `rules/01-skill-format.md` 2 处、`catalog.json` 1 处）。改名需同步全部活引用且收益为零，因此**只搬走共用部分**。

| 文件 | `paths` | 触发时机 |
|---|---|---|
| `doc-conventions.md`（新建） | `**/CHANGELOG.md`<br>`plugins/*/skills/**/README.md`<br>`plugins/*/agent-docs/**/*.md` | 编辑任何 CHANGELOG、skill README、agent 配套文档 |
| `skill-conventions.md`（保留原名，瘦身） | `**/SKILL.md` | 编辑 SKILL.md |
| `agent-conventions.md`（新建） | `plugins/*/agents/*.md` + `plugins/*/agents/**/*.md` | 编辑 agent 本体 |

**三条 glob 的设计要点**：

- `doc-conventions.md` 的 `plugins/*/agent-docs/**/*.md` 覆盖 agent 的 CHANGELOG 与 README。注意 `**/CHANGELOG.md` 已能覆盖前者，这条 glob 的实际增量是 **agent 的 README**（`plugins/*/skills/**/README.md` 那条覆盖不到 `agent-docs/`）
- `agent-conventions.md` 用 `*.md` 而非 `*.agent.md`——若后续有人按 Claude Code 官方示例建纯 `.md` 的 agent，规范仍能自动加载。原 glob `plugins/*/agents/**/*.agent.md` 会漏掉这种情形
- **两条 glob 并存**（`plugins/*/agents/*.md` + `plugins/*/agents/**/*.md`），而非只写后者：`agents/` 被硬约束为**平铺**，平铺文件的目录层数为零，而严格 glob 语义下 `**` 要求**至少一层**目录——只写 `**/*.md` 会对唯一合法形态（平铺）完全不匹配，规则文件永不加载。第一条命中平铺，第二条兜底误放子目录的情形，两种匹配语义下都成立
- **`skill-conventions.md` 的 `paths` 从四条收窄到一条**。这是本次拆分的核心收益：编辑 CHANGELOG 不再注入 190 行无关内容

### 4.2 内容归属

| 现有章节 | 行数 | 去向 | 理由 |
|---|---|---|---|
| 编辑铁律：禁止无关格式化 | 4 | **`doc-conventions.md`** | 它约束的是「编辑 Markdown」这个动作本身，对三类文档同等适用。放在共用层，编辑任一类文档都能加载到 |
| Skill frontmatter 规范（含 metadata.version / author / category、compatibility、allowed-tools） | 64 | 留 `skill-conventions.md` | skill 专属 |
| Agent 规范 | 57 | **`agent-conventions.md`**（并按 § 5 重写） | agent 专属 |
| 执行前置校验（四类检查、硬约束 vs 可协商风险） | 28 | 留 `skill-conventions.md` | 约束的是 skill 的执行流程；agent 不执行动作（只读推理），不适用 |
| 需求预告 | 12 | 留 `skill-conventions.md` | 同上——agent 独立上下文只收一个 prompt，无「逐步追问」问题 |
| CHANGELOG.md 规范 | 26 | **`doc-conventions.md`** | 共用 |
| README.md 规范 | 43 | **`doc-conventions.md`**（并按 § 6 补 agent 分栏） | 共用骨架 + 两栏差异 |
| Skill 持续优化的强制约定（known-issues + darwin-skill） | 7 | 留 `skill-conventions.md` | darwin-skill 的 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应维度 |

**预估体量**：`doc-conventions.md` ≈ 90 行（含 agent 分栏新增内容）、`skill-conventions.md` ≈ 115 行、`agent-conventions.md` ≈ 75 行。

### 4.3 交叉引用方向

单向引用，不互引：

```
doc-conventions.md          ← 被引用，自身不引用其他两份
      ↑            ↑
skill-conventions   agent-conventions
```

两份专属规范各在开头一句指向 `doc-conventions.md`，措辞对齐现有风格（现文件已有「通用规范见 `knowledge-base/skill-authoring/`」的先例）。

⚠️ **不在 `doc-conventions.md` 里反向声明「skill 见 X、agent 见 Y」**——共用层被两侧引用，反向声明会造成三份文件互相指向，任一改名都要改三处。

## 5. `agent-conventions.md` 的内容规格

现有「Agent 规范」节直接搬过去不够——有四处必须按本次核实结论改写。

### 5.1 沿用的部分（原样搬迁）

- 何时建 agent 而非 skill 的三行判据表（上下文 / 适合的任务 / 是否执行动作）
- 「不确定时选 skill」及其理由
- frontmatter 不写 Claude 侧独有字段（`model` / `effort` / `maxTurns` / `disallowedTools` / `skills` / `memory` / `background` / `isolation`）——保持双 harness 均等
- `hooks` / `mcpServers` / `permissionMode` 三字段插件 agent 不支持
- `claude plugin validate ./plugins/<plugin-name>` 强制校验及其理由（静默降级肉眼看不出）

### 5.2 必须改写的四处

| # | 原表述 | 改为 | 依据 |
|---|---|---|---|
| 1 | 「无需在 `.claude-plugin/marketplace.json` 或 `.codex-plugin/plugin.json` 声明——两个 harness 均自动发现默认目录」 | **必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**；自动发现虽存在，但显式声明是官方 replaces 语义，用于杜绝误加载 | § 2.3 排他命名空间、§ 2.4、§ 2.7 |
| 2 | 「`CHANGELOG.md` **不要求**」「`README.md`（六章节）**不要求**」 | **两者均要求**，但**必须放在 `plugins/*/agent-docs/<name>/` 而非 `agents/` 下** | § 2.3、§ 3.1 决策 1 |
| 3 | 「**不写 `metadata.version`**：agent 版本随 marketplace 统一管理，不独立版本化——这是与 skill 的实质差异」 | **agent 独立版本化，首版 1.0.0**；版本号真源是 `agent-docs/<name>/CHANGELOG.md` 的最新 `## [x.y.z]`，README 头部抄录须一致。**frontmatter 仍不写任何版本字段**（插件 agent 无 `metadata` 合法字段） | § 2.1、§ 2.9、§ 3.1 决策 2、§ 3.3 |
| 4 | 目录与命名节只说「`<agent-name>.agent.md`，与微软官方 `dotnet-agent-skills` 生态一致」 | 补明**该命名来自 VS Code / Copilot 约定，非 Claude Code 官方**；Claude Code 官方示例为纯 `.md`，因 `.agent.md` 仍以 `.md` 结尾故可加载 | § 2.10、§ 3.4 |

### 5.3 新增的三节

**① 目录结构（硬约束）**

```
plugins/<plugin>/
├── agents/<name>.agent.md        ← 只放本体。平铺，禁止子目录，禁止任何辅助文件
└── agent-docs/<name>/
    ├── CHANGELOG.md
    └── README.md
```

两条禁令各有独立理由，须分别写明：

- **禁止子目录**：插件 agent 的子目录名会拼进调用标识符（`plugin:sub:name`），造成冗余难记的调用名（§ 2.2）
- **禁止辅助文件**：`agents/` 下任何 `.md` 都会被注册为可调用 agent，无 `name` 时按文件名加载——`agents/CHANGELOG.md` 会变成一个叫 `<plugin>:CHANGELOG` 的假 agent，且官方无豁免机制（§ 2.3）

**② 版本管理**

| 变更类型 | 升级 |
|---|---|
| 新增能力 / 新增章节 / 扩大适用范围 | **Minor** `x.X.x` |
| 修改已有行为 / 修复措辞 / 优化 description | **Patch** `x.x.X` |
| 删除或重命名 agent、破坏性改变调用契约 | **Major** `X.x.x` |

与 skill 同表。**同时须升所属插件版本**（`plugin.json` ×2，见 § 7.4 触发矩阵），两个版本号各自独立、互不换算，且**幅度可以不同**（§ 7.5）。

⚠️ **agent 的版本号写在 `agent-docs/<name>/CHANGELOG.md`，不写进 `plugin.json`**——`plugin.json` 的 `version` 是整个插件的版本，不是某个 agent 的（§ 7.1）。

**③ darwin-skill 门禁仍然豁免**

darwin-skill 的 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应评分维度。**agent 的 Minor/Major 升级不跑 darwin-skill**，改为按其 spec 的验收清单人工核验。

⚠️ 注意这与 § 5.2 第 2 处的改动**不矛盾**：配套文档（CHANGELOG/README）要求与评分门禁是两件事——前者是可人工核验的结构要求，后者依赖针对 SKILL.md 的自动化 rubric。因此 `known-issues.md` 对 agent **仍不要求**（它是 darwin-skill 循环的输入产物）。

## 6. `doc-conventions.md` 的 README 两栏差异

现有 README 六章节是为 skill 量身定的，其中两章对 agent 不成立：

| 章节 | skill 写法（现状，不变） | agent 写法 | 为何必须分叉 |
|---|---|---|---|
| 标题与元信息 | 版本 + 分类抄自 `metadata.version` / `metadata.category` | 版本抄自 `agent-docs/<name>/CHANGELOG.md`；**无分类**，改标「产物类型：agent」 | agent frontmatter 无 `metadata`，故无 `category`（§ 2.1） |
| **所处层级** | 按 `metadata.category` 的 6 个取值画层级图 | ⚠️ **改为按「与相邻产物的划界」画图**：标出本 agent 与哪些 skill / 官方产物相邻，各自负责什么 | agent 无 `category` 字段，6 取值层级无从谈起 |
| **触发词 / 内部触发条件** | 用户会说什么话触发；复合子 skill 改写为内部触发条件 | ⚠️ **改为「调用方式与触发面」**：Claude 侧 `@plugin-name:agent-name`、Codex 侧同名触发，并写明 description 里的跨语言触发词 | agent 无复合形态；且 agent 是 @-mention 调用，与 skill 的 `/` 调用机制不同 |
| 业务逻辑流程图 | Step 1..N 竖排 ASCII | 同 | 无差异 |
| 产出物数据流 | 输入 → skill → 产出 → 下游 | 同（agent 的产出是结论文本，下游是人工接手） | 无差异 |
| 依赖关系图 | 谁调度本 skill、本 skill 调度谁 | 同（须标出 agent 加载的 skill——若 `tools` 含 skill 能力） | 无差异 |

**图表约定不变**：全部纯 ASCII box-drawing，不用 Mermaid、不嵌图片。

### 6.1 CHANGELOG 规范的共用与差异

格式（`## [版本号] - YYYY-MM-DD` + Added/Changed/Removed/Fixed 四类、只写实际发生的类别、倒序最新在上、新建时初始 `[1.0.0]`）**完全共用，无差异**。

需要改的只有现有那句豁免声明：

| 原文 | 改为 |
|---|---|
| 「**`plugins/*/agents/` 下的 agent 不要求 CHANGELOG.md**（不独立版本化，见「Agent 规范」节）」 | 「**agent 的 CHANGELOG.md 放在 `plugins/*/agent-docs/<name>/` 下，不放 `agents/`**——`agents/` 目录下任何 `.md` 都会被注册为可调用 agent（详见 `agent-conventions.md`）」 |

### 6.2 适用范围声明的调整

现有 README 规范写「仅 `plugins/*/skills/` 下新增的 skill 必须配 README.md；`.claude/skills/` 不强制；已有 skill 不回填」。

补一句：「`plugins/*/agents/` 下新增的 agent 同样必须配 README.md 与 CHANGELOG.md，位置在 `plugins/*/agent-docs/<name>/`。」

**已有 agent 不回填**——本仓当前 agent 数为 0，该句是为将来预留，写明可避免后续有人纠结存量。

## 7. 版本真源下移与触发矩阵

### 7.1 版本号分两类，不可混为一谈

这是整节的立论基础：**版本号应挂在「分发单元」上，而分发单元是插件，不是 skill 也不是 agent。**

harness 拉取、缓存、更新的最小粒度就是插件——所以插件层的版本号是**功能性的**（改了它 harness 才知道要拉新内容），产物层的版本号是**描述性的**（供人判断该产物自身演进到哪一步）。

| 类别 | 层级 | 消费者与后果 | 本次决策 |
|---|---|---|---|
| **功能性** | `.claude-plugin/plugin.json`（每插件） | Claude Code 用它决定「要不要拉新版本」。官方原文：设了 `version` 就 pin 到该字符串，用户只在你 bump 时才收到更新 | ✅ **新建并写 `version`** |
| **功能性** | `.codex-plugin/plugin.json`（每插件） | Codex 侧同上 | ✅ **保留 `version`**，与上一行**同步升级、保持同值**（§ 7.6） |
| 描述性 | `marketplace.json` **顶层** | 描述 marketplace 集合自身；**不在官方回退链里**，官方也未赋予它任何行为（§ 2.11.3） | ✅ **保留**，语义收窄为「集合里有哪些插件」——**仅在增删插件时升**（§ 7.4 要点 3），不再是任何插件的版本来源 |
| — | `marketplace.json` **插件条目内** | 官方回退链第 2 级，会被 `plugin.json` **静默覆盖**；且本仓条目 `source` 为本地路径，填了还会触发官方的不一致警告（§ 2.11.3） | ❌ **主动舍弃**，永不填写 |
| 描述性 | `SKILL.md` 的 `metadata.version` | **无 harness 读取**，纯人工与本仓脚本消费 | ✅ **保留** |
| 描述性 | `agent-docs/<name>/CHANGELOG.md` 的 `## [x.y.z]` | 同上（agent frontmatter 无 `metadata` 合法字段，§ 2.9） | ✅ **新建** |

**插件版本真源是「这两份文件构成的一对」**，不是其中某一份——两份同步升级、始终同值，任一份单独看都是完整的真源，合起来是同一个事实的两个 harness 视图（§ 7.6）。

⚠️ **两类版本号不换算、不同步、不要求任何对应关系。** 试图让 `csharp-code-review` 的 `1.5.5` 与插件的 `12.1.9` 对应是无解的——一个插件多个 skill、各自迭代节奏不同。这正是 § 2.11.1 那套「统一编号」机制自然失去语义的根本原因。

⚠️ **注意「真源」在两个层级上各有一个，不冲突**：插件版本的真源是那对 `plugin.json`；agent 版本的真源是 `agent-docs/<name>/CHANGELOG.md`。它们描述的是不同的东西（分发单元 vs 单个产物），不存在谁覆盖谁。

### 7.2 决策变更记录：为什么 `plugin.json` 从「不写 version」改为「写 version」

本 spec 撰写过程中该决策**反转过一次**，记录在此以免后续维护者困惑于两种说法：

| 阶段 | 结论 | 前提 |
|---|---|---|
| 初版（§ 2.6 发现官方警告后） | `plugin.json` **绝不写 `version`** | 「marketplace 为版本号唯一真源」——写了会静默覆盖，使该声明失效 |
| **现版（§ 2.11 实测后）** | `plugin.json` **必须写 `version`** | 该前提本身不成立：marketplace **顶层** `version` 不在官方回退链里，Claude 侧压根不读它（§ 2.11.2）。「静默覆盖」的顾虑随前提一起消失 |

⚠️ 官方那条警告仍然有效，只是**适用条件被规避掉了**——它警告的是「两处都写」。本设计规定 marketplace 插件条目永不填写 `version`，因此不存在两处冲突。

§ 3.2 已按现版结论改写，与本节一致。

### 7.3 各插件的起始版本号：全部重置为 `1.0.0`（已决策）

现有版本号（12.1.8 ~ 14.0.0）**语义为空**（§ 2.11.2）。用户决策：**9 个本仓插件全部重置为 `1.0.0`**（外部引用的 `cangjie-skill` 不参与，见 § 7.7.1），视为「插件级独立版本化的第一版」。此后各插件按自己的改动独立递增，号与号之间不再有任何关联。

被放弃的方案是「沿用当前值继续递增」——它避免了视觉跳变，但会把无语义的三段数字永久继承下去，`optimus-office-plugin` 的那个 `12` 将永远无法解释。

#### 7.3.1 ⚠️ 新建 plugin.json 后的解析与更新行为必须先验证（实施第一步）

本次是给从未有过 `.claude-plugin/plugin.json` 的插件**首次设立**该文件。设立后 Claude 侧的版本解析会从官方回退链的兜底项切换到 `plugin.json` 的值，需先在单点确认该值能被正确解析、且已安装用户能正常收到更新，再全量推广。

因此实施顺序上这是**第一个动作，不是最后的验收项**：

1. 先只改一个插件（建议 `optimus-mcp-servers`——它无 skills，改动面最小、影响最低）
2. 跑 `claude plugin list` 看改动前解析到什么，再 `update` / `install` 后复看，确认变为 `1.0.0`
3. 通过 → 推广至其余 8 个；**不通过 → 停下来回报，本节决策需要重新评估**

⚠️ **一个曾经的担心已被实测证伪，记录于此避免重复顾虑**：原先担心「`12.1.8` → `1.0.0` 版本号变小，客户端若按『新值 > 旧值才更新』比较，已安装用户会静默卡住」。**该前提不成立**——本仓插件此前没有 `.claude-plugin/plugin.json`，Claude 侧按官方回退链解析到的是 **git commit SHA**（形如 `ae8271959d92`）；`.codex-plugin/plugin.json` 里那个 `12.1.8` 只有 Codex 侧读取，从未进入 Claude 侧用户的本地缓存。因此本次不是「降版本」，而是「SHA → 语义化版本」的首次建立，不存在可供数值比较的旧语义化版本。实测更新行为是**按提交拉取**，不做版本号大小比较。

⚠️ 前提被证伪不等于验证可跳过——需要确认的已从「变小是否触发更新」变为「新设的 `version` 是否被正确解析」，验证动作本身仍是第一步。

### 7.4 触发矩阵：什么改动升哪一层

核心规则：**改动物理上落在哪个分发单元内，就升那个单元的版本号；产物级版本号只在改动落在该产物内部时才升。**

下表「插件 `plugin.json`」列指的是**两份 `plugin.json`（`.claude-plugin/` 与 `.codex-plugin/`）在同一次改动内一起升到同一个新值**——它们总是同进同退，故合并为一列（§ 7.6）。

| 改动的文件 | 插件 `plugin.json` | `SKILL.md` `metadata.version` | agent CHANGELOG | `marketplace.json` 顶层 |
|---|---|---|---|---|
| `plugins/*/skills/<name>/` 内任一文件（SKILL.md / references / scripts / CHANGELOG / README） | ✅ **升** | ✅ **升** | — | ❌ |
| `plugins/*/agents/<name>.agent.md` | ✅ **升** | — | ✅ **升** | ❌ |
| `plugins/*/agent-docs/<name>/` 内文件 | ✅ **升** | — | ✅ **升** | ❌ |
| `plugins/*/hooks/` 内脚本或配置 | ✅ **升** | — | — | ❌ |
| `plugins/*/scripts/`、`.mcp.json`、`mcp.config.json` 等插件级资源 | ✅ **升** | — | — | ❌ |
| `plugins/*/README.md`（插件根） | ✅ **升** | — | — | ❌ |
| **新增或删除整个插件** | ✅ 新插件起 `1.0.0` | — | — | ✅ **升**（集合构成变了） |
| `marketplace.json` 的插件 `description` / `displayName` 等展示元数据 | ❌ | — | — | ❌ **不升**（收窄，见要点 3） |
| **只改 `plugin.json` 自身的 `version`**（如修正漏升） | ❌ **不再升** | — | — | ❌ |
| **外部 url 源条目**（`cangjie-skill`）的 `sha` / `ref` 更新 | — 无该文件 | — | — | ❌ 不升（版本即 `sha`，§ 7.7.1） |
| `.claude/` 下任何文件（rules / skills / hooks） | ❌ | — | — | ❌ |
| `docs/`、`knowledge-base/`、`AGENTS.md`、`CLAUDE.md` | ❌ | — | — | ❌ |

**六条判读要点：**

1. **同一次改动可能同时升两层**——改 SKILL.md 就要同时升该 skill 的 `metadata.version` 与所属插件的 `plugin.json`。这不是重复，是两类版本号各自记录不同的事（「这个 skill 变了」与「这个插件的分发内容变了」）
2. **`marketplace.json` 顶层只在「集合里的插件数变了」时升**——新增或删除插件。**除此以外一律不升**，包括改插件内部内容、改插件描述。这是与现状最大的差异
3. ⚠️ **`description` 变更不升顶层版本号（本条为刻意收窄）**。`description` 是给用户看的展示文本，改它不改变集合构成，也不影响任何 harness 的行为——顶层 `version` 本就不参与版本解析（§ 2.11.3）。让展示文案的微调牵动一个版本号是纯粹的记账负担。**代价须承认**：顶层版本号因此不再能追溯「描述改过几次」，这类改动只能靠 git history 追溯。取舍成立的前提是它本来也没有任何机制消费者
4. **`.claude/` 与 `docs/` 一律不升任何版本号**——它们不随插件分发，harness 读不到
5. ⚠️ **「只改 version 本身」不构成再升一次**（表中第 9 行）。补上某一侧的漏升、或本次全量重置为 `1.0.0`，都属于版本号自身的维护，不是插件内容变更。**否则会陷入无法终止的递归**——升版本要改 `plugin.json`，改 `plugin.json` 又要升版本。微软 Nerdbank.GitVersioning 用 `pathFilters` 排除 manifest 自身来解决同一问题（§ 2.10），我们靠这条规则手工排除
6. **外部 url 源引用不参与任何一层**——它的版本由上游的 commit SHA 决定，我们既无处写也不该代写（§ 7.7.1）

**收窄后的净效果**：顶层 `version` 成为一个**变动极少的号**——只在插件目录增删时动。本仓当前 10 个条目，若未来一年不增删插件，它会一直停在 `14.0.0`。这是预期行为，不是遗漏。

### 7.5 升级幅度判定

各层独立判定，互不影响：

| 层级 | Major | Minor | Patch |
|---|---|---|---|
| 插件 `plugin.json`（两份同步） | 删除/重命名用户可见功能（skill、agent、command） | 新增 skill / agent / hook / command | 修改或修复已有内容 |
| `SKILL.md` `metadata.version` | 接口不兼容、删除用户可见功能 | 新增功能 / 章节 / 参数 | 修改、修复、文档优化、重构 |
| agent CHANGELOG | 删除或重命名 agent、破坏调用契约 | 新增能力 / 章节 / 扩大适用范围 | 修改已有行为、修复措辞、优化 description |
| `marketplace.json` 顶层 | 删除插件 | 新增插件 | **无对应场景**（见下） |

⚠️ **同一次改动在不同层的幅度可以不同**：给某 skill 新增一个章节 → 该 skill `metadata.version` 升 **Minor**，但所属插件只是「修改已有内容」→ `plugin.json` 升 **Patch**。不要求两层幅度一致。

⚠️ **两份 `plugin.json` 的幅度必然一致**——幅度由本次改动的性质决定，两份文件记录的是同一次改动，不存在「一份升 Minor 另一份升 Patch」的情形（§ 7.6）。

⚠️ **顶层 `version` 的 Patch 位永久停在 `0`**：收窄后（§ 7.4 要点 3）它只有「新增插件 → Minor」「删除插件 → Major」两种触发，没有任何改动会落到 Patch。这是收窄的直接结果，不是遗漏——**实施时不要为了「填满三档」而给它编造 Patch 场景**。若日后确实需要记录集合层面的小改动，届时再单独评估，不预留。

### 7.6 两份 plugin.json 同步升级，不存在抄录关系

原机制是「`.codex-plugin/plugin.json` 的 `version` **从** `.claude-plugin/marketplace.json` **抄录**」——抄录隐含一个抄录源和一个副本。真源下移后**这个关系整体取消**：

```
改动了某插件的内容
        ↓  同一次改动内
┌───────────────────────────────┬───────────────────────────────┐
│ .claude-plugin/plugin.json    │ .codex-plugin/plugin.json     │
│         version ↑             │         version ↑            │
└───────────────────────────────┴───────────────────────────────┘
        两份并列，同步升到同一个新值，无先后无主从
```

**规则一句话**：修改了某插件相关内容后，该插件的两份 `plugin.json` 的 `version` **在同一次改动内一起升级，且升到相同的值**。

**为什么不是抄录**，三条实质差异：

| 维度 | 抄录（旧机制） | **同步升级（本设计）** |
|---|---|---|
| 时序 | 有先后——先定主、再同步从 | **无先后**，同一次改动内一起改 |
| 中间状态 | 存在合法的「主已改、从未改」窗口 | **任何时刻不一致都是错误状态** |
| 谁决定新值 | 抄录源决定，副本无判断权 | **本次改动的性质决定**（按 § 7.5 幅度表），两份文件同等地是这个决定的记录 |

第三条是关键：新版本号不是从某个文件里读来的，而是**从「这次改了什么」推导出来的**（新增 skill → Minor、修 bug → Patch）。两份文件都是这个推导结果的载体，谈不上谁抄谁。

⚠️ **因此也不存在「不一致时以哪边为准」**——两边都不为准，**为准的是本次改动的性质**。发现不一致时正确的处置是回头看这次改了什么、该升到什么号，然后把两份都写成那个号；而不是拿一边去覆盖另一边（那样有 50% 概率把正确的一边改错）。

#### 7.6.1 必须补自动校验（本次唯一需要新增的自动化）

原机制下抄录源是**唯一的**（marketplace 顶层一个值），改任何插件都写同一个数——漏改容易被发现，因为 9 个插件的号本该趋同。下移后每个插件有自己的号，**失去了单一参照物**：`optimus-media-plugin` 的 Codex 侧停在 `1.0.1` 而 Claude 侧已是 `1.0.2`，肉眼扫过去毫无异常。

| 项 | 规格 |
|---|---|
| 落点 | `commit-cc-plugin` skill 的提交前检查环节 |
| 检查内容 | 对本次改动涉及的每个插件，比对两份 `plugin.json` 的 `version` |
| 不一致时 | **阻断提交**，提示「插件 `<name>` 的两份 `plugin.json` 版本不一致（`.claude-plugin` = X，`.codex-plugin` = Y）。请按本次改动的性质（§ 7.5）确定应升到的版本号，并把**两份都**改成该值」 |
| ⚠️ 提示措辞的硬要求 | **不得**写成「以 `.claude-plugin` 为准」——那会诱导直接覆盖，而正确动作是回头判断本次改动该升什么号（见上文 ⚠️） |
| 参照实现 | `.claude/skills/knowledge-base-maintain/scripts/check_index.py` L335-358 已有同构逻辑（比对领域 README 的 `> 版本：x.y.z` 与 CHANGELOG 的 `## [x.y.z]`），可直接借其模式 |

⚠️ 实现细节（改 `commit-cc-plugin` 正文还是加独立 Python 脚本）留待实施计划决定，本 spec 只定「必须有」与「阻断而非警告」。

**为什么必须阻断而非警告**：版本不一致的后果是两个 harness 的用户看到不同版本号，且**无任何报错**（§ 2.11.2 已实证这类静默失真会长期存在）。警告会被划过去，静默失真会一直留着。

### 7.7 存量补齐范围

| 项 | 处理 |
|---|---|
| **验证新建 plugin.json 后版本能否被正确解析并更新** | ⚠️ **实施第一步**，见 § 7.3.1。先在 `optimus-mcp-servers` 单点验证，不通过则停下回报 |
| **9 个本仓插件**新建 `.claude-plugin/plugin.json` | **本次全部建**，`version` 一律 `1.0.0`——不建则 Claude 侧继续落到 commit SHA，改动只对 devops 一个生效等于没改 |
| 同 9 个插件的 `.codex-plugin/plugin.json` | `version` 全部改为 `1.0.0`，与上一行**同一次改动内一起写**。这 9 个与上一行完全同一批，无缺口 |
| **`cangjie-skill`（第 10 个条目）** | ❌ **排除在本机制之外**，见 § 7.7.1 |
| `marketplace.json` 顶层 `version` | ⚠️ **本次不改**（保持 `14.0.0`）。它描述集合自身，本次未新增/删除插件（§ 7.4）。**注意它与各插件的 `1.0.0` 并存不是矛盾**——两者描述不同对象，顶层的 `14.0.0` 记录的是这个 marketplace 集合演进了 14 个大版本 |
| `marketplace.json` 插件条目 | 确认 10 个条目均无 `version`（实测已无），无需改动，规范里写明「永不填写」 |
| 9 个缺 `metadata.version` 的 SKILL.md | ⚠️ **不在本次范围**——补齐需逐个判断该给什么版本号（首版 1.0.0？还是按其 CHANGELOG 历史推算？），是独立的一轮工作。本次只在规范里明确该字段为 MUST，存量缺口另期处理 |

#### 7.7.1 `cangjie-skill` 是外部引用，排除在版本机制之外（已实测）

§ 2.11 记录的「marketplace 10 个条目 vs `.codex-plugin/plugin.json` 只有 9 个」不是遗漏，实测原因如下：

```json
{
  "name": "cangjie-skill",
  "source": { "source": "url", "url": "https://github.com/kangarooking/cangjie-skill.git",
              "ref": "main", "sha": "b633a4f..." },
  "strict": false,
  "skills": ["./"]
}
```

**它不在 `plugins/` 目录下**，`source` 是外部 git url 且 `sha` 已显式固定。三条推论：

1. **我们无法给它建 `.claude-plugin/plugin.json`**——那个文件在别人的仓库里
2. **不该在 marketplace 条目里替它编 `version`**——上游有自己的迭代节奏，我们编的号会与之脱节，且会掩盖真实来源
3. **它的版本语义已经完备**：按官方回退链（§ 2.6），url 源缺 `version` 时落到第 3 级 **git commit SHA**，而 `sha` 字段已锁定到 `b633a4f`。这个 SHA 就是它的版本，精确且无需维护

**因此本次改动的实际覆盖面是 9 个本仓插件，不是 10 个。** 规范中须为外部引用类条目写明这条例外，否则后续有人按「所有插件都要有 plugin.json」执行时会卡在这里。

⚠️ 顺带记录：`cangjie-skill` 的 `strict: false` 与 `skills: ["./"]` 是 Claude 侧独有能力（Codex 无对等机制），因此它本来就只在 Claude 侧生效——这也解释了为何它没有 `.codex-plugin/plugin.json`。

## 8. 连带改动清单

### 8.1 必改文件

| 文件 | 改动 | 不改的后果 |
|---|---|---|
| `.claude/rules/doc-conventions.md` | **新建**：编辑铁律 + CHANGELOG 规范 + README 规范（含 agent 分栏） | 拆分无共用层 |
| `.claude/rules/agent-conventions.md` | **新建**：按 § 5 规格 | agent 规范无处安放 |
| `.claude/rules/skill-conventions.md` | 瘦身：`paths` 收窄为单条 `**/SKILL.md`；移出编辑铁律 / Agent 规范 / CHANGELOG / README 四节；开头补一句指向 `doc-conventions.md` | 拆分未完成，宽 glob 仍在 |
| `AGENTS.md` L28 | 「不适用于 agent 的 skill 规范（CHANGELOG / README / darwin-skill 门禁）」→ 改为「**agent 配套文档与版本管理见 `agent-conventions.md`**」，并删去 CHANGELOG/README 的豁免表述；**同时删去「两个 harness 均自动发现该目录，无需在清单文件声明」**（§ 2.3/§ 2.4 已推翻） | 与新规范直接矛盾 |
| `AGENTS.md` L76 | 「Skill frontmatter / CHANGELOG 规范见 `skill-conventions.md`」→ 拆为三份文件各自的职责与触发路径 | 指向失真 |
| `AGENTS.md` L106 关键文件表 | 增 `doc-conventions.md`、`agent-conventions.md` 两行；`marketplace.json` 那行的用途从「插件仓库元数据和版本号真源」改为「**插件清单与展示元数据；顶层 `version` 仅记录集合构成，不是插件版本来源**」；增 `plugins/*/.claude-plugin/plugin.json` 一行标为「**每插件版本真源（与 `.codex-plugin/plugin.json` 同步同值）**」 | 新文件不可发现；版本真源指向错误 |
| **`AGENTS.md` 版本管理节** | ⚠️ **整节重写**（现文三段全部失效）：① 版本升级表的落点从 marketplace 改为每插件的**两份 `plugin.json`**；② **删去抄录规则**（原文「`.codex-plugin/plugin.json` 的 `version` 从 `.claude-plugin/marketplace.json` 抄录，不是独立真源」）——改为「改动插件内容后，该插件两份 `plugin.json` 的 `version` 同步升级并保持同值，新值由本次改动性质决定」；③ 新增 § 7.4 触发矩阵（什么改动升哪一层，含「只改 version 本身不再升」一条）与 § 7.5 幅度判定；④ 写明产物级版本号（skill `metadata.version` / agent CHANGELOG）与插件级不换算；⑤ 写明外部 url 源条目（`cangjie-skill`）不参与本机制 | 现文声明的真源不成立（§ 2.11.2），照它执行会继续产生无语义的版本号 |
| **9 个本仓插件 `.claude-plugin/plugin.json`** | **全部新建**，写 `name` + `version: "1.0.0"`（+ 有 agent 的插件写 `agents`） | Claude 侧继续落到 commit SHA（§ 7.7） |
| **同 9 个插件 `.codex-plugin/plugin.json`** | `version` 改为 `1.0.0`，与上一行同一次改动内一起写 | 两 harness 版本不一致 |
| **`commit-cc-plugin` skill** | 新增校验：改动插件的两份 `plugin.json` 的 `version` 须同值，不一致则**阻断**。⚠️ 报错措辞按 § 7.6.1——提示「按本次改动性质确定版本号，两份都改成该值」，**不得**写「以某一份为准」 | 各插件独立编号后失去单一参照物，漏升一侧的失真是静默的 |
| `knowledge-base/catalog.json` | `skill-authoring` 的 `consumers` 增两个新文件路径 | 消费者登记失真 |
| `knowledge-base/README.md` L151 | 描述里「CHANGELOG、README」职责移交说明 | 陈述性错误 |
| `knowledge-base/skill-authoring/README.md` L68 | 同上 | 同上 |

### 8.2 `dotnet-diagnose` spec 的同步修正

`2026-09-05-dotnet-diagnose-agent-design.md` 有六处受本次结论影响：

| 位置 | 改动 |
|---|---|
| § 2.5 双 harness 均等性表 | 「agent 目录…自动发现，无需在 manifest 声明」→ 改为显式声明；并补 `.agent.md` 命名来源（VS Code 约定非 CC 官方） |
| § 8.1 交付文件清单 | 增 `agent-docs/dotnet-diagnose/CHANGELOG.md`（初始 `[1.0.0]`）与 `README.md`；增新建 `.claude-plugin/plugin.json`；表中「适用规范」列的「agent 规范（四字段，无 CHANGELOG/README）」须改为「有 CHANGELOG/README，见 `agent-conventions.md`」 |
| § 8.2 frontmatter 规格 | 现文写「不加 `metadata.version`…**版本由 marketplace 统一管理**」——后半句失效，改为「agent 版本记在 `agent-docs/<name>/CHANGELOG.md`；frontmatter 不写版本字段的理由是插件 agent 无 `metadata` 合法字段」 |
| **§ 8.4 同期改动表** | ⚠️ **两行须重写**：① `.claude-plugin/marketplace.json` 那行「顶层 `version` 14.0.0 → 14.1.0」失效——收窄后顶层只在增删插件时升（§ 7.4 要点 3），**新增 agent+skill 且改 `description` 都不动它**。改为「devops 的两份 `plugin.json` 升 **Minor**（新增 agent + skill）；marketplace 只改 `description`，顶层 `version` 保持 `14.0.0`」；② `.codex-plugin/plugin.json` 那行「version 同步 14.1.0」改为「与 `.claude-plugin/plugin.json` 同步升级、同值」 |
| § 8.5 门禁落点 | agent 层现在也有 CHANGELOG/README 要求，但 darwin-skill 仍豁免、`known-issues.md` 仍不要求——须重新表述 |
| § 10.2 / § 10.4 验收清单 | § 10.2 增 agent 的 CHANGELOG/README/版本号一致性核对；**§ 10.4 的「marketplace 14.1.0 与 `.codex-plugin/plugin.json` 版本一致」须改为「devops 两份 `plugin.json` 版本一致且已升 Minor，marketplace 顶层保持 `14.0.0`」**；删去「`plugin.json` 不含 `version` 的检查项」（该项已反转） |

### 8.3 明确不改动

- **`plugins/*/skills/` 下现状全部不变**：SKILL.md + CHANGELOG + README 同目录是安全的（`skills/<name>/` 是「一个实体的组成部分」，非可调用实体列表，§ 2.3）
- **不回填 9 个缺 `metadata.version` 的 SKILL.md**：§ 7.7 已说明理由——补齐需逐个判断该给什么号，是独立一轮工作。本次只在规范里明确该字段为 MUST
- **不改 `marketplace.json` 的插件条目与顶层 `version`**：实测 10 个条目均无 `version`，现状即符合 § 7.1 的「永不填写」；顶层保持 `14.0.0`（§ 7.7）
- **不改 `cangjie-skill` 条目**：外部 url 源，不参与本机制（§ 7.7.1）
- **不引入 Nerdbank.GitVersioning 自动版本化**：§ 2.10 记录了微软的成熟范式可借鉴，但引入构建期工具链超出本次范围
- **不回填存量 spec 的产物形态声明**：与既有判断一致（收益低于改动面）
- **不改 `knowledge-base/skill-authoring/` 正文与 `index.jsonl`**：本次是仓库专属约定的重组，不涉及通用规范条款

## 9. 验收标准

### 9.1 拆分正确性

- [ ] 三份规则文件各自 `paths` 生效：编辑 `SKILL.md` 只加载 `skill-conventions.md`；编辑任一 `CHANGELOG.md` 只加载 `doc-conventions.md`；编辑 `agents/*.md` 只加载 `agent-conventions.md`
- [ ] `skill-conventions.md` 的 `paths` 只剩 `**/SKILL.md` 一条
- [ ] 八个现有章节按 § 4.2 表逐节归位，**无内容丢失**（拆分前后三份文件总行数 ≥ 248，差额即 agent 分栏新增）
- [ ] 交叉引用为单向（两份专属 → 共用层），`doc-conventions.md` 内**无**反向指向
- [ ] `skill-conventions.md` 文件名未改，全仓 5 处活引用无需改动

### 9.2 agent 规范正确性

- [ ] § 5.2 四处改写全部落地。**原豁免声明共 3 处**（现文件 L111 `不写 metadata.version…不独立版本化`、L125 不适用表的 `CHANGELOG.md | 不要求`、L197 CHANGELOG 规范节的 `agent 不要求 CHANGELOG.md`），须逐处处理：前两处随 Agent 规范迁入 `agent-conventions.md` 时改写，第三处随 CHANGELOG 规范迁入 `doc-conventions.md` 时按 § 6.1 改写。验证：三份新文件 grep 「不要求 CHANGELOG」「不独立版本化」应无命中
- [ ] 目录结构两条禁令（禁子目录 / 禁辅助文件）各配独立理由
- [ ] 版本管理三行升级表 + 「不得写 `plugin.json` 的 version」警告
- [ ] `.agent.md` 命名来源已写明为 VS Code 约定
- [ ] darwin-skill 与 `known-issues.md` 仍豁免的表述与 CHANGELOG/README 要求并存且不矛盾

### 9.3 README/CHANGELOG 规范正确性

- [ ] README 六章节的 skill / agent 两栏差异表落地，两章分叉（所处层级、触发词）各写明分叉理由
- [ ] CHANGELOG 格式共用、仅豁免声明改写
- [ ] 适用范围补 agent 一句，并写明「已有 agent 不回填（当前为 0）」

### 9.4 版本真源下移正确性

- [ ] ⚠️ **首个动作**：新建 `plugin.json` 后版本能被正确解析为 `1.0.0` 并正常更新，已在 `optimus-mcp-servers` 单点验证通过（§ 7.3.1）——**未验证不得推广至其余 8 个**
- [ ] 9 个本仓插件均有 `.claude-plugin/plugin.json`，各含 `name` + `version: "1.0.0"`；有 agent 的插件另含 `agents` 文件路径数组
- [ ] 9 个插件的 `.codex-plugin/plugin.json` 的 `version` 均为 `1.0.0`，与同插件 `.claude-plugin/plugin.json` 逐一比对同值
- [ ] `cangjie-skill` **未被改动**——它是外部 url 源，不建 `plugin.json`、不填 `version`（§ 7.7.1）
- [ ] `marketplace.json` 的 10 个插件条目**均无 `version` 字段**（避免触发官方的 local-path 不一致警告，§ 2.11.3）
- [ ] `marketplace.json` 顶层 `version` **保持 `14.0.0` 不变**——本次未增删插件（§ 7.4 要点 2/3；即使改了插件 `description` 也不升）
- [ ] `commit-cc-plugin` 的同值校验已落地，且**用一个故意不一致的用例验证过它真的会阻断**（只加代码不验证等于没加）；报错措辞为「按本次改动性质确定版本号，两份都改成该值」，**未**写成「以某一份为准」（§ 7.6.1）
- [ ] `AGENTS.md` 版本管理节已整节重写，全文 grep「抄录」「共用的版本号真源」应**无命中**
- [ ] § 7.4 触发矩阵与 § 7.5 幅度表已进 `AGENTS.md`，且矩阵含这三行：「`.claude/` 与 `docs/` 一律不升」、「只改 `version` 本身不再升」、「外部 url 源条目不参与」

### 9.5 连带改动

- [ ] `AGENTS.md` 四处改动完成（L28 / L76 / L106 关键文件表 / 版本管理节整节重写）
- [ ] `catalog.json` consumers 已增两项，JSON 可解析
- [ ] `knowledge-base/README.md` 与 `skill-authoring/README.md` 的职责描述已同步
- [ ] `dotnet-diagnose` spec 六处同步修正完成（§ 8.2）
- [ ] `python .claude/skills/knowledge-base-maintain/scripts/check_index.py` PASS，条目数不变
- [ ] `check_refs.py` PASS
- [ ] **9 份新建的 `plugin.json` 均可被 JSON 解析**，且 `claude plugin validate ./plugins/<name>` 对每个插件通过
- [ ] 全部改动经 `commit-cc-plugin` 推送

⚠️ **本次改动的版本号落点**：规则文件拆分部分全在 `.claude/` 与 `docs/` 下（不升任何版本号）；新建 9 份 `plugin.json` 虽落在 `plugins/` 下，但按 § 7.4 矩阵倒数第三行「**只改 `plugin.json` 自身的 `version` 不再升**」——新建这份文件本身就是在设立版本号载体，其首个值即 `1.0.0`，不存在「在它之上再升一次」。**实施时直接写 `1.0.0`，不额外递增。**

### 9.6 实施顺序约束

⚠️ 本 spec 与 `dotnet-diagnose` 的实施有依赖关系：**本 spec 必须先落地**，否则 agent 实施时无规范可依（`agent-docs/` 目录约定、`plugin.json` 声明方式、版本号载体都在本 spec 定义）。

## 10. 不在本次范围

| 项 | 归属 |
|---|---|
| `dotnet-diagnose` agent 与 skill 的实际创建 | `2026-09-05-dotnet-diagnose-agent-design.md` |
| 9 个缺 `metadata.version` 的 SKILL.md 回填 | § 7.7 已说明——需逐个判断起始号，独立一轮 |
| Nerdbank.GitVersioning 式自动版本化 | § 2.10 已记录范式，超出本次 |
| 存量 spec 回填产物形态声明 | 收益低于改动面 |
| `check_refs.py` 的 `CONSUMER_GLOBS` 扩展 | 属 `dotnet-diagnose` spec § 8.4 范围 |

⚠️ 原「双 harness 版本漂移隐患的修复」与「其余 8 个插件新建 `.claude-plugin/plugin.json`」两项**已移入本次范围**（分别见 § 7.6 与 § 7.7）。
