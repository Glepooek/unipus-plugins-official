# rules 拆分与版本真源下移 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `.claude/rules/skill-conventions.md` 拆为三份按动作精准加载的规则文件，并把插件版本真源从「marketplace 顶层一个值」下移为「每插件两份 `plugin.json` 同步同值」。

**Architecture:** 三阶段共 9 个任务，每个任务独立可验证、独立提交。

| 阶段 | 任务 | 性质 |
|---|---|---|
| ① 规则文件拆分 | Task 1-3 | 纯 `.claude/` 改动，零版本号影响；Task 1 必须最先（另两份要引用它） |
| ② 版本真源下移 | Task 4-5 | Task 4 是**单点验证 + go/no-go CHECKPOINT**，不通过则停下回报；通过后 Task 5 推广至其余 8 个插件 |
| ③ 规范文本与自动校验同步 | Task 6-9 | `AGENTS.md` 版本管理节整节重写、`commit-cc-plugin` 新增阻断式同值校验、8 处活引用更新、下游 spec 六处修正 |

阶段 ① 与 ② 相互无依赖，可并行；③ 依赖 ① 与 ② 均已落地。

**Tech Stack:** Markdown 规则文件（YAML frontmatter `paths` glob 驱动自动加载）、JSON 清单文件、Python 3（`unittest`，本机无 `pytest`）、`claude plugin validate` CLI。

**Spec:** `docs/superpowers/specs/2026-09-06-rules-split-and-agent-docs-design.md`

## Global Constraints

以下约束对**每个任务**同时生效，任务内不再重复：

- **编辑 Markdown 禁止无关格式化**：不增删空行、不调缩进、不做表格对齐。提交前看 `git diff`，出现大片纯空白变化说明格式化工具介入了，撤销重做。（`.claude/rules/skill-conventions.md` 现有铁律，拆分后移入 `doc-conventions.md`）
- **提交必须走 `commit-cc-plugin` skill**，禁止手动执行 git 工作流。计划中出现的 `git` 命令仅用于**只读检查**（`git status` / `git diff` / `git log`），实际提交由该 skill 完成。
- **本机无 `pytest`，只能用 `unittest`**：`python -m unittest discover -s <dir> -p "test_*.py"`。
- **本次改动的版本号落点**（三条，覆盖全部 9 个任务）：
  - **Task 1-3、6-9** 的改动落在 `.claude/`、`AGENTS.md`、`knowledge-base/`、`docs/` 下 → **不升任何插件版本号**。⚠️ 唯一例外是 Task 7 要升 `commit-cc-plugin` 这个 skill **自身的** `metadata.version`（`3.5.0` → `3.6.0`）——那是 skill 的描述性版本号，不是插件版本号，两者互不相干
  - **Task 4-5** 新建/改动 `plugin.json` 的 `version` 字段本身 → 按 spec § 7.4 要点 5「只改 `version` 本身不构成再升一次」→ **直接写 `1.0.0`，不额外递增**
  - `marketplace.json` 顶层 `version` **全程保持 `14.0.0`**（spec § 7.4 要点 2/3：仅增删插件时升）
- **本仓自有插件是 9 个**，不是 10 个。第 10 个 marketplace 条目 `cangjie-skill` 是外部 git url 引用（`source.source: "url"`，`sha` 已固定），不在 `plugins/` 目录下，**全程不得改动**（spec § 7.7.1）。
- **9 个插件的准确名单**（实测，按字母序）：`optimus-backend-plugin`、`optimus-decision-plugin`、`optimus-devops-plugin`、`optimus-frontend-plugin`、`optimus-mcp-servers`、`optimus-media-plugin`、`optimus-office-plugin`、`optimus-prd-plugin`、`optimus-qa-plugin`。
- **实施顺序硬约束**：本计划必须**先于** `docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md` 落地——agent 实施时要用到本计划定义的 `agent-docs/` 目录约定、`plugin.json` 声明方式、agent 版本号载体（spec § 9.6）。

---

## 文件结构

### 新建（4 个）

| 文件 | 职责 | 预估行数 |
|---|---|---|
| `.claude/rules/doc-conventions.md` | 三类文档共用：编辑铁律 + CHANGELOG 规范 + README 规范（含 skill/agent 两栏差异） | ~95 |
| `.claude/rules/agent-conventions.md` | agent 专属：选型判据、目录硬约束、frontmatter、配套文档、版本管理 | ~80 |
| `plugins/<9 个插件>/.claude-plugin/plugin.json` | 每插件的 Claude 侧清单，承载 `version` 真源 | 各 4 行 |

### 修改（14 个）

| 文件 | 改动性质 |
|---|---|
| `.claude/rules/skill-conventions.md` | 瘦身：`paths` 四条 → 一条；移出 4 节 |
| `plugins/<9 个插件>/.codex-plugin/plugin.json` | `version` → `1.0.0` |
| `AGENTS.md` | 4 处：L28 产物形态段、L76 规范指向段、L106 关键文件表、版本管理节**整节重写** |
| `.claude/skills/commit-cc-plugin/SKILL.md` | 第二步「版本号决策」整节重写 + 新增同值校验环节 + 第三步示例 + 常见错误表 + `metadata.version` → `3.6.0` |
| `.claude/skills/commit-cc-plugin/CHANGELOG.md` | 新增 `[3.6.0]` 条目 |
| `knowledge-base/catalog.json` | `skill-authoring` 的 `consumers` 增两项 + `notes` 改写 |
| `knowledge-base/README.md` L151 | 职责描述拆为三份文件 |
| `knowledge-base/skill-authoring/README.md` L31/L68 | 同上 |
| `knowledge-base/skill-authoring/rules/01-skill-format.md` L5/L84 | 同上 |
| `docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md` | 6 处同步修正（spec § 8.2） |

### 新建的脚本（2 个，随 Task 7）

| 文件 | 职责 |
|---|---|
| `.claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py` | 校验每插件两份 `plugin.json` 的 `version` 同值，暴露 `check_all(repo_root) -> list[str]` |
| `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py` | 11 个 unittest 用例，含「报错措辞不得写以某一份为准」一条 |

### 明确不动

- `plugins/*/skills/` 下全部现状（SKILL.md + CHANGELOG + README 同目录是安全的）
- `marketplace.json` 顶层 `version`（保持 `14.0.0`）与 10 个插件条目（均已无 `version`）
- `.agents/plugins/marketplace.json`（Codex 安装入口）——**实测顶层键只有 `name` / `interface` / `plugins`，无任何 `version` 字段，恰 9 个条目**（不含 `cangjie-skill`，印证它是 Claude 侧独有）。本次版本机制与它无关，不改
- `cangjie-skill` 条目（外部 url 源）
- 9 个缺 `metadata.version` 的 SKILL.md（另期处理）
- `knowledge-base/git/rules/04-versioning-release.md`（实测不含插件版本规则，只讲通用 Git 版本化）
- `knowledge-base/skill-authoring/` 正文与 `index.jsonl`（本次是仓库专属约定重组，不涉及通用条款）
- 历史记录类文件中的 `skill-conventions.md` 引用（`.remember/`、`.superpowers/sdd/`、旧 plan、各 CHANGELOG）——它们记录的是当时事实，不改写

### 拆分后的 `paths` 分工

```
编辑 SKILL.md                      → skill-conventions.md
编辑 任意 CHANGELOG.md             → doc-conventions.md
编辑 skills/**/README.md           → doc-conventions.md
编辑 agent-docs/**/*.md            → doc-conventions.md
编辑 agents/**/*.md                → agent-conventions.md
```

**核心收益**：现状下编辑任一 CHANGELOG（全仓 50+ 个）会注入 248 行，其中约 190 行无关；拆分后只注入 `doc-conventions.md` 的约 95 行且全部相关。

---

## Task 1: 新建 `doc-conventions.md`（共用文档层）

**Files:**
- Create: `.claude/rules/doc-conventions.md`
- Read (不改): `.claude/rules/skill-conventions.md`（源内容在 L9-11、L174-197、L199-240）

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: `.claude/rules/doc-conventions.md`，被 Task 2 的 `skill-conventions.md` 与 Task 3 的 `agent-conventions.md` 各在开头引用一次。三条 `paths` glob：`**/CHANGELOG.md`、`plugins/*/skills/**/README.md`、`plugins/*/agent-docs/**/*.md`

**为什么先做这个**：它是另两份文件的被引用方，先落地才能让后两个任务写出有效引用（spec § 4.3 单向引用方向：两份专属 → 共用层）。

- [ ] **Step 1: 记录搬迁前的基线行数**

Run:
```bash
wc -l .claude/rules/skill-conventions.md
```
Expected: `248 .claude/rules/skill-conventions.md`

把这个数字记下来——Task 3 结束时要验证「拆分前后三份文件总行数 ≥ 248」（差额即 agent 分栏与新增内容）。若实际不是 248，说明文件在计划撰写后被改过，**先停下核对再继续**。

- [ ] **Step 2: 创建文件骨架与 frontmatter**

Create `.claude/rules/doc-conventions.md`：

````markdown
---
paths:
  - "**/CHANGELOG.md"
  - "plugins/*/skills/**/README.md"
  - "plugins/*/agent-docs/**/*.md"
---

## 编辑铁律：禁止无关格式化

编辑 SKILL.md / CHANGELOG.md / README.md 时，只改动语义相关的内容，不增删空行、不调整缩进、不做表格对齐等纯格式化改动。仓库已配置 `.prettierignore`（排除 `*.md`）和 `.vscode/settings.json`（禁用 markdown 自动格式化）作为防护，但仍需自查：提交前看 `git diff`，若出现大片纯空白/缩进变化而无实际内容变化，说明格式化工具介入了，应撤销重做。
````

⚠️ **三条 glob 各有独立作用，不可合并**：
- `**/CHANGELOG.md` 覆盖全仓所有 CHANGELOG（含 skill 目录内、agent-docs 内、插件根）
- `plugins/*/skills/**/README.md` 覆盖 skill 的 README
- `plugins/*/agent-docs/**/*.md` 的**实际增量是 agent 的 README**——前一条 glob 覆盖不到 `agent-docs/`，而 agent 的 CHANGELOG 已被第一条覆盖

- [ ] **Step 3: 追加 CHANGELOG.md 规范节**

Append to `.claude/rules/doc-conventions.md`（原样搬迁自 `skill-conventions.md:174-197`，仅最后一条改写）：

`````markdown

## CHANGELOG.md 规范

每个 skill 目录**必须**有 `CHANGELOG.md`，提交前必须更新，格式：

````markdown
## [版本号] - YYYY-MM-DD

### Added
- 新增的功能或章节

### Changed
- 修改的内容

### Removed
- 删除的内容

### Fixed
- 修复的问题
````

规则：
- 只写实际发生的类别，无变更的类别可省略
- 新建 skill 时同步创建 CHANGELOG.md，初始版本为 `[1.0.0]`
- **agent 的 CHANGELOG.md 放在 `plugins/*/agent-docs/<name>/` 下，不放 `agents/`**——`agents/` 目录下任何 `.md` 都会被注册为可调用 agent（详见 `agent-conventions.md`）
`````

⚠️ **最后一条是改写，不是原样搬迁**。原文（`skill-conventions.md:197`）是「**`plugins/*/agents/` 下的 agent 不要求 CHANGELOG.md**（不独立版本化，见「Agent 规范」节）」——该豁免已被 spec § 3.1 决策 2 推翻，agent 现在有独立版本号与 CHANGELOG，只是位置在 `agent-docs/` 而非 `agents/`。

⚠️ **注意内层代码块的围栏层级**：CHANGELOG 格式示例本身是一个 ` ```markdown ` 块，写进 `doc-conventions.md` 时它是普通的三反引号块（原文件即如此）。上面用四/五反引号只是为了在本计划里展示，**落地时用三反引号**。

- [ ] **Step 4: 追加 README.md 规范节（含 skill/agent 两栏差异）**

Append to `.claude/rules/doc-conventions.md`：

