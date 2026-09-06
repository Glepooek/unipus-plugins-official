# AGENTS.md

本文件为 AI 编码 agent（Claude Code / OpenAI Codex）在此仓库中工作时提供指导。

## 仓库定位

自定义插件仓库，提供企业级开发工具链，**同时支持 Claude Code 与 OpenAI Codex 双 harness**。

各插件职责见 `.claude-plugin/marketplace.json` 的 `description` 字段。

**核心原则：单一真源，两个 harness 共用。** 所有 skill 内容只在 `plugins/*/skills/*/SKILL.md` 维护一份（开放 Agent Skills 规范，agentskills.io 六字段 frontmatter），两个 harness 各自的清单文件（`.claude-plugin/marketplace.json` / `.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json`）只是指向同一份内容的安装入口，不重复维护技能正文。下文规则默认对两个 harness 同时生效；仅在**必要差异**一节列出的地方才有分叉。

---

## Skill 分层与调用

**两层 skill，不要混淆：**

| 位置 | 性质 | Claude 调用 | Codex 调用 |
|---|---|---|---|
| `plugins/*/skills/` | 对外发布的插件产物 | `/plugin-name:skill-name` | 自然语言触发（按 description 匹配）或 `@plugin-name:skill-name` |
| `.claude/skills/` | 仅本仓库维护自用，不发布 | `/skill-name`（无前缀，经 `.kiro/skills/` 镜像） | 同名触发（经 `.agents/skills/` 镜像） |

`.claude/skills/` 下的 skill 需在 `.kiro/skills/`（Claude/Kiro 生态）与 `.agents/skills/`（Codex）**两处**保持同名符号链接镜像，`commit-cc-plugin` 会自动检测并补齐两处。

复合 skill 调用：`/plugin-name:skill-name:substep`（两个 harness 语法一致，仅前缀符号不同）。

**第三种产物形态：agent**（`plugins/*/agents/<name>.md`）。与 skill 的区别是上下文隔离——skill 注入当前对话，agent 独立上下文只收一个 prompt，适合单次可闭环、且需与主对话隔离的判定类任务。**必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**（该字段是 replaces 语义，声明后默认目录扫描被取代，杜绝把配套文档误加载成假 agent）；Claude 侧按 `plugin-name:agent-name` @-mention 调用，Codex 侧同名触发。agent 的配套文档放 `plugins/*/agent-docs/<name>/`（**不放 `agents/`**）、独立版本化、以及 darwin-skill 门禁豁免等细则，见 `.claude/rules/agent-conventions.md`。

---

## 重要约束（两个 harness 通用）

- **跨插件无重复 skills**：每个插件专注特定领域，新功能前先确认无跨插件重叠
- **Skills 可相互引用**：子 skill 用相对路径，跨插件用绝对命名空间
- **复合 skills 很少见**：仅在 3 个以上阶段且每阶段 >200 行时使用
- **新 skill 上线前自检**：这个 skill 是「引导器」（指导用户/agent 完成某件事）还是「传感器」（校验/检测已有产物是否合规）？有没有配对的另一半（例如有生成类 skill 却没有对应的校验类 skill）？避免只造轮子不造刹车
- **SKILL.md 是唯一真源**：修改技能行为只改 `plugins/*/skills/*/SKILL.md`，不要为 Codex 单独维护副本或调整 frontmatter——两个 harness 读的是同一份文件

---

## 本地测试

见 `test-locally` skill（`/test-locally` 触发）。

Python 脚本单元测试（**本机无 `pytest`，只能用 `unittest`**）：

```bash
# 维护型 skill（各自独立跑，unittest discover 不递归跨目录）
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py"  # 77 tests
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py"     # 141 tests
python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py"                # 46 tests
```

---

## 版本管理规则

### 版本号分两类

**功能性**——harness 用它决定要不要拉新版本，改了才生效：