`````markdown

## README.md 规范

**适用范围**：`plugins/*/skills/` 下新增的 skill（含复合 skill 的子 skill）必须配 README.md；`plugins/*/agents/` 下新增的 agent 同样必须配 README.md 与 CHANGELOG.md，位置在 `plugins/*/agent-docs/<name>/`。`.claude/skills/` 仅供本仓库自用不对外发布，不强制要求。**已有 skill 与已有 agent 均不回填**（agent 当前数为 0，该句为将来预留）。

新增时在对应目录下创建 `README.md`，固定包含以下章节，顺序不可打乱。其中两章 skill 与 agent 写法不同，已在各节标出。

### 标题与元信息

skill：

````markdown
# <skill-name>

> 版本：x.y.z | 分类：<metadata.category 取值>

一句话说明这个 skill 解决什么问题、产出什么。
````

版本号和分类直接抄 SKILL.md 的 `metadata.version` / `metadata.category`，两处必须保持一致。

agent：

````markdown
# <agent-name>

> 版本：x.y.z | 产物类型：agent

一句话说明这个 agent 解决什么问题、产出什么。
````

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
`````

⚠️ **不在本文件内反向声明「skill 见 X、agent 见 Y」**——共用层被两侧引用，反向声明会造成三份文件互相指向，任一改名都要改三处（spec § 4.3）。上文提到 `agent-conventions.md` 的那一处是**具体机制的出处指引**（`agents/` 为何是排他命名空间），不是目录式的反向声明，保留。

- [ ] **Step 5: 验证 glob 不会误伤**

Run:
```bash
python -c "
import pathlib
globs = ['**/CHANGELOG.md', 'plugins/*/skills/**/README.md', 'plugins/*/agent-docs/**/*.md']
root = pathlib.Path('.')
hit = set()
for g in globs:
    for p in root.glob(g):
        if '.git' in p.parts: continue
        hit.add(p.as_posix())
print('命中文件数:', len(hit))
for p in sorted(hit)[:8]: print(' ', p)
print()
print('是否误伤 SKILL.md:', any(p.endswith('SKILL.md') for p in hit))
print('是否误伤 agents/ 下文件:', any('/agents/' in p for p in hit))
"
```

Expected:
- 命中文件数 > 40（全仓 CHANGELOG 数量级）
- `是否误伤 SKILL.md: False`
- `是否误伤 agents/ 下文件: False`（当前 `agents/` 目录尚不存在，必然为 False；该检查是为将来 agent 落地后回归用）

⚠️ 若「误伤 SKILL.md」为 True，说明 glob 写错了（最可能是漏了 `CHANGELOG.md` 的文件名限定）。**必须修正后重跑，不得带着误伤进入下一步**——glob 误伤的后果正是本次拆分要消除的问题。

- [ ] **Step 6: 核对内容完整性**

Run:
```bash
echo "=== 新文件行数 ===" && wc -l .claude/rules/doc-conventions.md
echo "=== 二级标题数 ===" && grep -c '^## ' .claude/rules/doc-conventions.md
echo "=== glob 条数 ===" && grep -c '^  - "' .claude/rules/doc-conventions.md
echo "=== 旧豁免声明残留 ===" && grep -c '不要求 CHANGELOG\|不独立版本化' .claude/rules/doc-conventions.md
```

Expected:
- 行数在 85-115 之间
- 二级标题数 = **4**（编辑铁律、CHANGELOG.md 规范、README.md 规范，加 CHANGELOG 格式示例内的 `## [版本号]` 一行也会被计入）
- glob 条数 = **3**
- 旧豁免声明残留 = **0**（`grep -c` 无命中时退出码非 0 且输出 `0`，属预期）

⚠️ 二级标题计数会因格式示例里的 `## [版本号] - YYYY-MM-DD` 而多 1，这是正常的（现有 `skill-conventions.md` 的 `grep -n '^## '` 输出里也有这一行，见 L179）。**不要为了让数字变成 3 而去改格式示例。**

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin` skill。提交范围：仅 `.claude/rules/doc-conventions.md`。

提交消息建议：
```
docs(rules): 新建 doc-conventions.md 承载 CHANGELOG/README 共用规范
```

⚠️ **本次不升任何版本号**——改动全在 `.claude/` 下（见 Global Constraints）。若 `commit-cc-plugin` 第二步的版本号决策提示要升版本，答「跳过，`.claude/` 下改动不升级」。

---

## Task 2: `skill-conventions.md` 瘦身

**Files:**
- Modify: `.claude/rules/skill-conventions.md`（frontmatter L1-7；删除 L9-11、L77-132、L174-240）

**Interfaces:**
- Consumes: Task 1 产出的 `.claude/rules/doc-conventions.md`（在开头一句引用它）
- Produces: 瘦身后的 `skill-conventions.md`，`paths` 只剩 `**/SKILL.md` 一条。文件名**不改**——全仓 8 处活引用依赖该路径，Task 5 会逐处更新其描述文字但不改路径

**保留原名的依据**（spec § 4.1）：改名需同步 8 处活引用（`AGENTS.md`×3、`catalog.json`×2、`knowledge-base/README.md`×1、`skill-authoring/README.md`×2、`rules/01-skill-format.md`×2）且收益为零，因此只搬走共用部分。

- [ ] **Step 1: 收窄 frontmatter 的 paths 为单条**

Edit `.claude/rules/skill-conventions.md`，把 L1-7：

```yaml
---
paths:
  - "**/SKILL.md"
  - "**/CHANGELOG.md"
  - "plugins/*/skills/**/README.md"
  - "plugins/*/agents/**/*.agent.md"
---
```

改为：

```yaml
---
paths:
  - "**/SKILL.md"
---
```

**这是本次拆分的核心收益落点**：删掉的 `**/CHANGELOG.md` 是那条极宽的 glob——编辑全仓 50+ 个 CHANGELOG 中任意一个都会注入 248 行，其中约 190 行与「写 CHANGELOG」无关。

- [ ] **Step 2: 在文件开头补引用共用层的一句**

在 frontmatter 之后、第一个二级标题之前插入：

```markdown

> 文档类规范（编辑铁律、CHANGELOG.md、README.md）见 `.claude/rules/doc-conventions.md`；agent 规范见 `.claude/rules/agent-conventions.md`。本篇只承载 SKILL.md 自身的约定。
```

⚠️ 措辞对齐现有风格——该文件 L15 已有先例：「**通用规范见 `knowledge-base/skill-authoring/`**……本篇只承载**本仓库专属约定**」。

⚠️ **本句同时指向另两份文件是允许的**，与 spec § 4.3「不在共用层反向声明」不冲突——禁止的是 `doc-conventions.md`（被引用方）指回两个引用方；专属层指向兄弟文件不构成循环。

- [ ] **Step 3: 删除已搬走的四节**

按**从后往前**的顺序删除，避免行号漂移：

| 顺序 | 行范围 | 节名 | 去向 |
|---|---|---|---|
| 1 | L199-240 | `## README.md 规范` 至该节末（"…无需在 README 重复。"） | 已在 Task 1 Step 4 落地 |
| 2 | L174-197 | `## CHANGELOG.md 规范` 至该节末（"…不要求 CHANGELOG.md（不独立版本化，见「Agent 规范」节）"） | 已在 Task 1 Step 3 落地（末条改写） |
| 3 | L77-132 | `## Agent 规范` 至该节末（"…与 skill 同表（见 `AGENTS.md` 版本管理规则）。"） | Task 3 落地（按 spec § 5 重写，非原样搬迁） |
| 4 | L9-11 | `## 编辑铁律：禁止无关格式化` 及其正文段 | 已在 Task 1 Step 2 落地 |

⚠️ **L242 起的「Skill 持续优化的强制约定」节必须保留**——darwin-skill 的 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应维度，该节是 skill 专属（spec § 4.2）。

⚠️ **L134-172 的「执行前置校验」与「需求预告」两节也保留**——它们约束 skill 的执行流程；agent 不执行动作（只读推理），且独立上下文只收一个 prompt，无「逐步追问」问题（spec § 4.2）。

- [ ] **Step 4: 验证删除边界正确**

Run:
```bash
echo "=== 剩余二级标题 ===" && grep -n '^## ' .claude/rules/skill-conventions.md
echo "=== paths 条数（应为 1）===" && grep -c '^  - "' .claude/rules/skill-conventions.md
echo "=== 行数 ===" && wc -l .claude/rules/skill-conventions.md
echo "=== 搬走的内容不应残留 ===" && grep -c '编辑铁律\|## Agent 规范\|## CHANGELOG.md 规范\|## README.md 规范' .claude/rules/skill-conventions.md
echo "=== 保留的内容必须还在 ===" && grep -c 'metadata.version\|执行前置校验\|需求预告\|持续优化' .claude/rules/skill-conventions.md
```

Expected — 剩余二级标题**恰好这 4 个，按此顺序**：

```
## Skill frontmatter 规范
## 执行前置校验
## 需求预告：执行前一次性告知，而非逐步反应式发现
## Skill 持续优化的强制约定
```

- paths 条数 = **1**
- 行数在 **115-125** 之间
- 搬走的内容残留 = **0**
- 保留的内容命中 ≥ **4**

⚠️ 若出现第 5 个二级标题，说明某节没删干净——**按标题名逐一比对上面这 4 行**，多出来的那个就是漏删的。不要靠数量判断。

- [ ] **Step 5: 验证 SKILL.md 编辑时的加载内容正确**

Run:
```bash
python -c "
import pathlib
# 模拟编辑一个 SKILL.md 时会命中哪些规则文件
target = 'plugins/optimus-devops-plugin/skills/sync-skill-symlinks/SKILL.md'
import re, yaml
for rf in sorted(pathlib.Path('.claude/rules').glob('*.md')):
    text = rf.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        print(f'{rf.name}: 无 frontmatter'); continue
    globs = yaml.safe_load(m.group(1)).get('paths', [])
    hit = any(pathlib.PurePosixPath(target).match(g) for g in globs)
    print(f'{rf.name}: {\"命中\" if hit else \"不命中\"}  globs={globs}')
" 2>/dev/null || echo "（无 pyyaml，跳过此步，改用 Step 4 的静态核对）"
```

Expected:
- `skill-conventions.md: 命中`
- `doc-conventions.md: 不命中`

⚠️ **本机可能无 `pyyaml`**（`allowed-tools` 里没声明过该依赖）。命令末尾已加 fallback——若输出 fallback 提示，说明缺该库，**跳过本步即可**，Step 4 的静态核对已覆盖 glob 正确性。不要为此步去安装依赖。

- [ ] **Step 6: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `.claude/rules/skill-conventions.md`。

提交消息建议：
```
docs(rules): skill-conventions 瘦身，paths 收窄为单条 SKILL.md
```

⚠️ 不升版本号（`.claude/` 下改动）。

---

## Task 3: 新建 `agent-conventions.md`

**Files:**
- Create: `.claude/rules/agent-conventions.md`
- Read (不改): `.claude/rules/skill-conventions.md` 的 git 历史（原「Agent 规范」节已在 Task 2 删除，若需查原文用 `git show HEAD~1:.claude/rules/skill-conventions.md`）

**Interfaces:**
- Consumes: Task 1 的 `doc-conventions.md`（开头引用）、Task 2 已完成的删除（避免两处并存）
- Produces: `.claude/rules/agent-conventions.md`，`paths` 为 `plugins/*/agents/**/*.md`。定义 `agent-docs/<name>/` 目录约定与 agent 版本号载体，**Task 6-7 与 dotnet-diagnose 实施都依赖本文件**

⚠️ **这不是原样搬迁**。原「Agent 规范」节有**四处必须改写**（spec § 5.2）与**三节必须新增**（spec § 5.3），下面逐步给出最终内容。

- [ ] **Step 1: 创建 frontmatter 与选型判据节**

Create `.claude/rules/agent-conventions.md`：

````markdown
---
paths:
  - "plugins/*/agents/**/*.md"
---

> 文档类规范（CHANGELOG.md、README.md）见 `.claude/rules/doc-conventions.md`；skill 规范见 `.claude/rules/skill-conventions.md`。本篇只承载 agent 自身的约定。

## 何时建 agent 而非 skill

| 判据 | skill | agent |
|---|---|---|
| 上下文 | 注入当前对话，共享历史 | 独立上下文，只收一个 prompt |
| 适合的任务 | 需与用户往复交互、依赖对话历史 | 单次可闭环的推理/审查任务，且**需要与主对话隔离** |
| 是否执行动作 | 常执行（Bash/Write） | 可只读——需要隔离的往往正是"只推理不动手"的判定类任务 |

不确定时选 skill：skill 是本仓主形态（49 个 skill vs 1 个 agent），且 agent 的独立上下文对需要追问的任务是负担而非优势。
````

⚠️ **`paths` 用 `*.md` 而非 `*.agent.md`**（原 glob 是后者）。理由：若后续有人按 Claude Code 官方示例建纯 `.md` 的 agent，规范仍能自动加载；原 glob 会漏掉这种情形（spec § 4.1）。

- [ ] **Step 2: 追加目录结构硬约束节（新增，spec § 5.3 ①）**

Append：

````markdown

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
````

- [ ] **Step 3: 追加清单声明与命名来源节（改写 spec § 5.2 第 1、4 处）**

Append：

````markdown

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
````

- [ ] **Step 4: 追加 frontmatter 节（改写 spec § 5.2 第 3 处）**

Append：

````markdown

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
````

- [ ] **Step 5: 追加配套文档与版本管理节（改写 spec § 5.2 第 2 处 + 新增 § 5.3 ②③）**

Append：

````markdown

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
````

- [ ] **Step 6: 核对四处改写与三节新增全部落地**

Run:
```bash
echo "=== 二级标题（应为 7 个）===" && grep -n '^## ' .claude/rules/agent-conventions.md
echo ""
echo "=== spec § 5.2 四处改写的关键词都必须命中 ==="
for kw in '显式声明' 'agent-docs' '独立版本化' 'VS Code'; do
  printf '%-16s' "$kw"; grep -c "$kw" .claude/rules/agent-conventions.md
done
echo ""
echo "=== 旧豁免声明必须为 0 ==="
for kw in '不要求 CHANGELOG' '不独立版本化' '自动发现默认目录' '随 .claude-plugin/marketplace.json 统一管理'; do
  printf '%-40s' "$kw"; grep -c "$kw" .claude/rules/agent-conventions.md
done
echo ""
echo "=== 行数 ===" && wc -l .claude/rules/agent-conventions.md
```

Expected — 七个二级标题，按此顺序：

```
## 何时建 agent 而非 skill
## 目录结构（硬约束）
## 目录与命名
## frontmatter
## 配套文档
## 版本管理
## darwin-skill 门禁豁免
```

- 四处改写关键词各 ≥ 1
- 四条旧豁免声明各 = **0**
- 行数在 **95-130** 之间

- [ ] **Step 7: 验证三份文件总行数未丢内容**

Run:
```bash
echo "=== 三份文件行数 ===" && wc -l .claude/rules/*.md
echo ""
echo "=== 拆分前基线 248，现总数应 ≥ 248 ==="
```

Expected: 三份合计 ≥ **248**（差额即 agent 分栏、目录硬约束节、版本管理节等新增内容，预计合计 320-360 行）。

⚠️ 若总数 **< 248**，说明搬迁过程丢了内容。用 `git show HEAD~2:.claude/rules/skill-conventions.md > /tmp/orig.md` 取原文，逐节比对找出丢失部分。

- [ ] **Step 8: 三份文件的 glob 互不重叠验证**

Run:
```bash
python -c "
import pathlib
cases = {
    'plugins/optimus-devops-plugin/skills/x/SKILL.md':        ['skill-conventions'],
    'plugins/optimus-devops-plugin/skills/x/CHANGELOG.md':    ['doc-conventions'],
    'plugins/optimus-devops-plugin/skills/x/README.md':       ['doc-conventions'],
    'plugins/optimus-devops-plugin/agents/y.agent.md':        ['agent-conventions'],
    'plugins/optimus-devops-plugin/agent-docs/y/README.md':   ['doc-conventions'],
    'plugins/optimus-devops-plugin/agent-docs/y/CHANGELOG.md':['doc-conventions'],
}
globs = {
    'skill-conventions': ['**/SKILL.md'],
    'doc-conventions':   ['**/CHANGELOG.md','plugins/*/skills/**/README.md','plugins/*/agent-docs/**/*.md'],
    'agent-conventions': ['plugins/*/agents/**/*.md'],
}
ok = True
for path, expect in cases.items():
    p = pathlib.PurePosixPath(path)
    got = sorted(n for n,gs in globs.items() if any(p.match(g) for g in gs))
    mark = 'OK ' if got == sorted(expect) else 'FAIL'
    if got != sorted(expect): ok = False
    print(f'{mark} {path}')
    print(f'       期望={sorted(expect)} 实际={got}')
print()
print('全部通过' if ok else '有不匹配项，见上面 FAIL 行')
"
```

Expected: 6 行全部 `OK`，末尾输出 `全部通过`。

⚠️ 这一步是**本次拆分的核心验收**——它验证的正是 spec § 1.1 的驱动力（按动作精准加载）。若 `agent-docs/y/CHANGELOG.md` 同时命中 `doc-conventions` 的两条 glob，Python 的 `any()` 只返回一次，不算重叠，属正常。

- [ ] **Step 9: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `.claude/rules/agent-conventions.md`。

提交消息建议：
```
docs(rules): 新建 agent-conventions.md，agent 改为独立版本化并配套文档
```

⚠️ 不升版本号（`.claude/` 下改动）。

---

## Task 4: 单点验证「版本号变小能否触发更新」

**Files:**
- Create: `plugins/optimus-mcp-servers/.claude-plugin/plugin.json`
- Modify: `plugins/optimus-mcp-servers/.codex-plugin/plugin.json`（`version`: `12.1.8` → `1.0.0`）

**Interfaces:**
- Consumes: 无（与 Task 1-3 无依赖，可并行；但**必须在 Task 5 之前完成**）
- Produces: 一个已验证可正常更新的插件，以及一个 **go / no-go 判定**——通过则 Task 5 推广至其余 8 个；不通过则**停下回报**，spec § 7.3 决策需重新评估

**为什么单独一个任务、且必须最先做版本部分**：官方明确「设了 `version` 就 pin 到该字符串，用户只在你 bump 时才收到更新」，但**未说明版本号变小（`12.1.8` → `1.0.0`）是否仍触发更新**。若客户端做的是「新值 > 旧值才更新」而非「新值 ≠ 旧值」，已安装用户会**静默卡在旧版本**——因为是静默的，我们收不到任何报错。不验证就全量重置，失败时 9 个插件的用户全部卡住。

**为什么选 `optimus-mcp-servers` 做试点**：它无 `skills/` 目录（只有 `.mcp.json` 与 `scripts/`），改动面最小、影响最低。

- [ ] **Step 1: 记录改动前的实际状态**

Run:
```bash
echo "=== 当前 codex 侧版本 ===" && cat plugins/optimus-mcp-servers/.codex-plugin/plugin.json
echo ""
echo "=== 该插件是否已安装（Claude 侧）==="
ls ~/.claude/plugins/cache/ 2>/dev/null | head -20 || echo "（无 cache 目录）"
echo ""
echo "=== marketplace 顶层版本（应为 14.0.0，全程不动）==="
python -c "import json;print(json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'))['version'])"
```

Expected:
- codex 侧 `version` 为 `12.1.8`
- marketplace 顶层为 `14.0.0`

⚠️ 把 cache 目录的输出**记下来**——Step 6 要对比。若本机从未安装过本仓插件（cache 里没有 `optimus-*`），Step 6 的更新验证走路径 B。

- [ ] **Step 2: 新建 `.claude-plugin/plugin.json`**

Create `plugins/optimus-mcp-servers/.claude-plugin/plugin.json`：

```json
{
  "name": "optimus-mcp-servers",
  "version": "1.0.0"
}
```

**只写这两个字段**：
- `name` 标识插件
- `version` 承担 Claude 侧版本真源（官方回退链第 1 级）
- **不写 `description`** 等字段——已在 marketplace 条目声明，重复维护会产生第二真源
- **不写 `agents`**——该插件无 agent 目录

- [ ] **Step 3: 同步改 `.codex-plugin/plugin.json`**

Edit `plugins/optimus-mcp-servers/.codex-plugin/plugin.json`，把 `"version": "12.1.8"` 改为 `"version": "1.0.0"`。

⚠️ **只改 `version` 一个字段**，其余（`name` / `description` / `interface` 等）全部不动。

⚠️ 这两份文件是**同一次改动内一起写**，不是「先定一份再抄给另一份」——新版本号由本次改动的性质决定（此处是「设立版本号载体」，值为起始号 `1.0.0`），两份文件同等地是这个决定的记录。

- [ ] **Step 4: 验证 JSON 可解析且两份同值**

Run:
```bash
python -c "
import json
a = json.load(open('plugins/optimus-mcp-servers/.claude-plugin/plugin.json', encoding='utf-8'))
b = json.load(open('plugins/optimus-mcp-servers/.codex-plugin/plugin.json', encoding='utf-8'))
print('claude 侧:', a)
print('codex  侧 version:', b['version'])
print()
assert a['version'] == b['version'] == '1.0.0', f\"版本不一致或不是 1.0.0: {a['version']} vs {b['version']}\"
assert 'description' not in a, 'claude 侧不应写 description'
print('PASS: 两份同值 1.0.0，claude 侧字段最小化')
"
```

Expected: `PASS: 两份同值 1.0.0，claude 侧字段最小化`

- [ ] **Step 5: 验证 `claude plugin validate` 通过**

Run:
```bash
claude plugin validate ./plugins/optimus-mcp-servers
```

Expected: 校验通过，无 error。

⚠️ **若出现「entry's `version` doesn't match the one in `plugin.json`」类警告**，说明 marketplace 该插件条目里有 `version` 字段（实测应该没有）。此时**不要给条目补 version**——正确处置是删掉条目里的 `version`（spec § 7.1：marketplace 插件条目永不填写 `version`）。

- [ ] **Step 6: 🔴 CHECKPOINT — 更新行为验证（go / no-go 判定点）**

这是本任务的**目的**。两条路径，按本机实际情况选：

**路径 A（本机已安装本仓 marketplace）**：

```bash
# 1. 刷新 marketplace 本地副本
claude plugin marketplace update optimus-plugins-official

# 2. 尝试更新该插件
claude plugin update optimus-mcp-servers

# 3. 查看解析到的版本
claude plugin list
```

判定：
- ✅ **通过** — `plugin list` 显示 `optimus-mcp-servers` 版本为 `1.0.0`（或明确显示已更新）
- ❌ **不通过** — 提示 "already up to date" / 版本仍显示 `12.1.8` / 仍显示 commit SHA

**路径 B（本机未安装，或上述命令不可用）**：

无法验证真实更新行为。此时**不得默认通过**：

```bash
claude plugin --help 2>&1 | head -20
```

- 若命令存在但本仓未安装 → 先装上（`claude plugin marketplace add` 指向本仓），再走路径 A
- 若命令不可用 → **停下来向用户回报**，说明无法在本机验证版本号变小的更新行为，请用户决定是（a）在其他已安装环境验证后再继续、（b）接受风险直接推广、还是（c）改用下面的退路

🔴 **不通过时的退路（预先写定，避免临场决策）**：放弃「全部重置 `1.0.0`」，改为**从当前值继续递增**——`optimus-mcp-servers` 写 `12.1.9`（Patch，因本次只是设立载体）。此时须回头修改 spec § 7.3 的决策记录，并把 Task 5 的目标值改为各插件的「当前值 + Patch」。**该改动影响面较大，必须先向用户确认再执行。**

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
plugins/optimus-mcp-servers/.claude-plugin/plugin.json
plugins/optimus-mcp-servers/.codex-plugin/plugin.json
```

提交消息建议：
```
chore(mcp-servers): 新建 .claude-plugin/plugin.json，版本真源下移试点
```

⚠️ **不额外升版本号**——本次改动的内容**就是** `version` 字段本身，按 spec § 7.4 要点 5「只改 `version` 本身不构成再升一次」。若 `commit-cc-plugin` 第二步提示要升 marketplace 顶层，答「不升，顶层仅在增删插件时升（新规则）」。

⚠️ **marketplace 顶层 `version` 保持 `14.0.0`**，本次不动。

---

## Task 5: 推广至其余 8 个插件

**Files:**
- Create: 8 份 `plugins/<name>/.claude-plugin/plugin.json`
- Modify: 8 份 `plugins/<name>/.codex-plugin/plugin.json`（各自 `version` → `1.0.0`）

**Interfaces:**
- Consumes: Task 4 的 go 判定（**未通过不得开始本任务**）
- Produces: 9 个本仓插件全部具备 `.claude-plugin/plugin.json`，两份 `plugin.json` 同值 `1.0.0`。Task 7 的 `commit-cc-plugin` 校验以此为检查对象

**8 个插件与各自当前 codex 版本（实测，本任务全部改为 `1.0.0`）**：

| 插件 | 当前 codex `version` | 有 `agents/` 目录 |
|---|---|---|
| `optimus-backend-plugin` | `12.1.9` | 否 |
| `optimus-decision-plugin` | `12.3.1` | 否 |
| `optimus-devops-plugin` | `14.0.0` | 否（agent 由 dotnet-diagnose 计划创建） |
| `optimus-frontend-plugin` | `12.1.9` | 否 |
| `optimus-media-plugin` | `13.1.2` | 否 |
| `optimus-office-plugin` | `12.1.8` | 否 |
| `optimus-prd-plugin` | `12.1.8` | 否 |
| `optimus-qa-plugin` | `12.1.8` | 否 |

⚠️ **9 个插件当前都没有 `agents/` 目录**，因此本任务新建的 9 份 `plugin.json` **都不写 `agents` 字段**。devops 的 `agents` 声明由 `dotnet-diagnose` 计划在创建 agent 时补上（那是它的 § 8.1 交付项）。

⚠️ **`cangjie-skill` 不在此列**——它是 marketplace 的第 10 个条目，外部 git url 源（`source.source: "url"`，`sha` 固定为 `b633a4f`），不在 `plugins/` 目录下。它的版本按官方回退链落到 commit SHA，已精确且无需维护。**全程不得改动它。**

- [ ] **Step 1: 批量创建 8 份 `.claude-plugin/plugin.json`**

Run:
```bash
python -c "
import json, pathlib