- `plugins/<plugin>/.claude-plugin/plugin.json` 的 `version`（Claude 侧读）
- `plugins/<plugin>/.codex-plugin/plugin.json` 的 `version`（Codex 侧读）

**这两份是同一个事实的两个 harness 视图**：改动插件内容后，两份在**同一次改动内一起升到同一个新值**。不存在抄录关系与主从关系——新版本号由本次改动的性质决定（见下表），两份文件同等地是这个决定的记录。

**描述性**——无 harness 读取，纯供人判断该产物演进到哪一步：

- `SKILL.md` 的 `metadata.version`（每个 skill 自己的号）
- `agent-docs/<name>/CHANGELOG.md` 的最新 `## [x.y.z]`（每个 agent 自己的号）

⚠️ **两类版本号不换算、不同步、不要求任何对应关系**。一个插件有多个 skill、各自迭代节奏不同，试图让它们与插件号对应是无解的。

⚠️ `.claude-plugin/marketplace.json` 的**顶层** `version` 只记录「集合里有哪些插件」，**仅在增删插件时升**（详见下表）。它不在官方版本解析回退链里，harness 不用它判断插件版本——**它不是任何插件的版本来源**。

⚠️ **marketplace 的插件条目内永不填写 `version`。** 两个原因：① 官方明确「同时写 `plugin.json` 与 marketplace 条目时，Claude Code **总是用 `plugin.json` 的值且不给警告**」——条目里的值只会被静默忽略；② 本仓条目的 `source` 均为本地相对路径，官方对这类条目会额外校验并在两值不一致时报警告。不填则无从冲突。

⚠️ **外部 url 源引用（`cangjie-skill`）不参与本机制**——它不在 `plugins/` 下，我们无处写它的 `plugin.json`；其版本按官方回退链落到已固定的 `source.sha`，精确且无需维护。

### 触发矩阵：什么改动升哪一层

核心规则：**改动物理上落在哪个分发单元内，就升那个单元的版本号；产物级版本号只在改动落在该产物内部时才升。**

| 改动的文件 | 插件 `plugin.json`（两份同步） | `SKILL.md` `metadata.version` | agent CHANGELOG | marketplace 顶层 |
|---|---|---|---|---|
| `plugins/*/skills/<name>/` 内任一文件 | ✅ | ✅ | — | ❌ |
| `plugins/*/agents/<name>.md` | ✅ | — | ✅ | ❌ |
| `plugins/*/agent-docs/<name>/` 内文件 | ✅ | — | ✅ | ❌ |
| `plugins/*/hooks/` 内脚本或配置 | ✅ | — | — | ❌ |
| `plugins/*/scripts/`、`.mcp.json`、`mcp.config.json` 等插件级资源 | ✅ | — | — | ❌ |
| `plugins/*/README.md`（插件根） | ✅ | — | — | ❌ |
| **新增或删除整个插件** | ✅ 新插件起 `1.0.0` | — | — | ✅ |
| marketplace 的插件 `description` / `displayName` 等展示元数据 | ❌ | — | — | ❌ |
| **只改 `plugin.json` 自身的 `version`** | ❌ | — | — | ❌ |
| 外部 url 源条目（`cangjie-skill`）的 `sha` / `ref` | — 无该文件 | — | — | ❌ |
| `.claude/` 下任何文件 | ❌ | — | — | ❌ |
| `docs/`、`knowledge-base/`、`AGENTS.md`、`CLAUDE.md` | ❌ | — | — | ❌ |

**五条判读要点：**