plugins = [
    'optimus-backend-plugin',
    'optimus-decision-plugin',
    'optimus-devops-plugin',
    'optimus-frontend-plugin',
    'optimus-media-plugin',
    'optimus-office-plugin',
    'optimus-prd-plugin',
    'optimus-qa-plugin',
]

for name in plugins:
    d = pathlib.Path('plugins') / name / '.claude-plugin'
    d.mkdir(exist_ok=True)
    f = d / 'plugin.json'
    if f.exists():
        print(f'跳过（已存在）: {f}')
        continue
    f.write_text(json.dumps({'name': name, 'version': '1.0.0'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'创建: {f}')
"
```

Expected: 8 行 `创建: plugins/<name>/.claude-plugin/plugin.json`，无「跳过」。

⚠️ 脚本对已存在的文件**跳过而非覆盖**——若出现「跳过」，说明该插件已有该文件（可能是 Task 4 试点或手工创建），先查清再决定。

⚠️ 生成的 JSON 用 `indent=2` 且**末尾带换行**，与 `.codex-plugin/plugin.json` 的现有风格一致。

- [ ] **Step 2: 批量改 8 份 `.codex-plugin/plugin.json` 的 version**

Run:
```bash
python -c "
import json, pathlib, re

plugins = [
    'optimus-backend-plugin',
    'optimus-decision-plugin',
    'optimus-devops-plugin',
    'optimus-frontend-plugin',
    'optimus-media-plugin',
    'optimus-office-plugin',
    'optimus-prd-plugin',
    'optimus-qa-plugin',
]

for name in plugins:
    f = pathlib.Path('plugins') / name / '.codex-plugin' / 'plugin.json'
    text = f.read_text(encoding='utf-8')
    old = json.loads(text)['version']
    # 只替换 version 一行，保留原文件的全部格式与字段顺序
    new_text, n = re.subn(r'(\"version\"\s*:\s*\")[^\"]+(\")', r'\g<1>1.0.0\g<2>', text, count=1)
    assert n == 1, f'{f}: version 字段替换次数异常 = {n}'
    f.write_text(new_text, encoding='utf-8')
    print(f'{name}: {old} -> 1.0.0')
"
```

Expected: 8 行 `<name>: <旧值> -> 1.0.0`，旧值与本任务开头表格一致。

⚠️ **用正则逐行替换而非 `json.dump` 重写整个文件**——后者会丢掉原文件的字段顺序、缩进风格和任何非标准格式，产生大量无关 diff，违反 Global Constraints 的「禁止无关格式化」。

- [ ] **Step 3: 全量核对 9 个插件的两份 plugin.json**

Run:
```bash
python -c "
import json, pathlib

expected = [
    'optimus-backend-plugin', 'optimus-decision-plugin', 'optimus-devops-plugin',
    'optimus-frontend-plugin', 'optimus-mcp-servers', 'optimus-media-plugin',
    'optimus-office-plugin', 'optimus-prd-plugin', 'optimus-qa-plugin',
]

fail = []
for name in expected:
    base = pathlib.Path('plugins') / name
    ca, co = base / '.claude-plugin/plugin.json', base / '.codex-plugin/plugin.json'
    if not ca.exists(): fail.append(f'{name}: 缺 .claude-plugin/plugin.json'); continue
    if not co.exists(): fail.append(f'{name}: 缺 .codex-plugin/plugin.json'); continue
    a, b = json.load(open(ca, encoding='utf-8')), json.load(open(co, encoding='utf-8'))
    va, vb = a.get('version'), b.get('version')
    status = 'OK ' if va == vb == '1.0.0' else 'FAIL'
    if status == 'FAIL': fail.append(f'{name}: claude={va} codex={vb}')
    extra = set(a) - {'name', 'version', 'agents'}
    if extra: fail.append(f'{name}: claude 侧有多余字段 {extra}')
    print(f'{status} {name:28} claude={va} codex={vb} agents={\"有\" if \"agents\" in a else \"无\"}')

print()
if fail:
    print('FAIL 项:'); [print(' ', x) for x in fail]
else:
    print('全部 9 个插件通过：两份 plugin.json 同值 1.0.0，claude 侧字段最小化')
"
```

Expected: 9 行全 `OK`，末尾 `全部 9 个插件通过…`。

- [ ] **Step 4: 确认 marketplace 未被波及**

Run:
```bash
python -c "
import json
d = json.load(open('.claude-plugin/marketplace.json', encoding='utf-8'))
print('顶层 version:', d['version'])
assert d['version'] == '14.0.0', '顶层 version 被改动了！应保持 14.0.0'

with_ver = [p['name'] for p in d['plugins'] if 'version' in p]
print('条目内有 version 的插件:', with_ver or '（无，正确）')
assert not with_ver, f'插件条目不应有 version: {with_ver}'

cangjie = [p for p in d['plugins'] if p['name'] == 'cangjie-skill'][0]
print('cangjie-skill sha:', cangjie['source']['sha'])
assert cangjie['source']['sha'] == 'b633a4fad5a02f0fc6b2524d1ddf3ed50c753a40', 'cangjie-skill 被改动了！'
print()
print('PASS: marketplace 顶层 14.0.0 未动、条目无 version、cangjie-skill 未动')
"
```

Expected: `PASS: marketplace 顶层 14.0.0 未动、条目无 version、cangjie-skill 未动`

- [ ] **Step 5: 逐插件跑 `claude plugin validate`**

Run:
```bash
for p in plugins/*/; do
  n=$(basename "$p")
  echo "=== $n ==="
  claude plugin validate "./$p" 2>&1 | tail -5
done
```

Expected: 9 个插件全部校验通过，无 error。

⚠️ 若某插件报错，**不要跳过继续**——先修那一个。最可能的两类错误：JSON 语法（Step 1/2 的脚本产物）、或 marketplace 条目与 `plugin.json` 的 `version` 不一致（Step 4 已排除）。

- [ ] **Step 6: 看 diff 确认无无关格式化**

Run:
```bash
git diff --stat
echo "=== 逐文件看 codex 侧 diff（应只有 version 一行）==="
git diff -- 'plugins/*/.codex-plugin/plugin.json' | grep -E '^[+-]' | grep -v '^[+-][+-]'
```

Expected: `.codex-plugin/plugin.json` 的 diff **只有 8 对 `-"version": "..."` / `+"version": "1.0.0"`**，无其他增删行。

⚠️ 若出现大片格式变化（缩进、引号、字段顺序），说明 Step 2 的正则替换失效而走了 `json.dump` 路径——`git checkout -- plugins/*/.codex-plugin/plugin.json` 撤销后重做。

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围（16 个文件）：
```bash
plugins/optimus-backend-plugin/.claude-plugin/plugin.json
plugins/optimus-backend-plugin/.codex-plugin/plugin.json
plugins/optimus-decision-plugin/.claude-plugin/plugin.json
plugins/optimus-decision-plugin/.codex-plugin/plugin.json
plugins/optimus-devops-plugin/.claude-plugin/plugin.json
plugins/optimus-devops-plugin/.codex-plugin/plugin.json
plugins/optimus-frontend-plugin/.claude-plugin/plugin.json
plugins/optimus-frontend-plugin/.codex-plugin/plugin.json
plugins/optimus-media-plugin/.claude-plugin/plugin.json
plugins/optimus-media-plugin/.codex-plugin/plugin.json
plugins/optimus-office-plugin/.claude-plugin/plugin.json
plugins/optimus-office-plugin/.codex-plugin/plugin.json
plugins/optimus-prd-plugin/.claude-plugin/plugin.json
plugins/optimus-prd-plugin/.codex-plugin/plugin.json
plugins/optimus-qa-plugin/.claude-plugin/plugin.json
plugins/optimus-qa-plugin/.codex-plugin/plugin.json
```

提交消息建议：
```
chore(plugins): 版本真源下移至每插件 plugin.json，8 个插件重置为 1.0.0
```

⚠️ **不额外升版本号**（改动内容即 `version` 本身）；**marketplace 顶层保持 `14.0.0`**。

---

## Task 6: 重写 `AGENTS.md` 的四处

**Files:**
- Modify: `AGENTS.md`（L28 产物形态段、L57-70 版本管理节**整节**、L76 规范指向段、L106-115 关键文件表）

**Interfaces:**
- Consumes: Task 1-3 产出的三份规则文件（L76 与 L106 表要指向它们）、Task 5 落地的每插件 `plugin.json`（版本管理节的新规则以它为落点）
- Produces: 与新机制一致的 `AGENTS.md`。它是两个 harness 的入口文档，**Task 7 的 `commit-cc-plugin` 改写以本任务的版本管理节为依据**

⚠️ **四处改动性质不同**：L28 与 L76 是**局部改写**，L106 表是**增行 + 改两行**，版本管理节是**整节重写**（现文三段全部失效）。

- [ ] **Step 1: 改 L28 的产物形态段**

Edit `AGENTS.md`，把这一整段：

```markdown
**第三种产物形态：agent**（`plugins/*/agents/<name>.agent.md`）。与 skill 的区别是上下文隔离——skill 注入当前对话，agent 独立上下文只收一个 prompt，适合单次可闭环、且需与主对话隔离的判定类任务。两个 harness 均自动发现该目录，无需在清单文件声明；Claude 侧按 `plugin-name:agent-name` @-mention 调用，Codex 侧同名触发。选型判据、frontmatter 字段（四字段，与 skill 六字段不同体系）、以及不适用于 agent 的 skill 规范（CHANGELOG / README / darwin-skill 门禁）见 `.claude/rules/skill-conventions.md` 的「Agent 规范」节。
```

改为：

```markdown
**第三种产物形态：agent**（`plugins/*/agents/<name>.agent.md`）。与 skill 的区别是上下文隔离——skill 注入当前对话，agent 独立上下文只收一个 prompt，适合单次可闭环、且需与主对话隔离的判定类任务。**必须在每插件 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**（该字段是 replaces 语义，声明后默认目录扫描被取代，杜绝把配套文档误加载成假 agent）；Claude 侧按 `plugin-name:agent-name` @-mention 调用，Codex 侧同名触发。agent 的配套文档放 `plugins/*/agent-docs/<name>/`（**不放 `agents/`**）、独立版本化、以及 darwin-skill 门禁豁免等细则，见 `.claude/rules/agent-conventions.md`。
```

**三处实质变化**：① 删去「两个 harness 均自动发现该目录，无需在清单文件声明」（已被推翻——自动发现存在，但显式声明才是官方实践且是防假 agent 的机制）；② 删去「不适用于 agent 的 skill 规范（CHANGELOG / README / …）」（CHANGELOG/README 现在**要求**，只是位置不同）；③ 指向从 `skill-conventions.md` 的「Agent 规范」节改为独立的 `agent-conventions.md`。

- [ ] **Step 2: 整节重写版本管理节（L57-70）**

Edit `AGENTS.md`，把从 `## 版本管理规则` 到该节末（现 L70 「…agent 改动改为按其 spec 的验收清单人工核验。」）**整段替换**为：

`````markdown
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
| `plugins/*/agents/<name>.agent.md` | ✅ | — | ✅ | ❌ |
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
`````

- [ ] **Step 3: 改 L76 的规范指向段**

Edit `AGENTS.md`，把：

```markdown
## Skill frontmatter 规范

Skill frontmatter / CHANGELOG 规范见 `.claude/rules/skill-conventions.md`（编辑 SKILL.md / CHANGELOG.md 或 `plugins/*/skills/` 下的 README.md 时自动加载）。该规范同时约束两个 harness——frontmatter 字段是 Codex 也会原样读取缓存的内容，不存在"仅 Claude 遵守"的特例。
```

改为：

```markdown
## 产物规范（三份规则文件，按编辑路径自动加载）

| 规则文件 | 承载什么 | 编辑什么时自动加载 |
|---|---|---|
| `.claude/rules/skill-conventions.md` | SKILL.md 的六字段 frontmatter、执行前置校验、需求预告、持续优化约定 | `**/SKILL.md` |
| `.claude/rules/doc-conventions.md` | 编辑铁律、CHANGELOG.md 格式、README.md 六章节（含 skill/agent 两栏差异） | `**/CHANGELOG.md`、`plugins/*/skills/**/README.md`、`plugins/*/agent-docs/**/*.md` |
| `.claude/rules/agent-conventions.md` | agent 选型判据、`agents/` 目录硬约束、四字段 frontmatter、配套文档与独立版本化 | `plugins/*/agents/**/*.md` |

三份规范**同时约束两个 harness**——frontmatter 字段是 Codex 也会原样读取缓存的内容，不存在"仅 Claude 遵守"的特例。
```

**为什么拆成表格**：三份文件各有独立触发路径，用表格能一眼看出「改什么会加载什么」，这正是本次拆分的目的。

- [ ] **Step 4: 改 L106-115 的关键文件表**

Edit `AGENTS.md` 的关键文件表，改为：

```markdown
| 文件 | 用途 | harness |
|---|---|---|
| `.claude-plugin/marketplace.json` | 插件清单与展示元数据；顶层 `version` 仅记录集合构成，**不是插件版本来源** | 两者共用 |
| `plugins/*/.claude-plugin/plugin.json` | **每插件版本真源**（与 `.codex-plugin/plugin.json` 同步同值）+ `agents` 声明 | Claude 侧读，两者共同维护 |
| `.agents/plugins/marketplace.json` | Codex plugin marketplace 安装入口 | Codex 专属 |
| `plugins/*/.codex-plugin/plugin.json` | 每插件的 Codex 标识清单 + 版本号（与 `.claude-plugin/plugin.json` 同步同值） | Codex 侧读，两者共同维护 |
| `.claude/rules/skill-conventions.md` | SKILL.md frontmatter 规范（按路径自动加载） | 两者共用 |
| `.claude/rules/doc-conventions.md` | CHANGELOG / README 规范（按路径自动加载） | 两者共用 |
| `.claude/rules/agent-conventions.md` | agent 规范（按路径自动加载） | 两者共用 |
```

**四处变化**：① marketplace 那行的用途从「插件仓库元数据和版本号真源」改为不再声称是版本真源；② 新增 `plugins/*/.claude-plugin/plugin.json` 一行；③ `.codex-plugin` 那行补上版本号职责与同步要求；④ 新增两份规则文件。

- [ ] **Step 5: 核对四处改动落地且旧表述清除**

Run:
```bash
echo "=== 旧表述必须全部为 0 ==="
for kw in '两个 harness 均自动发现该目录' '两个 harness 共用的版本号真源' '从 .claude-plugin/marketplace.json 抄录' '不适用于 agent 的 skill 规范' '插件仓库元数据和版本号真源'; do
  printf '%-44s' "$kw"; grep -c "$kw" AGENTS.md
done
echo ""
echo "=== 新表述必须都命中 ==="
for kw in 'agent-conventions.md' 'doc-conventions.md' '触发矩阵' '同一次改动内一起升' '无对应场景' 'cangjie-skill'; do
  printf '%-30s' "$kw"; grep -c "$kw" AGENTS.md
done
echo ""
echo "=== 版本管理节的子节（应为 4 个三级标题）==="
sed -n '/^## 版本管理规则/,/^## /p' AGENTS.md | grep '^### '
```

Expected:
- 5 条旧表述各 = **0**
- 6 条新表述各 ≥ **1**
- 版本管理节下有 4 个三级标题：`### 版本号分两类`、`### 触发矩阵：什么改动升哪一层`、`### 升级幅度`、`### darwin-skill 评分门禁`

- [ ] **Step 6: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `AGENTS.md`。

提交消息建议：
```
docs(agents): 版本管理节整节重写，落点下移至每插件 plugin.json
```

⚠️ **不升版本号**——`AGENTS.md` 在触发矩阵最后一行，明确不升任何版本号。

---

## Task 7: `commit-cc-plugin` 改写版本决策 + 新增同值校验

**Files:**
- Create: `.claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py`
- Create: `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py`
- Modify: `.claude/skills/commit-cc-plugin/SKILL.md`（第二步「版本号决策」整节 L43-57、第三步暂存示例、常见错误表、frontmatter 的 `metadata.version`）
- Modify: `.claude/skills/commit-cc-plugin/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 6 的 `AGENTS.md` 版本管理节（本任务的规则表以它为唯一依据，不重复定义）、Task 5 落地的 9 个插件两份 `plugin.json`（校验对象）
- Produces:
  - `check_plugin_versions.py` 暴露 `check_all(repo_root: pathlib.Path) -> list[str]` — 返回问题描述列表，空列表表示通过
  - `SKILL.md` 第二步新增一个校验环节，调用该脚本，非空则阻断提交

**为什么需要这道自动化**（spec § 7.6.1）：原机制的抄录源是**唯一的**（marketplace 顶层一个值），改任何插件都写同一个数——漏改容易被发现，因为 9 个插件的号本该趋同。下移后每个插件有自己的号，**失去了单一参照物**：某插件 codex 侧停在 `1.0.1` 而 claude 侧已是 `1.0.2`，肉眼扫过去毫无异常，且两个 harness 的用户会看到不同版本号而**无任何报错**。

- [ ] **Step 1: 写失败的测试**

Create `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py`：

```python
import json
import pathlib
import shutil
import tempfile
import unittest

from check_plugin_versions import check_all


def make_plugin(root, name, claude_ver, codex_ver, claude_extra=None):
    """在临时仓库里造一个插件。ver 传 None 表示不建该文件。"""
    base = root / "plugins" / name
    if claude_ver is not None:
        d = base / ".claude-plugin"
        d.mkdir(parents=True, exist_ok=True)
        body = {"name": name, "version": claude_ver}
        if claude_extra:
            body.update(claude_extra)
        (d / "plugin.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if codex_ver is not None:
        d = base / ".codex-plugin"
        d.mkdir(parents=True, exist_ok=True)
        (d / "plugin.json").write_text(
            json.dumps({"name": name, "version": codex_ver}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    base.mkdir(parents=True, exist_ok=True)
    return base


class TestCheckPluginVersions(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        (self.root / "plugins").mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_two_files_same_version_passes(self):
        make_plugin(self.root, "p-ok", "1.2.3", "1.2.3")
        self.assertEqual(check_all(self.root), [])

    def test_version_mismatch_is_reported_with_both_values(self):
        make_plugin(self.root, "p-bad", "1.0.2", "1.0.1")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("p-bad", problems[0])
        self.assertIn("1.0.2", problems[0])
        self.assertIn("1.0.1", problems[0])

    def test_error_message_does_not_name_an_authoritative_side(self):
        """报错措辞不得写「以某一份为准」——正确动作是回头判断本次改动该升什么号。"""
        make_plugin(self.root, "p-bad", "2.0.0", "1.0.0")
        msg = check_all(self.root)[0]
        for forbidden in ("以 .claude-plugin 为准", "以 .codex-plugin 为准", "为准"):
            self.assertNotIn(forbidden, msg)
        self.assertIn("本次改动", msg)

    def test_missing_claude_plugin_json_is_reported(self):
        make_plugin(self.root, "p-no-claude", None, "1.0.0")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".claude-plugin/plugin.json", problems[0])

    def test_missing_codex_plugin_json_is_reported(self):
        make_plugin(self.root, "p-no-codex", "1.0.0", None)
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".codex-plugin/plugin.json", problems[0])

    def test_missing_version_field_is_reported(self):
        base = self.root / "plugins" / "p-no-ver" / ".claude-plugin"
        base.mkdir(parents=True)
        (base / "plugin.json").write_text('{"name": "p-no-ver"}\n', encoding="utf-8")
        codex = self.root / "plugins" / "p-no-ver" / ".codex-plugin"
        codex.mkdir(parents=True)
        (codex / "plugin.json").write_text(
            '{"name": "p-no-ver", "version": "1.0.0"}\n', encoding="utf-8")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_invalid_json_is_reported_not_raised(self):
        base = self.root / "plugins" / "p-broken" / ".claude-plugin"
        base.mkdir(parents=True)
        (base / "plugin.json").write_text("{not json", encoding="utf-8")
        codex = self.root / "plugins" / "p-broken" / ".codex-plugin"
        codex.mkdir(parents=True)
        (codex / "plugin.json").write_text(
            '{"name": "p-broken", "version": "1.0.0"}\n', encoding="utf-8")
        problems = check_all(self.root)   # 不得抛异常
        self.assertEqual(len(problems), 1)
        self.assertIn("无法解析", problems[0])

    def test_multiple_plugins_all_reported(self):
        make_plugin(self.root, "p-ok", "1.0.0", "1.0.0")
        make_plugin(self.root, "p-bad1", "1.0.0", "2.0.0")
        make_plugin(self.root, "p-bad2", "3.0.0", "4.0.0")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 2)

    def test_claude_side_extra_fields_are_reported(self):
        """.claude-plugin/plugin.json 只应有 name / version / agents。"""
        make_plugin(self.root, "p-extra", "1.0.0", "1.0.0",
                    claude_extra={"description": "不该写在这里"})
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("description", problems[0])

    def test_agents_field_is_allowed(self):
        make_plugin(self.root, "p-agents", "1.0.0", "1.0.0",
                    claude_extra={"agents": ["./agents/x.agent.md"]})
        self.assertEqual(check_all(self.root), [])

    def test_directory_without_any_plugin_json_is_skipped(self):
        """plugins/ 下可能有非插件目录（如临时文件夹），不报错。"""
        (self.root / "plugins" / "not-a-plugin").mkdir()
        self.assertEqual(check_all(self.root), [])


if __name__ == "__main__":
    unittest.main()
```

⚠️ **`test_error_message_does_not_name_an_authoritative_side` 是本组测试的关键一条**。它把 spec § 7.6.1 的「⚠️ 提示措辞的硬要求」变成断言——报错不得写「以某一份为准」，因为若错的恰好是那一份（该升 Minor 却升了 Patch），照该提示修会把正确的一边也改错。**规则对了但错误提示写错，实际执行时仍会走偏。**

- [ ] **Step 2: 运行测试确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/commit-cc-plugin/scripts -p "test_*.py" -v
```

Expected: FAIL，报 `ModuleNotFoundError: No module named 'check_plugin_versions'`（11 个测试全部 error）。

- [ ] **Step 3: 写最小实现**

Create `.claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py`：

```python
#!/usr/bin/env python3
"""校验每插件两份 plugin.json 的 version 是否同值。

版本真源是「两份 plugin.json 构成的一对」——改动插件内容后，两份在同一次改动内
一起升到同一个新值。不存在抄录关系与主从关系：新版本号由本次改动的性质决定
（见 AGENTS.md 版本管理规则的触发矩阵与幅度表），两份文件同等地是这个决定的记录。

因此发现不一致时，正确处置是回头判断本次改动该升什么号，然后把两份都写成那个号，
而不是拿一边覆盖另一边——那样有 50% 概率把正确的一边改错。
"""
import json
import pathlib
import sys

CLAUDE_ALLOWED_KEYS = {"name", "version", "agents"}


def _load(path):
    """返回 (data, err)。err 非 None 时 data 为 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"无法解析 JSON：{e}"
    except OSError as e:
        return None, f"无法读取：{e}"


def check_plugin(plugin_dir):
    """校验单个插件目录，返回问题描述列表。"""
    name = plugin_dir.name
    claude_f = plugin_dir / ".claude-plugin" / "plugin.json"
    codex_f = plugin_dir / ".codex-plugin" / "plugin.json"

    # 两份都没有 → 不是本仓插件目录（如临时文件夹），跳过
    if not claude_f.exists() and not codex_f.exists():
        return []

    problems = []

    if not claude_f.exists():
        problems.append(
            f"[{name}] 缺 .claude-plugin/plugin.json"
            f"——Claude 侧会落到 git commit SHA 而非语义化版本")
        return problems
    if not codex_f.exists():
        problems.append(
            f"[{name}] 缺 .codex-plugin/plugin.json"
            f"——Codex 侧读不到该插件的版本号")
        return problems

    claude, err = _load(claude_f)
    if err:
        return [f"[{name}] .claude-plugin/plugin.json {err}"]
    codex, err = _load(codex_f)
    if err:
        return [f"[{name}] .codex-plugin/plugin.json {err}"]

    va, vb = claude.get("version"), codex.get("version")
    if va is None:
        problems.append(f"[{name}] .claude-plugin/plugin.json 缺 version 字段")
    if vb is None:
        problems.append(f"[{name}] .codex-plugin/plugin.json 缺 version 字段")

    if va is not None and vb is not None and va != vb:
        problems.append(
            f"[{name}] 两份 plugin.json 版本不一致："
            f".claude-plugin = {va}，.codex-plugin = {vb}。"
            f"请按本次改动的性质（见 AGENTS.md 版本管理规则的幅度表）确定应升到的版本号，"
            f"并把两份都改成该值")

    extra = set(claude) - CLAUDE_ALLOWED_KEYS
    if extra:
        problems.append(
            f"[{name}] .claude-plugin/plugin.json 有多余字段 {sorted(extra)}"
            f"——只应写 name / version / agents，其余元数据在 marketplace.json 声明，"
            f"重复维护会产生第二真源")

    return problems


def check_all(repo_root):
    """遍历 plugins/ 下所有目录，返回全部问题描述列表。"""
    repo_root = pathlib.Path(repo_root)
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.is_dir():
        return [f"plugins/ 目录不存在：{plugins_dir}"]

    problems = []
    for d in sorted(plugins_dir.iterdir()):
        if d.is_dir():
            problems.extend(check_plugin(d))
    return problems


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("插件版本号校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("插件版本号校验通过：所有插件的两份 plugin.json 同值")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

⚠️ **`_load` 捕获异常返回 err 而非抛出**——校验脚本在提交前跑，抛异常会让整个提交流程崩掉而看不出原因。返回可读的问题描述让阻断信息保持有用。

⚠️ **「两份都没有」跳过而非报错**——`plugins/` 下可能出现非插件目录，报错会让校验对无关目录误伤。

- [ ] **Step 4: 运行测试确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/commit-cc-plugin/scripts -p "test_*.py" -v
```

Expected: `Ran 11 tests` / `OK`

- [ ] **Step 5: 在真实仓库上跑一次**

Run:
```bash
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
```

Expected: `插件版本号校验通过：所有插件的两份 plugin.json 同值`

⚠️ 若报「缺 .claude-plugin/plugin.json」，说明 Task 5 未完成或有插件漏建——回 Task 5 补齐再继续。

- [ ] **Step 6: 用故意不一致的用例验证真的会阻断**

这一步**不可省略**——只加校验代码不验证它会拦住问题，等于没加。

Run:
```bash
# 故意把一个插件的 codex 侧改成不同版本
python -c "
import pathlib, re
f = pathlib.Path('plugins/optimus-qa-plugin/.codex-plugin/plugin.json')
t = f.read_text(encoding='utf-8')
f.write_text(re.sub(r'(\"version\"\s*:\s*\")[^\"]+(\")', r'\g<1>9.9.9\g<2>', t, count=1), encoding='utf-8')
print('已故意改为 9.9.9')
"

# 跑校验，应阻断
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
echo "退出码: $?"

# 恢复
git checkout -- plugins/optimus-qa-plugin/.codex-plugin/plugin.json
echo "=== 恢复后再跑 ==="
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
echo "退出码: $?"
```

Expected:
1. 第一次跑：输出 `插件版本号校验未通过`，含 `[optimus-qa-plugin]`、`.claude-plugin = 1.0.0`、`.codex-plugin = 9.9.9`，**退出码 1**
2. 报错文字里**不含**「为准」二字
3. 恢复后：`校验通过`，**退出码 0**

⚠️ 务必确认第 3 步恢复成功（`git status` 应为 clean 或只有本任务的新文件），不要把 `9.9.9` 留在工作树里。

- [ ] **Step 7: 改写 SKILL.md 第二步**

Edit `.claude/skills/commit-cc-plugin/SKILL.md`，把第二步整节（L43-57，从 `## 第二步 — 版本号决策` 到 `如需升级，编辑 .claude-plugin/marketplace.json 的 "version" 字段，随本次一并暂存。`）替换为：

`````markdown
## 第二步 — 版本号决策

插件版本号规则的**唯一依据是 `AGENTS.md` 的「版本管理规则」节**（触发矩阵 + 幅度表），本步骤不重复定义，只给执行动作。Git tag 与发布流程遵循 [`knowledge-base/git/rules/04-versioning-release.md`](../../../knowledge-base/git/rules/04-versioning-release.md)。

**第 1 步 — 判断本次改动落在哪里：**

- **`.claude/`、`docs/`、`knowledge-base/`、`AGENTS.md`、`CLAUDE.md`** → 跳过，不升任何版本号
- **`plugins/<plugin>/` 下的内容** → 升该插件的**两份** `plugin.json`（见下）
- **新增或删除整个插件** → 除插件自身版本外，另升 `.claude-plugin/marketplace.json` 的**顶层** `version`
- **只改了 `plugin.json` 的 `version` 字段本身** → 不再额外升（否则递归）
- **改了 marketplace 的插件 `description` 等展示元数据** → 不升任何版本号

**第 2 步 — 若需升插件版本，两份文件同步改：**

```
plugins/<plugin>/.claude-plugin/plugin.json    ← version 升到新值
plugins/<plugin>/.codex-plugin/plugin.json     ← version 升到同一个新值
```

⚠️ **两份是同一次改动内一起改，没有先后主从**。新版本号由本次改动的性质决定（`AGENTS.md` 幅度表），两份文件同等地是这个决定的记录——不是一方抄另一方。

⚠️ **`marketplace.json` 的插件条目内永不填写 `version`**——它会被 `plugin.json` 静默覆盖，且本仓条目 `source` 为本地路径时官方还会报不一致警告。

⚠️ **`cangjie-skill` 不参与本机制**——它是外部 git url 源，版本由上游 commit SHA 决定。

**第 3 步 — 校验两份同值（阻断式）：**

```bash
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
```

🔴 **CHECKPOINT — 退出码非 0 则禁止继续提交**。按报错提示回头判断本次改动该升什么号，把两份都改成该值后重跑，直到通过。

**不要**因为报错提到某一份文件就直接拿另一份覆盖它——错的可能恰好是"另一份"（该升 Minor 却升了 Patch），覆盖会把正确的一边也改错。
`````

⚠️ **删掉了原节的四行升级幅度表**——它与 `AGENTS.md` 的表重复，且原表比 `AGENTS.md` 多两行（`mcp/lsp`、「删除内部实现 → Patch」）。**两处表述不一致本身就是隐患**，本次统一到 `AGENTS.md` 为唯一依据。

- [ ] **Step 8: 更新第三步的暂存示例**

Edit `.claude/skills/commit-cc-plugin/SKILL.md` 的第三步，把示例中的：

```bash
git add .claude-plugin/marketplace.json
git add plugins/<插件名>/skills/<skill名>/SKILL.md
```

改为：

```bash
git add plugins/<插件名>/.claude-plugin/plugin.json
git add plugins/<插件名>/.codex-plugin/plugin.json
git add plugins/<插件名>/skills/<skill名>/SKILL.md
```

**为什么要改这个示例**：原示例第一行暗示「升版本就是改 marketplace」，与新机制矛盾。示例是执行者最容易照抄的部分，留着旧路径会让新规则失效。

- [ ] **Step 9: 更新常见错误表**

Edit `.claude/skills/commit-cc-plugin/SKILL.md` 的「常见错误」节，把这两行：

```markdown
| `.claude/` 下改动也升级版本 | 仅 `plugins/` 下变更才判断版本；Git 版本与发布规则见 `knowledge-base/git/rules/04-versioning-release.md` |
| 新增 skill 忘记升级版本 | 新增内容 → Minor |
```

改为：

```markdown
| `.claude/` 下改动也升级版本 | 仅 `plugins/` 下变更才判断版本；规则见 `AGENTS.md` 版本管理规则 |
| 新增 skill 忘记升级版本 | 新增内容 → 插件两份 `plugin.json` 升 Minor，且新 skill 的 `metadata.version` 起 `1.0.0` |
| 只升了一份 `plugin.json` | 两份必须同值——第二步的校验脚本会阻断 |
| 改插件内容却升了 marketplace 顶层 | 顶层仅在增删插件时升；改插件内部内容只升该插件的 `plugin.json` |
```

- [ ] **Step 10: 升 `commit-cc-plugin` 自身版本并写 CHANGELOG**

Edit `.claude/skills/commit-cc-plugin/SKILL.md` 的 frontmatter，`metadata.version` 从 `"3.5.0"` 改为 `"3.6.0"`（**Minor** — 新增了校验环节这个功能）。

Edit `.claude/skills/commit-cc-plugin/CHANGELOG.md`，在最上方插入：

```markdown
## [3.6.0] - 2026-09-06

### Added
- 第二步新增阻断式校验：`scripts/check_plugin_versions.py` 比对每插件两份 `plugin.json` 的 `version`，不一致则禁止提交（配 11 个 unittest 用例，含「报错措辞不得写以某一份为准」一条）

### Changed
- 第二步「版本号决策」整节重写：版本落点从 `.claude-plugin/marketplace.json` 顶层下移至每插件的两份 `plugin.json`；升级幅度表删除，统一以 `AGENTS.md` 版本管理规则为唯一依据（原表与 AGENTS.md 有两行差异）
- 第三步暂存示例改为两份 `plugin.json`，不再示范 `git add .claude-plugin/marketplace.json`
- 常见错误表增两行：只升一份 `plugin.json`、改插件内容却升 marketplace 顶层
```

⚠️ **`.claude/` 下的 skill 有自己的 `metadata.version`，但不牵动任何插件版本号**——它不随插件分发。这与「`.claude/` 下改动不升版本号」不矛盾：后者说的是**插件版本号**，skill 自身的描述性版本号照常维护。

- [ ] **Step 11: 回归全部测试**

Run:
```bash
echo "=== 新增脚本的测试 ==="
python -m unittest discover -s .claude/skills/commit-cc-plugin/scripts -p "test_*.py"
echo ""
echo "=== 既有维护型 skill 的测试（确认未被波及）==="
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py" 2>&1 | tail -3
```

Expected:
- 新增脚本：`Ran 11 tests` / `OK`
- `knowledge-base-maintain`：`Ran 139 tests` / `OK`
- `sync-cc-tips`：`Ran 46 tests` / `OK`
- `sync-cc-docs-to-youdaonote`：`Ran 77 tests` / `OK`

- [ ] **Step 12: 提交**

说「提交」触发 `commit-cc-plugin`（**用改造后的它自己跑一遍，顺便实测新校验环节**）。提交范围：
```
.claude/skills/commit-cc-plugin/SKILL.md
.claude/skills/commit-cc-plugin/CHANGELOG.md
.claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py
.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py
```

提交消息建议：
```
feat(commit-cc-plugin): 版本决策改为每插件 plugin.json，新增两份同值阻断校验
```

⚠️ **不升任何插件版本号**（改动全在 `.claude/` 下）；`commit-cc-plugin` 自身的 `metadata.version` 已在 Step 10 升为 `3.6.0`。

---

## Task 8: 更新 `skill-conventions.md` 的 8 处活引用

**Files:**
- Modify: `knowledge-base/catalog.json` L79（`consumers`）+ L81（`notes`）
- Modify: `knowledge-base/README.md` L151
- Modify: `knowledge-base/skill-authoring/README.md` L31 + L68
- Modify: `knowledge-base/skill-authoring/rules/01-skill-format.md` L5 + L84

**Interfaces:**
- Consumes: Task 1-3 产出的三份规则文件（引用目标必须已存在，否则指向空文件）
- Produces: 全仓对 `.claude/rules/` 的描述与实际布局一致。**不改任何路径**——`skill-conventions.md` 保留原名（Task 2），本任务只改「它承载什么」的描述文字并补两个新文件

**实测 8 处，spec § 4.1 说 5 处是低估的**（它把 `AGENTS.md` 的 3 处算作一处、把两个 README 各自的两处合并计数）。`AGENTS.md` 的 3 处已在 Task 6 处理完，本任务处理剩余 5 处（分布在 4 个文件、共 6 个位置——`catalog.json` 一处改 `consumers` 一处改 `notes`）。

⚠️ **`catalog.json` 的 `consumers` 不被脚本做路径存在性校验**（实测 `check_index.py` 的 `check_catalog` 只校验 `categories` 对应的目录存在），因此写错路径不会报错。**必须人工核对拼写**。

- [ ] **Step 1: 改 `catalog.json` 的 consumers 与 notes**

Edit `knowledge-base/catalog.json`，把 `skill-authoring` 那条记录的两个字段：

```json
      "consumers": [".claude/rules/skill-conventions.md", ".claude/skills/darwin-skill"],
```
```json
      "notes": "开放 Agent Skills 规范的通用约束；本仓库专属约定见 .claude/rules/skill-conventions.md"
```

分别改为：

```json
      "consumers": [".claude/rules/skill-conventions.md", ".claude/rules/doc-conventions.md", ".claude/rules/agent-conventions.md", ".claude/skills/darwin-skill"],
```
```json
      "notes": "开放 Agent Skills 规范的通用约束；本仓库专属约定见 .claude/rules/ 三份规则文件（skill-conventions / doc-conventions / agent-conventions）"
```

⚠️ **`doc-conventions.md` 与 `agent-conventions.md` 确实算 `skill-authoring` 领域的消费者**——它们承载的 CHANGELOG / README / agent 规范是「怎么写 skill 与 agent 产物」的一部分，与 `skill-conventions.md` 同源拆分而来。不登记会让该领域的消费者清单失真。

- [ ] **Step 2: 改 `knowledge-base/README.md` L151**

Edit，把：

```markdown
- `.claude/rules/skill-conventions.md`：skill 的仓库专属约定（版本号、author、category、前置校验、需求预告、CHANGELOG、README）；通用规范引用 `knowledge-base/skill-authoring/`。
```

改为：

```markdown
- `.claude/rules/skill-conventions.md`：SKILL.md 的仓库专属约定（版本号、author、category、compatibility、allowed-tools、前置校验、需求预告、持续优化）；通用规范引用 `knowledge-base/skill-authoring/`。
- `.claude/rules/doc-conventions.md`：CHANGELOG.md 与 README.md 的格式规范（含 skill / agent 两栏差异）、编辑铁律。
- `.claude/rules/agent-conventions.md`：agent 的仓库专属约定（选型判据、`agents/` 目录硬约束、frontmatter、配套文档位置、独立版本化）。
```

⚠️ **原句里的「CHANGELOG、README」必须从这一行移走**——它们已搬去 `doc-conventions.md`。留着会让读者在 `skill-conventions.md` 里找不到。

- [ ] **Step 3: 改 `skill-authoring/README.md` 的两处**

Edit `knowledge-base/skill-authoring/README.md` L31：

```markdown
2. **前置检查**：按 `.claude/rules/skill-conventions.md` 的仓库专属约定（版本号、author、category、allowed-tools 写法）自查
```

→

```markdown
2. **前置检查**：按 `.claude/rules/skill-conventions.md` 的仓库专属约定（版本号、author、category、allowed-tools 写法）自查；CHANGELOG.md / README.md 的格式要求见 `.claude/rules/doc-conventions.md`
```

Edit 同文件 L68：

```markdown
- `.claude/rules/skill-conventions.md`：仓库级规则文件，聚焦本仓库专属约定（版本号、author、category、allowed-tools、前置校验、需求预告、CHANGELOG、README 章节）；其中涉及"如何创建 skill"的规范引用本领域各篇
```

→

```markdown
- `.claude/rules/skill-conventions.md`：仓库级规则文件，聚焦 SKILL.md 的专属约定（版本号、author、category、allowed-tools、前置校验、需求预告、持续优化）；其中涉及"如何创建 skill"的规范引用本领域各篇
- `.claude/rules/doc-conventions.md`：CHANGELOG.md 与 README.md 章节规范，skill 与 agent 共用（两者在「所处层级」「触发词」两章有分叉写法）
- `.claude/rules/agent-conventions.md`：agent 产物的专属约定，与 skill 是并列的两套规范，不互相套用
```

- [ ] **Step 4: 改 `rules/01-skill-format.md` 的两处**

Edit `knowledge-base/skill-authoring/rules/01-skill-format.md` L5：

```markdown
> 来源：[Agent Skills 规范](https://agentskills.io/specification)。本篇是格式层面的**硬约束**——违反会导致 skill 无法被跨 runtime 识别或校验失败。仓库专属约定（版本号、author、category、allowed-tools 写法）见 `.claude/rules/skill-conventions.md`，本篇不重复。
```

→

```markdown
> 来源：[Agent Skills 规范](https://agentskills.io/specification)。本篇是格式层面的**硬约束**——违反会导致 skill 无法被跨 runtime 识别或校验失败。仓库专属约定（版本号、author、category、allowed-tools 写法）见 `.claude/rules/skill-conventions.md`，配套文档（CHANGELOG / README）格式见 `.claude/rules/doc-conventions.md`，本篇均不重复。
```

Edit 同文件 L84：

```markdown
- **应该**：校验通过后，按 `.claude/rules/skill-conventions.md` 的仓库约定（版本号、author、category、CHANGELOG）补齐仓库侧要求
```

→

```markdown
- **应该**：校验通过后，按 `.claude/rules/skill-conventions.md` 补齐 SKILL.md 侧要求（版本号、author、category），按 `.claude/rules/doc-conventions.md` 补齐 CHANGELOG.md 与 README.md
```

⚠️ **这一条是 MUST/SHOULD 语气的规范条款行**（knowledge-base 性质，见 `AGENTS.md` 的 docs/knowledge-base 划分表）。**只改引用指向，不动「应该」二字**——改语气等于改规范级别，超出本次范围。

- [ ] **Step 5: 核对引用完整性与 JSON 可解析**

Run:
```bash
echo "=== 三份规则文件都被提及几次 ==="
for f in skill-conventions doc-conventions agent-conventions; do
  printf '%-20s' "$f"
  grep -rc "$f" knowledge-base/catalog.json knowledge-base/README.md \
    knowledge-base/skill-authoring/README.md \
    knowledge-base/skill-authoring/rules/01-skill-format.md 2>/dev/null \
    | awk -F: '{s+=$2} END {print s}'
done
echo ""
echo "=== catalog.json 可解析且 consumers 已含三份 ==="
python -c "
import json
d = json.load(open('knowledge-base/catalog.json', encoding='utf-8'))
e = [x for x in d['domains'] if x['domain'] == 'skill-authoring'][0]
print('consumers:', e['consumers'])
for want in ['.claude/rules/skill-conventions.md', '.claude/rules/doc-conventions.md', '.claude/rules/agent-conventions.md']:
    assert want in e['consumers'], f'缺 {want}'
print('PASS')
"
echo ""
echo "=== consumers 里登记的路径必须真实存在（脚本不校验，人工补校验）==="
python -c "
import json, pathlib
d = json.load(open('knowledge-base/catalog.json', encoding='utf-8'))
missing = []
for e in d['domains']:
    for c in e.get('consumers', []):
        if not pathlib.Path(c).exists():
            missing.append(f\"[{e['domain']}] {c}\")
print('不存在的 consumers 路径:', missing or '（无，全部存在）')
assert not missing, missing
"
```

Expected:
- `skill-conventions` ≥ 5、`doc-conventions` ≥ 4、`agent-conventions` ≥ 3
- `catalog.json` `PASS`
- 不存在的 consumers 路径 = 无

⚠️ 最后一段是**本任务补的人工校验**（`check_index.py` 不做这件事）。若报某路径不存在，说明 Task 1-3 未完成或文件名拼错。

- [ ] **Step 6: 跑知识库两个校验脚本**

Run:
```bash
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
echo "check_index 退出码: $?"
echo ""
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
echo "check_refs 退出码: $?"
```

Expected: 两个都 PASS，退出码 0。条目数不变（全局 576）。

⚠️ **本任务不改 `index.jsonl`、不改 `rules/` 的条目结构**，因此条目数必然不变。若数字变了，说明误改了正文的小节标题——`01-skill-format.md` 的 L5 与 L84 都不是小节标题行，正确操作不会影响索引。

⚠️ `check_refs.py` 的 `CONSUMER_GLOBS` 不含 `.claude/rules/*.md`，所以三份规则文件里的 `knowledge-base/...` 引用**不被该脚本校验**。这是既有行为，本次不扩展（扩展 glob 属 `dotnet-diagnose` spec § 8.4 范围）。

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
knowledge-base/catalog.json
knowledge-base/README.md
knowledge-base/skill-authoring/README.md
knowledge-base/skill-authoring/rules/01-skill-format.md
```

提交消息建议：
```
docs(kb): 规则文件引用更新为三份，补 doc/agent-conventions
```

⚠️ **不升任何版本号**——`knowledge-base/` 在触发矩阵最后一行。

⚠️ **也不升 `skill-authoring` 领域的版本号**：本次是「引用指向修正」，未新增/删除/改写任何索引条目。领域版本号只随条目变更升（见 `knowledge-base/README.md` 的版本化规则）。

---

## Task 9: `dotnet-diagnose` spec 的六处同步修正

**Files:**
- Modify: `docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md`（§ 2.5 表 L103/L104、§ 8.1 表 L379、§ 8.2 L407、§ 8.4 表 L427/L428/L432、§ 8.5 L445-456、§ 10.2 L516、§ 10.4 L546/L548）

**Interfaces:**
- Consumes: Task 1-8 全部落地（本任务把新规范的结论回写进下游 spec）
- Produces: 与本次规范一致的 `dotnet-diagnose` spec，其实施计划可直接依据它执行

**为什么这是本计划的最后一个任务**：`dotnet-diagnose` spec 是本规范的**首个适用对象**（本计划 spec 头部的「关联」行）。它现文六处仍按旧规范写（agent 无 CHANGELOG/README、版本由 marketplace 统一管理、顶层升 14.1.0），不修正则 agent 实施时会照旧规范执行，本次改动白做。

⚠️ **本任务只改 spec 文档，不创建任何 agent 或 skill**——那是 `dotnet-diagnose` 自己实施计划的范围（本计划 § 文件结构「明确不动」已声明）。

- [ ] **Step 1: 改 § 2.5 双 harness 均等性表**

Edit，把表中这两行：

```markdown
| agent 目录 | 插件根 `agents/`，自动发现，无需在 manifest 声明 | 插件根 `agents/`（官方 `dotnet-diag/0.1.0/agents/` 实证） |
| 文件命名 | 无强制规则，`name` 字段优先，文件名为 fallback | `*.agent.md`（官方实践） |
```

改为：

```markdown
| agent 目录 | 插件根 `agents/`，**必须在 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**（该字段是 replaces 语义，取代默认扫描） | 插件根 `agents/`（官方 `dotnet-diag/0.1.0/agents/` 实证） |
| 文件命名 | 无强制规则，`name` 字段优先，文件名为 fallback。⚠️ `.agent.md` 双扩展名来自 **VS Code / Copilot 约定，非 Claude Code 官方**（官方示例为纯 `.md`），沿用它是跟随微软 `dotnet/skills` 实践 | `*.agent.md`（官方实践） |
```

**两处实质变化**：① 删去「自动发现，无需在 manifest 声明」——自动发现存在，但显式声明才是防假 agent 的机制；② 补明 `.agent.md` 的真实来源，避免后续维护者误以为官方文档里能查到依据。

- [ ] **Step 2: 改 § 8.1 交付文件清单**

Edit，把 agent 那一行的「适用规范」列：

```markdown
| `plugins/optimus-devops-plugin/agents/dotnet-diagnose.agent.md` | 编排层：三步主干、加载 skill 时机、边界、输出格式（含台账交接块）、免责声明。**≤ 80 行** | agent 规范（四字段，无 CHANGELOG/README） |
```

改为：

```markdown
| `plugins/optimus-devops-plugin/agents/dotnet-diagnose.agent.md` | 编排层：三步主干、加载 skill 时机、边界、输出格式（含台账交接块）、免责声明。**≤ 80 行** | `.claude/rules/agent-conventions.md`（四字段 frontmatter，**有 CHANGELOG/README，位置在 `agent-docs/`**） |
```

再在该表的 agent 行之后（skill 行之前）**插入三行新交付文件**：

```markdown
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md` | 初始 `[1.0.0]` — **agent 版本号真源** | `.claude/rules/doc-conventions.md` |
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md` | 六章节，其中「所处层级」按与相邻产物的划界画图、「触发词」改为调用方式与触发面 | `.claude/rules/doc-conventions.md`（agent 分栏） |
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | **已在本次规范实施时新建**（`name` + `version`）；本次只需**增补** `"agents": ["./agents/dotnet-diagnose.agent.md"]` | `.claude/rules/agent-conventions.md` |
```

⚠️ **第三行是「增补」不是「新建」**——本计划 Task 5 已给 devops 建好 `plugin.json`（含 `name` + `version: "1.0.0"`），`dotnet-diagnose` 实施时只需往里加 `agents` 字段。写成「新建」会导致覆盖已有的 `version`。

再改该表下方的连带后果段：

```markdown
**结构变化的连带后果**：skill 层回归 skill 的完整规范，因此 CHANGELOG / README / known-issues / **darwin-skill 基线评估**全部适用——这与只建 agent 时的豁免（§ 8.5）不同。agent 层仍豁免。
```

→

```markdown
**结构变化的连带后果**：skill 层回归 skill 的完整规范，因此 CHANGELOG / README / known-issues / **darwin-skill 基线评估**全部适用。**agent 层的豁免范围已收窄**：CHANGELOG / README **不再豁免**（位置在 `agent-docs/dotnet-diagnose/`），仅 `known-issues.md` 与 darwin-skill 评分门禁仍豁免（§ 8.5）。
```

- [ ] **Step 3: 改 § 8.2 frontmatter 规格**

Edit，把这一条：

```markdown
- **不加 `metadata.version`**：Claude 侧插件 agent 的 frontmatter 容错是静默降级（解析失败则全部字段被忽略），加入两侧未共同验证的字段有风险；版本由 marketplace 统一管理
```

改为：

```markdown
- **不加 `metadata.version`**：插件 agent 的 11 个合法字段里**不含 `metadata`**（与 skill 不同——skill 有 agentskills.io 规范明确留出的 `metadata` 自由映射）；且 Claude 侧 frontmatter 容错是静默降级（解析失败则全部字段被忽略），加未知键是在赌文档空白。**agent 版本号记在 `agent-docs/dotnet-diagnose/CHANGELOG.md` 的最新 `## [x.y.z]`**，首版 `1.0.0`，与所属插件版本互不换算
```

**改的是后半句**：「版本由 marketplace 统一管理」已失效——marketplace 顶层不再是任何产物的版本来源。同时把「不加」的**理由从「有风险」升级为「字段清单里没这个键」**，这是更硬的依据。

- [ ] **Step 4: 改 § 8.4 同期改动表的三行**

Edit，把这三行：

```markdown
| `.claude-plugin/marketplace.json` | 顶层 `version` 14.0.0 → **14.1.0**；`optimus-devops-plugin` 的 `description` 加入诊断能力 | 「功能变了版本号不变 = 不完整交付」；description 不改则用户看不到该能力 |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `version` 同步 14.1.0；`description` 与 `interface.longDescription` 两处同步；`interface.capabilities` 由 `["Skills"]` 增补 agent 能力（**须先验证该取值合法，不合法则不改此项**） | version 从 marketplace 抄录，不同步即失真 |
```

改为：

```markdown
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | `version` `1.0.0` → **`1.1.0`**（Minor，新增 agent + skill）；增补 `"agents": ["./agents/dotnet-diagnose.agent.md"]` | 「功能变了版本号不变 = 不完整交付」；不声明 `agents` 则失去 replaces 语义的防假 agent 保护 |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `version` **同一次改动内一起升到 `1.1.0`**（与上一行同值，无先后主从）；`description` 与 `interface.longDescription` 两处同步；`interface.capabilities` 由 `["Skills"]` 增补 agent 能力（**须先验证该取值合法，不合法则不改此项**） | 两份不同值会被 `commit-cc-plugin` 的同值校验阻断 |
| `.claude-plugin/marketplace.json` | **顶层 `version` 保持 `14.0.0` 不动**；只改 `optimus-devops-plugin` 的 `description` 加入诊断能力 | 顶层仅在增删插件时升——本次是给已有插件加内容，不改集合构成；description 不改则用户看不到该能力 |
```

⚠️ **表格行序也变了**：原表以 marketplace 开头（旧机制它是真源），新表以 `.claude-plugin/plugin.json` 开头（新真源），marketplace 降到第三行且只剩 `description` 一项职责。**行序体现的是真源位置，不是排版偏好。**

⚠️ **`1.0.0` → `1.1.0` 的前提**：Task 4/5 已把 devops 重置为 `1.0.0`。若 Task 4 的 CHECKPOINT 走了退路（改为从当前值递增），此处的 `1.0.0 → 1.1.0` 须相应改为「当前值 → 当前值升 Minor」。**执行本步时先确认 devops 的实际当前值。**

再改同表的 `skill-conventions.md` 那一行：

```markdown
| `.claude/rules/skill-conventions.md` | ✅ **已完成**：① `paths` 增 `plugins/*/agents/**/*.agent.md`（编辑 agent 文件时自动加载本规范）；② 新增「Agent 规范」节——选型判据、目录命名、四字段 frontmatter、`claude plugin validate` 强制校验、不适用的 skill 规范清单、版本管理 | 同上 |
```

改为：

```markdown
| `.claude/rules/agent-conventions.md` | ✅ **已完成**（由 `2026-09-06-rules-split-and-agent-docs-design.md` 交付）：agent 规范已从 `skill-conventions.md` 拆出为独立文件，`paths` 为 `plugins/*/agents/**/*.md`（用 `*.md` 而非 `*.agent.md`，纯 `.md` 的 agent 也能命中）；含选型判据、`agents/` 目录硬约束、frontmatter、配套文档位置、独立版本化、darwin-skill 豁免 | 同上 |
```

- [ ] **Step 5: 改 § 8.5 门禁落点**

Edit，把 § 8.5 的开头两段与表：

```markdown
AGENTS.md 版本管理表原先列的是「新增 skill/hook/command」，未列 agent。本 spec 撰写期间已按语义补入 agent（「新增用户可见功能 → Minor」），并同步写明 `darwin-skill` 评分门禁只约束 skill——其 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应维度。

**改为两层后，门禁并非整体豁免**，按层区分：
```

改为：

```markdown
AGENTS.md 的版本管理节已由 `2026-09-06-rules-split-and-agent-docs-design.md` 整节重写：版本落点下移至每插件的两份 `plugin.json`，含「什么改动升哪一层」的触发矩阵；`darwin-skill` 评分门禁只约束 skill——其 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应维度。

**agent 层的豁免范围已收窄，须按项区分**：CHANGELOG / README **不再豁免**（`agent-conventions.md` 定为必须，位置在 `agent-docs/<name>/`），仅 `known-issues.md` 与 darwin-skill 评分门禁仍豁免——后者是因为 `known-issues.md` 本身就是 darwin-skill 循环的输入产物，两者同进同退。

**darwin-skill 按层区分：**
```

- [ ] **Step 6: 改 § 10.2 与 § 10.4 验收清单**

Edit § 10.2，在 `claude plugin validate` 那一项**之前**插入三项：

```markdown
- [ ] `agent-docs/dotnet-diagnose/CHANGELOG.md` 初始 `[1.0.0]`；`README.md` 六章节齐备，「所处层级」按与相邻产物的划界画图（非 category 层级图）、「触发词」为调用方式与触发面
- [ ] README 头部的版本号与 `agent-docs/dotnet-diagnose/CHANGELOG.md` 最新条目**一致**
- [ ] `agents/` 目录下**只有** `dotnet-diagnose.agent.md` 一个文件，无 CHANGELOG / README / 任何辅助文件（否则会注册成假 agent）
- [ ] `.claude-plugin/plugin.json` 已含 `"agents": ["./agents/dotnet-diagnose.agent.md"]`，且原有 `name` / `version` 未被覆盖
```

Edit § 10.4，把这一项：

```markdown
- [ ] marketplace 14.1.0 与 `.codex-plugin/plugin.json` 版本一致
```

改为：

```markdown
- [ ] devops 两份 `plugin.json`（`.claude-plugin/` 与 `.codex-plugin/`）版本**同值**且已升 **Minor**（新增 agent + skill）；`marketplace.json` 顶层 `version` **保持 `14.0.0` 未动**
- [ ] `python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .` 通过（两份同值校验）
```

再改这一项：

```markdown
- [ ] AGENTS.md 与 `.claude/rules/skill-conventions.md` 的 agent 规范已补（✅ 撰写期间已完成，实施时只需复核未被回退）
```

改为：

```markdown
- [ ] `AGENTS.md` 与 `.claude/rules/agent-conventions.md` 的 agent 规范已就位（由 `2026-09-06-rules-split-and-agent-docs-design.md` 交付，实施时只需复核未被回退）
```

- [ ] **Step 7: 核对六处全部落地且旧表述清除**

Run:
```bash
F=docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md
echo "=== 旧表述必须全部为 0 ==="
for kw in '自动发现，无需在 manifest 声明' '版本由 marketplace 统一管理' '14.1.0' 'version 从 marketplace 抄录' '无 CHANGELOG/README' 'agent 层仍豁免'; do
  printf '%-34s' "$kw"; grep -c "$kw" "$F"
done
echo ""
echo "=== 新表述必须都命中 ==="
for kw in 'agent-conventions.md' 'agent-docs/dotnet-diagnose' 'VS Code' '保持 .14.0.0. 未动\|保持 `14.0.0`' 'check_plugin_versions.py' '同一次改动内一起升'; do
  printf '%-32s' "$kw"; grep -c "$kw" "$F"
done
echo ""
echo "=== skill-conventions 的 agent 规范引用应已改指向 ==="
grep -n 'skill-conventions' "$F"
```

Expected:
- 6 条旧表述各 = **0**
- 6 条新表述各 ≥ **1**
- `skill-conventions` 的剩余命中（若有）**不得**再声称承载 agent 规范

⚠️ **`14.1.0` 必须为 0**：该值出现在 § 8.4 与 § 10.4 两处，都已在 Step 4/6 改掉。若仍有命中，说明漏了一处——顶层版本号在新规范下不会因新增 agent 而动。

- [ ] **Step 8: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md`。

提交消息建议：
```
docs(spec): dotnet-diagnose 六处同步新版本机制与 agent 配套文档规范
```

⚠️ **不升任何版本号**——`docs/` 在触发矩阵最后一行。

---

## 完成后的整体核验

全部 9 个任务完成后跑一遍，对齐 spec § 9 验收标准：

```bash
echo "########## § 9.1 拆分正确性 ##########"
wc -l .claude/rules/*.md
grep -c '^  - "' .claude/rules/skill-conventions.md   # 应为 1

echo ""
echo "########## § 9.2 旧豁免声明在三份文件里全部清零 ##########"
for kw in '不要求 CHANGELOG' '不独立版本化' '随 .claude-plugin/marketplace.json 统一管理' '不适用于 agent 的 skill 规范'; do
  printf '%-46s' "$kw"
  grep -rc "$kw" .claude/rules/ 2>/dev/null | awk -F: '{s+=$2} END {print s+0}'
done

echo ""
echo "########## § 9.4 版本真源下移 ##########"
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
python -c "
import json
d = json.load(open('.claude-plugin/marketplace.json', encoding='utf-8'))
assert d['version'] == '14.0.0', f\"顶层被改动: {d['version']}\"
assert not [p['name'] for p in d['plugins'] if 'version' in p], '条目内出现 version'
print('marketplace: 顶层 14.0.0、条目无 version — PASS')
"

echo ""
echo "########## AGENTS.md 旧表述清零 ##########"
grep -c '抄录\|共用的版本号真源' AGENTS.md

echo ""
echo "########## § 9.5 连带改动 ##########"
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py

echo ""
echo "########## 全部单元测试 ##########"
python -m unittest discover -s .claude/skills/commit-cc-plugin/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/sync-cc-tips/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/sync-cc-docs-to-youdaonote/scripts -p "test_*.py" 2>&1 | tail -3

echo ""
echo "########## 工作树应干净 ##########"
git status --short
```

Expected:
- 三份规则文件合计 ≥ 248 行；`skill-conventions.md` 的 paths 恰 1 条
- 四条旧豁免声明在 `.claude/rules/` 下各 = **0**（spec § 9.2 的显式验证要求）
- 版本校验 PASS；marketplace PASS
- `AGENTS.md` 旧表述 = **0**
- 两个知识库脚本 PASS
- 四组测试全 `OK`（11 / 139 / 46 / 77）
- `git status --short` 为空（全部已提交）

⚠️ **本计划**不覆盖 spec § 9.2 / § 9.3 的部分验收项——它们要求「agent 规范落地后有实际 agent 可验」，而本仓当前 agent 数为 0。那些项在 `dotnet-diagnose` 实施时才有验证对象，届时按其 spec § 10.2 核验。

---