1. **同一次改动可能同时升两层**——改 SKILL.md 要同时升该 skill 的 `metadata.version` 与所属插件的两份 `plugin.json`。这不是重复，是两类版本号记录不同的事
2. **marketplace 顶层只在「集合里的插件数变了」时升**——新增或删除插件。**改插件内部内容、改插件 `description` 都不升它**
3. ⚠️ **「只改 `version` 本身」不构成再升一次**——补上某一侧的漏升、或新建 `plugin.json` 时写入起始号，都属于版本号自身的维护。否则会陷入递归：升版本要改 `plugin.json`，改 `plugin.json` 又要升版本
4. **`.claude/` 与 `docs/` 一律不升任何版本号**——它们不随插件分发，harness 读不到
5. **外部 url 源引用不参与任何一层**——`cangjie-skill` 的版本由上游 commit SHA 决定（`source.sha` 已固定），我们既无处写也不该代写

### 升级幅度

各层独立判定，同一次改动在不同层的幅度**可以不同**（如给某 skill 新增一节 → 该 skill Minor，但插件只是「修改已有内容」→ 插件 Patch）：

| 层级 | Major | Minor | Patch |
|---|---|---|---|
| 插件 `plugin.json`（两份同步） | 删除/重命名用户可见功能 | 新增 skill / agent / hook / command | 修改或修复已有内容 |
| `SKILL.md` `metadata.version` | 接口不兼容、删除用户可见功能 | 新增功能 / 章节 / 参数 | 修改、修复、文档优化、重构 |
| agent CHANGELOG | 删除或重命名 agent、破坏调用契约 | 新增能力 / 章节 / 扩大适用范围 | 修改已有行为、修复措辞 |
| marketplace 顶层 | 删除插件 | 新增插件 | **无对应场景** |

⚠️ **两份 `plugin.json` 的幅度必然一致**——幅度由本次改动的性质决定，两份记录的是同一次改动。

⚠️ **marketplace 顶层的 Patch 位永久停在 `0`**：它只有「新增插件 → Minor」「删除插件 → Major」两种触发。这是刻意收窄的结果，**不要为了填满三档而编造 Patch 场景**。

**功能变了版本号不变 = 不完整交付**——必须主动检查并升版，不等用户提醒。`commit-cc-plugin` 会在提交前校验两份 `plugin.json` 是否同值，不一致则阻断。

### darwin-skill 评分门禁

Minor/Major 升级前必须用 `darwin-skill` 对改动的 skill 评分：新分数 ≥ 改动前分数才可提交，倒退则先修正。（评分产物落在 gitignore 的 `.claude/skills/darwin-skill/results.tsv`，不进版本库。）

**该门禁只约束 skill**——darwin-skill 的 rubric 针对 SKILL.md 结构，对 agent 无对应评分维度，agent 改动改为按其 spec 的验收清单人工核验。

---

## 产物规范（三份规则文件，按编辑路径自动加载）

| 规则文件 | 承载什么 | 编辑什么时自动加载 |
|---|---|---|
| `.claude/rules/skill-conventions.md` | SKILL.md 的六字段 frontmatter、执行前置校验、需求预告、持续优化约定 | `**/SKILL.md` |
| `.claude/rules/doc-conventions.md` | 编辑铁律、CHANGELOG.md 格式、README.md 六章节（含 skill/agent 两栏差异） | `**/CHANGELOG.md`、`plugins/*/skills/**/README.md`、`plugins/*/agent-docs/**/*.md` |
| `.claude/rules/agent-conventions.md` | agent 选型判据、`agents/` 目录硬约束、四字段 frontmatter、配套文档与独立版本化 | `plugins/*/agents/*.md`、`plugins/*/agents/**/*.md` |

三份规范**同时约束两个 harness**——frontmatter 字段是 Codex 也会原样读取缓存的内容，不存在"仅 Claude 遵守"的特例。

---

## 提交与推送

**必须**使用 `commit-cc-plugin` skill，禁止手动执行 git 工作流。说"提交"或"推上去"即可触发。

---

## docs/ 与 knowledge-base/ 的定位划分

两者都是 Markdown 文档集合，但性质不同，新增文档前先判断该落在哪一侧（该判断与 harness 无关）：

| 维度 | `knowledge-base/` | `docs/` |
|---|---|---|
| 内容性质 | **规范条款**（MUST/SHOULD/MAY 语气），可执行的判断依据 | **叙述性资料**：使用指南、历史决策记录、外部资料备份 |
| 消费方式 | 被 skill **编程式检索**（`index.jsonl` + `file`+`anchor` 定位单条） | 人类完整阅读，无检索单条的场景 |
| 版本化 | 有独立版本号 + CHANGELOG，条目级别管理，见 `knowledge-base/README.md` | 无版本号，靠文件名日期或 git history 追溯 |

**判断标准**：这份内容是否需要被某个 skill 按条检索引用作为判断依据？是 → `knowledge-base/`；仅供人类阅读理解（工具怎么用、当时为什么这么设计、外部资料备份）→ `docs/`。

`docs/` 内部已有的分类，供参照：

- `superpowers/specs/`、`superpowers/plans/`：brainstorming→writing-plans 工作流产生的**历史决策记录**，记录某功能当时为什么这么设计，不是可复用规范，不进 knowledge-base
- `claude_blog/`、`claude_docs/`、`url_list.txt`：外部资料备份/追踪表，与本仓库规范无关
- `SUPERPOWERS_GUIDE.md`、`claude-code-config.md`：操作使用指南（怎么用某个工具/插件），非"代码该怎么写"的规范条款，即使内容详尽也不归入 knowledge-base——这类流程性叙述天然依赖线性阅读顺序，拆成索引条目会破坏可读性

---

## 关键文件

| 文件 | 用途 | harness |
|---|---|---|
| `.claude-plugin/marketplace.json` | 插件清单与展示元数据；顶层 `version` 仅记录集合构成，**不是插件版本来源** | 两者共用 |
| `plugins/*/.claude-plugin/plugin.json` | **每插件版本真源**（与 `.codex-plugin/plugin.json` 同步同值）+ `agents` 声明 | Claude 侧读，两者共同维护 |
| `.agents/plugins/marketplace.json` | Codex plugin marketplace 安装入口 | Codex 专属 |
| `plugins/*/.codex-plugin/plugin.json` | 每插件的 Codex 标识清单 + 版本号（与 `.claude-plugin/plugin.json` 同步同值） | Codex 侧读，两者共同维护 |
| `.claude/rules/skill-conventions.md` | SKILL.md frontmatter 规范（按路径自动加载） | 两者共用 |
| `.claude/rules/doc-conventions.md` | CHANGELOG / README 规范（按路径自动加载） | 两者共用 |
| `.claude/rules/agent-conventions.md` | agent 规范（按路径自动加载） | 两者共用 |

**已被 gitignore 的目录（有意排除，非缺失）：** `.claude/skills/darwin-skill/`（评估产物）、`.remember/`、`.codegraph/`

---

## 两个 harness 的必要差异（仅此一处，其余规则均通用）

| 方面 | Claude Code | Codex |
|---|---|---|
| 安装入口 | `/plugin marketplace add` 或手动 clone 到 `~/.claude/plugins/marketplace/` | `codex plugin marketplace add <repo>` → `codex plugin add <plugin>@optimus-plugins-official`，读取 `.agents/plugins/marketplace.json` |
| 提交流程 | 强制 `/commit-cc-plugin` skill | 标准 git + Conventional Commits，禁止 `--no-verify` |
| Hooks | SessionStart（技巧轮播）、Notification（权限通知）生效 | 无对应机制，Claude 侧 hooks 在 Codex 中不生效 |
| 维护型 skill 镜像目录 | `.kiro/skills/<name>` | `.agents/skills/<name>` |
| 插件标识文件 | `.claude-plugin/marketplace.json`（含全部插件） | 额外的 `.agents/plugins/marketplace.json` + 每插件 `.codex-plugin/plugin.json` |

除以上五项，其余所有规则（约束、frontmatter、版本管理、docs/knowledge-base 划分、本地测试）对两个 harness 一视同仁，不需要也不应该分叉处理。
