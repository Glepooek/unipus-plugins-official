# dotnet-diagnose agent + skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `optimus-devops-plugin` 交付本仓首个 agent（`dotnet-diagnose`，编排层）与其承载 skill（`dotnet-diagnose-triage`，判据层），把 `knowledge-base/dotnet-debugging/` 的 74 条判据变成可调用的根因定位能力。

**Architecture:** 两层产物 + 一批同期改动，共 8 个任务。agent 只写编排（≤80 行，不含任何判据），skill 承载全部判据引用（SKILL.md 主干 + 三个按需下钻的 `references/`）。判据一律以 `file § anchor` 引用知识库，不复制正文。

| 阶段 | 任务 | 性质 |
|---|---|---|
| ① 承载层 | Task 1-4 | skill 骨架 → 三个 references → 台账/自检主干 → 黄金测例 |
| ② 编排层 | Task 5-6 | agent 本体 + `agents` 声明与加载实测 → agent 配套文档 |
| ③ 收口 | Task 7-8 | 同期改动（版本、consumers、glob、marketplace description）→ 黄金测例逐例人工跑 + 全量验收 |

阶段 ① 必须先于 ②——agent 正文要写「加载哪个 skill、什么时机」，skill 不存在时那句话无处落。Task 8 依赖全部前序。

**Tech Stack:** Markdown（SKILL.md 六字段 frontmatter / agent 三字段 frontmatter）、JSON 清单、Python 3（`unittest`，本机无 `pytest`）、`claude plugin validate` 与 `claude -p` 无头模式 CLI。

**Spec:** `docs/superpowers/specs/2026-09-05-dotnet-diagnose-agent-design.md`

## Global Constraints

以下约束对**每个任务**同时生效，任务内不再重复：

- **提交必须走 `commit-cc-plugin` skill**，禁止手动执行 git 工作流。计划中的 `git` 命令仅用于**只读检查**（`git status` / `git diff` / `git log`）。
- **编辑 Markdown 禁止无关格式化**：不增删空行、不调缩进、不做表格对齐。提交前看 `git diff`，出现大片纯空白变化说明格式化工具介入了，撤销重做。
- **写长文档必须分段**：SKILL.md、三个 references、golden.md 都会超过百行。用 `Write` 建骨架 + 多次 `Edit` 逐节追加，禁止单次输出几百行。
- **本机无 `pytest`，只能用 `unittest`**。
- **判据引用形态**（spec § 3.1 实测）：命令篇是 `<观察> → **证实**` / `→ **排除**`（箭头 + 加粗，**无冒号**），决策表是第三列文字（**不加粗**）。⚠️ **全角冒号的 `证实：` / `排除：` 在全域零命中**，不得按该形态检索或书写。
- **知识库正文一律不改**：本次只消费不新增判据。`knowledge-base/dotnet-debugging/` 的 `index.jsonl` 与 `reference/`、`rules/` 正文**全程不动**，领域版本 1.2.0 不变。唯一例外是 README 里一句过时陈述（Task 7）。
- **本次改动的版本号落点**（三条）：
  - **Task 1-4、6** 落在 `plugins/optimus-devops-plugin/skills/` 与 `agent-docs/` 内 → 升 devops **两份** `plugin.json`（`1.0.0` → `1.1.0`，Minor，新增 skill + agent），且新 skill 的 `metadata.version` 起 `1.0.0`、新 agent 的 CHANGELOG 起 `[1.0.0]`。**两份 plugin.json 的 `version` 在 Task 7 一次性升到位**，前序任务不各自升（否则每个任务都要动同两个文件，且中间态会被 `check_plugin_versions.py` 判为不一致——它只校验两份同值，不校验是否已升）
  - **Task 5** 增补 `agents` 字段属插件内容改动 → 同上，由 Task 7 统一升版
  - **Task 7 的 `.claude/`、`knowledge-base/`、`marketplace.json` description 部分不升任何版本号**（AGENTS.md 触发矩阵最后两行 + 「展示元数据不升」行）
- **`marketplace.json` 顶层 `version` 全程保持 `14.0.0`**——本次是给已有插件加内容，不改集合构成（AGENTS.md 触发矩阵）。
- **agent 文件命名用纯 `.md`，禁止 `.agent.md`**（spec § 2.5 实测：`.agent.md` 是 VS Code / Copilot 约定，Claude Code 官方文档零提及）。
- **agent frontmatter 恰三字段** `name` / `description` / `tools`，**不含 `license`**（不在官方 11 字段清单内）、不含 `metadata`。
- **`claude plugin details` 的 Agents 列不可信**（spec § 2.5 约束 2：声明 `agents` 时统计为 0、显示文件名而非注册名）。**核验加载只用 `claude -p` 无头模式实调**。
- **darwin-skill 按层区分**：skill 层必须跑基线评估（新建 skill，`knowledge-base/skill-authoring/rules/06-continuous-improvement.md § 1`），agent 层不跑（rubric 无对应维度）。

---

## 文件结构

### 新建（12 个）

| 文件 | 职责 | 预估行数 |
|---|---|---|
| `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md` | 承载层主干：台账规则、自检四项、三结论强度、九条失败处理、交接表、合规约束 | ~170 |
| `.../dotnet-diagnose-triage/references/symptom-hypothesis-map.md` | 8 类征象 × 合并候选集 + 二维路由表 + 第二跳去向清单 | ~110 |
| `.../dotnet-diagnose-triage/references/evidence-precheck.md` | B 组三项证据可用性校验 + 崩溃日志定位与区分线 | ~70 |
| `.../dotnet-diagnose-triage/references/verdict-forms.md` | 判据两种书写形态 + 修复方向四档分级与转述规则 | ~85 |
| `.../dotnet-diagnose-triage/CHANGELOG.md` | 初始 `[1.0.0]` | ~10 |
| `.../dotnet-diagnose-triage/README.md` | 六章节（全 ASCII box-drawing） | ~90 |
| `.../dotnet-diagnose-triage/known-issues.md` | darwin-skill 基线评估记录 | ~15 |
| `.../dotnet-diagnose-triage/test-cases/golden.md` | 七个黄金测例，每例四段 | ~150 |
| `plugins/optimus-devops-plugin/agents/dotnet-diagnose.md` | 编排层，**≤ 80 行** | ≤80 |
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md` | 初始 `[1.0.0]` — **agent 版本号真源** | ~10 |
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md` | 六章节，「所处层级」按划界画图、「触发词」为调用方式 | ~85 |

⚠️ **只有 11 行**——spec § 8.1 的第 12 项 `.claude-plugin/plugin.json` 是**增补**已有文件，不是新建，列在下表。

### 修改（7 个）

| 文件 | 改动性质 |
|---|---|
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | 增补 `agents` 字段（Task 5）+ `version` → `1.1.0`（Task 7） |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `version` → `1.1.0` + description 两处同步 + `capabilities` 增补（Task 7） |
| `.claude-plugin/marketplace.json` | 只改 devops 的 `description`，**顶层 `version` 不动** |
| `knowledge-base/catalog.json` | `dotnet-debugging` 的 `consumers` 由 `[]` 登记 skill 层 + `reviewed_at` |
| `knowledge-base/dotnet-debugging/README.md` L18 | 「本领域一期无固定 skill 消费者」改为指向本次产物 |
| `.claude/skills/knowledge-base-maintain/scripts/check_refs.py` | `CONSUMER_GLOBS` 增 `plugins/*/skills/*/references/*.md` 一行 |
| `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py` L112 | 测试固件里的 `./agents/x.agent.md` 改为 `./agents/x.md` |

### 明确不动

- `knowledge-base/dotnet-debugging/` 的 `index.jsonl` 与全部 `reference/`、`rules/` 正文（本次只消费）
- `knowledge-base/dotnet-debugging/CHANGELOG.md`（无条目变更，领域版本 1.2.0 不变）
- `.claude/rules/` 三份规则文件（agent 规范修正已在本计划**之前**独立完成）
- `AGENTS.md`（同上，L28 与触发矩阵的 `.agent.md` → `.md` 已改完）
- `marketplace.json` 顶层 `version` 与其余 9 个插件条目
- devops 现有四个 skill（`jenkins-build` / `project-analyze` / `sync-skill-symlinks` / `weekly-report`）

### 两层的引用方向

```
agents/dotnet-diagnose.md   （编排：三步主干 + 加载时机 + 边界 + 输出格式）
        │ 用 Skill 工具加载
        ▼
skills/dotnet-diagnose-triage/SKILL.md   （每轮都用：台账 / 自检 / 强度 / 失败处理）
        │ progressive disclosure，按需下钻
        ├──▶ references/symptom-hypothesis-map.md   （定征象那一轮）
        ├──▶ references/evidence-precheck.md        （手里有 dump 或崩溃日志时）
        └──▶ references/verdict-forms.md            （裁剪台账与出结论给修复方向时）
                │ 全部以 file § anchor 引用，不复制正文
                ▼
        knowledge-base/dotnet-debugging/（74 条判据，14 篇 reference + 1 篇 rules）
```

**判据密度分布**：`symptom-hypothesis-map.md` 与 `verdict-forms.md` 是 anchor 最密的两份，这正是 Task 7 要给 `check_refs.py` 补 glob 的原因——现有四条 glob 覆盖不到 `skills/*/references/` 子目录。

---

## Task 1: skill 骨架与 frontmatter

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md`（仅 frontmatter + 概述 + 章节标题占位）
- Read (不改): `plugins/optimus-devops-plugin/skills/project-analyze/SKILL.md`（frontmatter 范式）

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: skill 目录与合规的六字段 frontmatter。**Task 5 的 agent 正文要写「加载 `optimus-devops-plugin:dotnet-diagnose-triage`」，`name` 字段在本任务定稿后不得再改**

**为什么先建骨架再填内容**：SKILL.md 最终约 170 行，一次写完违反分段输出规则；且 frontmatter 的 `name` 是后续 agent 正文与 README 的引用目标，先定稿能避免返工。

- [ ] **Step 1: 确认知识库现状未变**

Run:
```bash
python .claude/skills/knowledge-base-maintain/scripts/check_index.py 2>&1 | tail -5
echo "=== dotnet-debugging 条目数（应 74）==="
grep -c '"domain": "dotnet-debugging"' knowledge-base/dotnet-debugging/index.jsonl || \
  wc -l < knowledge-base/dotnet-debugging/index.jsonl
echo "=== 领域文件应为 14 篇 reference + 1 篇 rules ==="
ls knowledge-base/dotnet-debugging/reference/ | wc -l
ls knowledge-base/dotnet-debugging/rules/ | wc -l
```

Expected: `check_index.py` PASS；index.jsonl 74 行；reference 14 个文件；rules 1 个文件。

⚠️ 若条目数或文件数与此不符，说明知识库在 spec 撰写后被改过——**先停下核对 spec § 3.2 的候选集数字是否仍然成立再继续**，那张表是台账初始化的唯一依据。

- [ ] **Step 2: 创建 SKILL.md 的 frontmatter 与概述**

Create `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md`：

````markdown
---
name: dotnet-diagnose-triage
description: 解读已取得的 .NET 取证输出并按假设台账定位根因：SOS 命令输出逐列语义、dump 类型与符号的可用性前置校验、假设消解与跨轮续用、WPF 专属归因（Dispatcher 死锁与四类泄漏堆形态）、.NET Framework 4.x 分析侧。判据全部引用 knowledge-base/dotnet-debugging/，不复制正文。触发词：这个 dump 说明什么问题、SOS 输出怎么读、!dumpheap 结果分析、!syncblk 死锁判断、!gcroot 根链读法、托管内存泄漏定位、线程池饥饿判断、WPF 窗口关不掉泄漏、崩溃日志异常链、analyze dump output、read SOS output。不做取证抓取——需要抓 dump 或选采集工具时转 dump-collect / dotnet-trace-collect。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: quality
compatibility: 纯文本推理，无运行时依赖。判据来源 knowledge-base/dotnet-debugging/（须与本仓库同处一个工作树才能读到）。不执行任何诊断命令——抓取 dump 与采集 trace 由用户自行完成或转微软官方 dotnet-diag 插件。
allowed-tools: Read Glob Grep
---

# .NET 取证输出解读与根因定位

## 概述

本 skill 是 `dotnet-diagnose` agent 的承载层，把 `knowledge-base/dotnet-debugging/` 的 74 条判据组织成可执行的**假设消解循环**。

**做什么**：读懂已经拿到的证据（dump / SOS 输出 / trace 报告 / 崩溃日志），按知识库判据裁剪候选根因，给出带出处与强度标注的结论。

**不做什么**：不抓 dump、不选采集工具、不执行任何诊断命令。这一半由微软官方 `dump-collect` / `dotnet-trace-collect` 覆盖且更完备（含容器与 K8s 适配），我们专做官方明确拒绝的分析侧。

**为什么核心数据结构是台账而不是流程步骤**：知识库每条命令条目的第 4 段固定为「判据：能证实 / 排除什么假设」，这些判据在语义上就是假设集上的消解算子；两张决策表的「候选根因」列就是初始假设集。因此本 skill 只需写清循环规则，判据本身一律按 `file § anchor` 引用。
````

⚠️ **`description` 的三条硬要求**（spec § 8.3）：① 必须写明「已经拿到证据之后」这个时机边界，否则取证阶段的用户误触发会浪费一轮；② 保留 `dump` / `SOS` / `trace` / `WPF` / `.NET Framework` 等**原形技术标识符**——它们在中英文提问里都会出现，是跨语言的公共触发面；③ 主体保持中文（与知识库、其余 48 个 skill 一致），**不做双语**——两个 harness 均按单一 description 匹配，双语会稀释语义密度。

⚠️ **`allowed-tools` 恰 `Read Glob Grep` 三项**：本 skill 只读知识库文件做推理，不写文件、不执行命令、不派发子代理（故**不含 `Task`**）。

⚠️ **`category: quality`** 而非 `decision`——它产出的是带出处的诊断结论（quality：性能诊断明确在该档），不是选型建议。

- [ ] **Step 3: 追加六个章节标题占位**

Append to SKILL.md：

````markdown

## 假设台账

## 出结论前的自检

## 三种结论强度

## 失败处理

## 与官方产物的交接

## dump 处置合规
````

**占位的作用**：Task 3 会逐节填内容。先立标题能让 Step 4 的结构校验有可比对象，也避免填内容时漏节。

- [ ] **Step 4: 校验 frontmatter 合规**

Run:
```bash
F=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md
echo "=== 顶层字段（只允许 6 个规范字段，本次用 5 个）==="
sed -n '/^---$/,/^---$/p' "$F" | grep -E '^[a-z-]+:' 
echo ""
echo "=== metadata 三项 ==="
sed -n '/^metadata:/,/^[a-z]/p' "$F" | grep -E '^  '
echo ""
echo "=== description 字符数（须 < 1024，且含时机边界）==="
python -c "
import re, pathlib
t = pathlib.Path('$F').read_text(encoding='utf-8')
m = re.search(r'^description: (.+)$', t, re.M)
d = m.group(1)
print('长度:', len(d))
for kw in ['dump', 'SOS', 'trace', 'WPF', '.NET Framework', 'dotnet-trace-collect']:
    print(f'  含 {kw}:', kw in d)
"
echo ""
echo "=== 章节标题（应为 概述 + 6 节 = 7 个二级标题）==="
grep -c '^## ' "$F"
```

Expected:
- 顶层字段恰 `name` / `description` / `metadata` / `compatibility` / `allowed-tools` **五个**（`license` 本仓 skill 不写）
- `metadata` 下三项：`version` / `author` / `category`
- description 长度 < 1024，六个关键词全为 `True`
- 二级标题数 = **7**

⚠️ **顶层出现第六个字段就是错**——开放 Agent Skills 规范只允许六个（`name`/`description`/`license`/`compatibility`/`metadata`/`allowed-tools`），多余字段会让跨 runtime 严格校验器报 "Unexpected fields in frontmatter"。

- [ ] **Step 5: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md`。

提交消息建议：
```
feat(devops-plugin): 新建 dotnet-diagnose-triage skill 骨架与 frontmatter
```

⚠️ **本任务不升 devops 两份 `plugin.json`**——按 Global Constraints，两份 `version` 在 Task 7 一次性升到 `1.1.0`。若 `commit-cc-plugin` 第二步提示要升版本，答「本次为多任务交付的第 1 步，版本在收口任务统一升 Minor」。

---

## Task 2: 三个 references 文件

**Files:**
- Create: `.../dotnet-diagnose-triage/references/symptom-hypothesis-map.md`
- Create: `.../dotnet-diagnose-triage/references/evidence-precheck.md`
- Create: `.../dotnet-diagnose-triage/references/verdict-forms.md`
- Read (不改): `knowledge-base/dotnet-debugging/reference/*.md`（核对 anchor 逐字一致）

**Interfaces:**
- Consumes: Task 1 的 skill 目录
- Produces: 三份下钻文件。**Task 3 的 SKILL.md 主干要写「何时加载哪一份」，本任务的三个文件名定稿后不得再改**；Task 4 的黄金测例 1/3/5/6/7 直接考这三份的内容

**分文件的判据是「是否每轮都要读」**（spec § 2.2）：征象映射表与路由表只在定征象那一轮用，证据校验只在收到新证据时用，判据形态与修复分级在裁剪与收尾两个时点用。三者互不重叠，且都比主干长——留在主干会让每次调用都付出全量读取成本。

- [ ] **Step 1: 建 `symptom-hypothesis-map.md` 的征象映射表**

Create `references/symptom-hypothesis-map.md`，第一节逐字照录 spec § 3.2 的八行映射表：

````markdown
# 征象映射与路由

> 何时读这份：**定下征象、初始化台账那一轮**。台账建好后不必重读。

## 八类征象 → 合并后完整候选集

知识库有**两套征象命名**：dump 决策树 6 类、活体决策表 6 类，两套之间部分同义、部分互补。必须按下表映射，**不能把用户报的征象直接当成某一张表的行名**。

| 用户报的征象 | dump 表入口（候选数） | 活体表入口（候选数） | 合并后完整候选集 |
|---|---|---|---|
| 挂起 / 无响应 | `debugging-decision-tree.md § 1`（5，WPF 另加 2） | `live-monitoring-decision.md § 5` 线程池饥饿（2） | **7 条**（Monitor 死锁、异步死锁、线程池饥饿、长时间 GC 暂停、等待外部 I/O 无超时、同步阻塞异步、长任务占用工作线程）+ WPF 2 条 |
| 内存持续增长 | `§ 2`（4，WPF 另加 4 类形态） | `live-monitoring-decision.md § 2`（3） | **5 条**（托管对象泄漏、LOH 碎片化、非托管内存泄漏、加载器堆增长、分配压力非真实泄漏） |
| CPU 打满 | `§ 3`（4） | `live-monitoring-decision.md § 3`（3） | **4 条**（业务热点、自旋等待、GC 压力、无限循环） |
| 崩溃退出 | `§ 4`（4） | — | **4 条** |
| 间歇抖动 / 延迟尖峰 | `§ 5`（5） | `live-monitoring-decision.md § 1`（5） | **5 条**（GC 暂停、线程池注入延迟、锁竞争、外部 I/O 抖动、JIT 首次编译） |
| 句柄 / 资源耗尽 | `§ 6`（3） | — | **3 条** |
| 异常风暴 | — | `live-monitoring-decision.md § 4`（3） | **3 条** |
| 启动阶段慢 | — | `live-monitoring-decision.md § 6`（3） | **3 条** |

**八类征象**是对用户可见的统一命名（左列），十个小节是知识库的内部分布。以下三条规则消除落差：

1. **台账按「合并后完整候选集」初始化，不按单张表的候选集**——否则用户报「挂起」但只有 counters 数据时，Monitor 死锁将永无入口（该假设只在 dump 表列出）
2. 手里的证据类型只决定**当前能用哪些判据裁剪**，不决定台账里有哪些假设。证据不足以裁剪的假设停在 `待验`，并注明「需 <某类证据> 才能判定」
3. 合并后有重复语义的假设（如 dump 表「线程池饥饿」与活体表 § 5 整节）**合并为一条**，依据列同时挂两处 anchor

⚠️ 两张决策表的重叠**不是冗余**：「GC 暂停」「锁竞争」「线程池饥饿」「托管泄漏」在两表都出现，差别在取证手段——dump 表给单时点判据，活体表给「基线形态 / 异常形态 / 区分点」三元组。同一假设在两表对应不同裁剪算子，这是路由必须按二维定位的原因。
````

⚠️ **候选数与合并后条数必须逐字照 spec § 3.2**，不得凭印象重算。那张表是逐节核对知识库得出的实测结果，改动任一数字都会让台账初始化偏离（Task 4 的测例 5 专考「完整 7 条」）。

- [ ] **Step 2: 追加二维路由表与三个空格的处置**

Append to `references/symptom-hypothesis-map.md`：

````markdown

## 路由表：证据类型 × 征象

只写去向不写内容（知识库 README 认可的「固定映射」消费模式）：

| 征象 | 单时点证据（dump / SOS） | 时间序列证据（counters / trace） |
|---|---|---|
| 挂起 / 无响应 | `debugging-decision-tree.md § 1`（WPF 加挂 `wpf-dispatcher-deadlock.md § 3`） | `live-monitoring-decision.md § 5` |
| 内存持续增长 | `§ 2`（WPF 加挂 `wpf-leak-patterns.md § 1`） | `live-monitoring-decision.md § 2` |
| CPU 打满 | `§ 3` | `live-monitoring-decision.md § 3` |
| 崩溃退出 | `§ 4` | — |
| 间歇抖动 | `§ 5` | `live-monitoring-decision.md § 1` |
| 句柄 / 资源耗尽 | `§ 6` | — |
| 异常风暴 | `§ 4` 部分可用（见下） | `live-monitoring-decision.md § 4` |
| 启动阶段慢 | — | `live-monitoring-decision.md § 6` |

**三个「—」是知识库的真实形状，不是疏漏**：崩溃与句柄耗尽只有单时点判据；启动阶段只有趋势判据（`live-monitoring-decision.md § 6` 原文明示 dump 在该场景不可用，出路是 `--diagnostic-port` 反向连接）。命中空格时必须明确说「该组合无对应判据，需先换一类证据」，**不得硬塞不适用的入口**。

### 异常风暴格是「部分可用」，不是空格

`live-monitoring-decision.md § 4` 原文：「dump 只能看到抓取那一刻**当前未处理**的异常（`debugging-decision-tree.md § 4` 里 `!threads` 的 `Exception` 列），对已经被 `catch` 吞掉的异常没有任何痕迹留存」。据此拆分：

| 异常风暴的候选根因 | dump 能否覆盖 |
|---|---|
| 依赖不可用（持续抛出、未被吞） | ✅ 可用——`!threads` 的 `Exception` 列 + `sos-threads-and-stacks.md § 4. !pe` 展开 `InnerException` 链 |
| 参数校验失败风暴 | ✅ 同上 |
| 吞异常的重试循环（`catch` 后立即重试） | ❌ **天生盲**——吞掉的异常在抓取时刻已不存在于任何线程的当前异常状态 |

因此该格的正确话术是「dump 可证实前两类、**无法排除**第三类」——第三类须停在 `无法判定` 并注明需 first-chance 异常计数器（时间序列）才能判定，**不得因 dump 未见异常就报「无异常风暴」**。

## 路由是两跳而非一跳

上表右列不是终点。活体篇有 **6 条判据句**写成「→ 证实 X，**转** `sos-*.md § N`」形式（§1 两条、§3 两条、§4 一条、§5 一条），共指向 7 个第二跳目标。最长的一条是 `live-monitoring-decision.md § 5`：「证实线程池饥饿，转 `sos-locks-and-async.md § 3. !threadpool` 核对当前线程状态，**再转** `sos-threads-and-stacks.md § 2. !clrstack` 找出占用工作线程却卡在同步等待的调用栈」。

两条规则：

1. **第一跳定征象与候选集，第二跳才拿到可裁剪的判据**。路由表给的是第一跳；第二跳去向写在判据句里，须原样跟随，**不得停在第一跳就下结论**
2. ⚠️ **第二跳往往需要另一类证据**——SOS 命令篇要么读 dump、要么连活体进程。只有 counters 数据的用户走到第二跳会断链，此时该假设停在 `待验`，注明「时间序列已指向 X，确认需 `sos-*.md § N` 所需的 dump 或活体连接」。**这不是 `无法判定`**：证据方向已明确，只差最后一步取证，结论强度记为「推测」

## WPF 反查入口（与前向路由方向相反）

`wpf-leak-patterns.md § 6. 根链形态图鉴速查表` 是六行「根链末端标志物 → 泄漏类型」的反查表。**手里已有 `!gcroot` 输出但说不清征象的 WPF 场景，先走 § 6 反查表**，反查失败再回 § 1 常规起点（该表原文已给反查失败的出路）。
````

- [ ] **Step 3: 建 `evidence-precheck.md`**

Create `references/evidence-precheck.md`：

````markdown
# 证据可用性前置校验

> 何时读这份：**手里有 dump 或崩溃日志时**。仅有 counters / trace 数据或纯症状描述时不必读。

## A 组 · 路由所需（3 项，任何情况都要问）

| 清点项 | 取值 | 影响 |
|---|---|---|
| 手里有什么证据 | 命令输出 / dump 文件 / 崩溃日志 / 仅症状描述 | 决定能否进入判据裁剪 |
| 证据类型 | 单时点（dump / SOS 输出） / 时间序列（counters / trace 报告） | 决定用哪张表的判据裁剪（**不决定台账内容**） |
| 运行时 | .NET Framework 4.x / .NET 6+ / 未知 | 决定哪些判据适用 |

**运行时未知不阻塞**：按 `applies_to` 交集给通用判据，说明「若为 Framework 4.x 则以下第 N 条不适用」。二期活体篇全部标 `.NET 5+`，对 Framework 4.x 整章不适用。

⚠️ **A 组与官方 `dotnet-trace-collect` 的 6 项 Inputs 表不重叠**——官方问「采集前该用什么工具」（OS / admin / 部署形态 / 复现特征），这里问「手里这份证据够不够支撑分析」。后者官方压根不问，因为它抓完即停。

## B 组 · 三项硬校验（仅当手里有 dump 时）

这三项都是「不校验就会白做整轮分析」的坎：

| 校验项 | 判据来源 | 不校验的后果 |
|---|---|---|
| dump 位数与调试器是否匹配 | `dump-types-and-capability.md § 2. 位数必须匹配` | **静默失败**——不报错，只给出损坏的托管栈，极易误判为「dump 损坏」而重抓 |
| dump 类型是否支撑本次目标 | `dump-types-and-capability.md § 1. 四种类型的能力对照` | 用 Mini / Triage 查内存泄漏＝白做；OOM 崩溃须 Heap 或 Full（`debugging-decision-tree.md § 4` 末段） |
| 符号与 SOS 版本是否就位 | `symbols-and-tool-matching.md` 全篇四节 | 命令报错但原因在符号侧，会被误当成「命令不适用」 |

**任一项不满足时，先给补救路径（补符号 / 换调试器位数 / 重抓正确类型的 dump），不进入台账循环**——基于不可用证据的裁剪结论是假结论。

缺符号可降级分析的情形按 `symbols-and-tool-matching.md § 4. 缺符号时的降级读法` 判断：**结论只依赖托管栈时不必补符号**。

⚠️ 知识库入口篇 `debugging-decision-tree.md` 第 7 行显式要求：「命令报错先查 `reference/symbols-and-tool-matching.md`」。用户报「命令报错了 / 输出一堆错误」时**先查符号**，不要当成「证据不足」而降级结论强度。

## 崩溃日志的定位

崩溃日志既不是 SOS 输出也不是 dump，B 组三项对它不适用，而「业务日志不可解读」又把它排除在外——若不单独规定，它会成为「合法输入但无处可去」的一类。

| 是什么 | 能做什么 | 不能做什么 |
|---|---|---|
| .NET 未处理异常记录（异常类型 + 托管堆栈 + `InnerException` 链）、WER 记录的错误代码与故障模块 | ① 定征象为「崩溃退出」；② 按异常类型初筛——`debugging-decision-tree.md § 4` 首段把该征象拆为「未处理托管异常 / `StackOverflowException` / `OutOfMemoryException` / 原生代码崩溃」四支，日志里的异常类型直接对上其中一支；③ 借 `sos-threads-and-stacks.md § 4. !pe` 的 `InnerException` 链读法找根因异常层 | 裁剪任何依赖堆或线程状态的假设——日志无托管堆快照、无其余线程栈。这些假设必须停在 `待验` 并注明「需 § 4 所列 dump 才能判定」 |

⚠️ **`!pe` 那条判据只能借读法，不能声称命中**。其原文形态是 `InnerException` 非 `<none>` → 证实存在链式异常，而 `<none>` 是 SOS 输出的标记，日志文本里不存在。因此：
- 日志已完整打印异常链时，可据链末层定位
- 只打印了最外层时，须注明「可能存在未展开的内层异常」，**不得按最外层异常直接定根因**

**与「业务日志不可解读」的区分线**：含托管异常类型与堆栈帧的是崩溃日志（可用），只含业务语义文字（`用户登录失败`、`订单处理超时`）的是业务日志（不可用）。**同一个文件里两者混排时，只取异常记录段。**

## 仅有症状描述、无任何取证输出

**不进入台账循环。** 给出该征象需要什么证据（引用对应决策表的取证命令列），并明确告知取证由用户自行完成或转官方 `dump-collect` / `dotnet-trace-collect`。这是收窄后的硬边界。
````

- [ ] **Step 4: 建 `verdict-forms.md`**

Create `references/verdict-forms.md`：

````markdown
# 判据形态与修复方向分级

> 何时读这份：**每轮裁剪台账时**（判据形态），以及**出结论给修复方向时**（四档分级）。

## 判据的两种实际书写形态

这是台账关闭规则能否落地的前提。知识库中判据有两种形态，须同时识别：

| 形态 | 书写样式 | 分布 | 实测量 |
|---|---|---|---|
| **命令篇判据行** | 小节标题固定为 `### 判据：能证实 / 排除什么`，正文为 `<观察> → **证实**…` 或 `<观察> → **排除**…`（箭头 + 加粗，**无冒号**） | `sos-heap-and-objects.md`(13) / `sos-threads-and-stacks.md`(11) / `sos-locks-and-async.md`(8) / `wpf-leak-patterns.md`(10) / `wpf-dispatcher-deadlock.md`(9) | 51 处 |
| **决策表结论列** | 表格第三列的文字，如「全 0 → 排除 Monitor 死锁」「→ 证实线程池饥饿，转…」，**不加粗** | `debugging-decision-tree.md`(19 行) / `live-monitoring-decision.md`(11 行) | 30 行 |

⚠️ **带全角冒号的 `证实：` / `排除：` 在全域零命中**——引用判据时不要按该形态检索。

## 修复方向：转述而非自造

「给修复方向」若靠自行推理，会产出无出处的建议。知识库**已把跨领域修复 anchor 内嵌在判据句里**，正确动作是原样转述，不是自己找映射。

例如 `wpf-leak-patterns.md § 2` 的证实判据句末尾原文即为：「修复方向（跨领域引用）见 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`」。

覆盖不均，且引用出现的**位置**决定了能不能当修复方向用：

| 位置 | 分布 | 怎么用 |
|---|---|---|
| **判据句内**（`→ **证实** … 修复方向见 X`） | 共 6 处：`wpf-leak-patterns.md § 2`、`wpf-dispatcher-deadlock.md § 3`（证实长任务）、`§ 4`（证实互等闭环）、`sos-heap-and-objects.md § 2`（静态集合字段）、`sos-locks-and-async.md § 3`（证实线程池饥饿）、`sos-threads-and-stacks.md § 4`（UI 线程异常） | **原样转述该 anchor**，不改写、不替换为自己认为更合适的目标。此档最可靠——修复方向与被证实的假设一对一绑定 |
| **反查表格行内** | `sos-heap-and-objects.md § 4. !gcroot` 的根链形态表两行：静态字段 → `csharp/rules/06-memory-resource.md § 5. 静态引用`；事件 `_invocationList` → `§ 4. 事件与委托泄漏` | 与判据句内同等可靠——按根链末端形态一对一反查 |
| **小节末「下一步」段** | `wpf-leak-patterns.md § 3`（`wpf/rules/10-performance.md § 7` + `wpf/rules/03-mvvm.md § 7`）、`§ 5`（`wpf/rules/09-threading.md § 7`） | 同样原样转述，但须注明它对应**整节**而非某一条判据 |
| **文件导语或正文叙述段** | 五篇 reference 导语各一处（`clr-runtime-anatomy` / `sos-heap-and-objects` / `sos-locks-and-async` / `wpf-dispatcher-deadlock` / `wpf-leak-patterns`）；另 `clr-runtime-anatomy § 5`、`wpf-dispatcher-deadlock § 2` 为正文叙述 | ⚠️ **粒度太粗，只能作兜底**——导语引用的是整份 rules 文件或宽泛章节，用它回答「怎么修这条具体根因」会给出跑偏的指向 |
| 四档都没有 | 两张决策表与取证工具篇（`dump-capture` / `dotnet-counters` / `dotnet-trace` / `dump-types-and-capability` / `symbols-and-tool-matching`）全篇无跨领域引用 | 回落到 `dotnet-debugging/README.md` 的相邻领域划界表（三行：`csharp/rules/06-memory-resource.md § 4/§6/§9`、`csharp/rules/11-observability.md § 7`、`wpf/rules/12-exceptions-crash.md § 1–3`）。**该表也覆盖不到时，如实说「本领域未登记该根因的修复侧引用」，不自造 anchor** |

⚠️ **硬约束：修复方向只给 anchor 与一句话方向，不展开成修复方案。** 展开即越界到 `csharp-code-review` / `wpf-code-review` 的地盘（切线是「验尸 vs 预防」），也会复制那两个领域的正文。
````

- [ ] **Step 5: 校验三份文件的 anchor 逐字存在**

Run:
```bash
D=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/references
echo "=== 三份文件行数 ===" && wc -l $D/*.md
echo ""
echo "=== 被引用的知识库文件必须都存在 ==="
python -c "
import re, pathlib
kb = pathlib.Path('knowledge-base/dotnet-debugging')
refs = set()
for f in pathlib.Path('$D').glob('*.md'):
    refs |= set(re.findall(r'\`?([a-z0-9-]+\.md)', f.read_text(encoding='utf-8')))
known = {p.name for p in kb.rglob('*.md')}
missing = sorted(r for r in refs if r.endswith('.md') and r not in known and not r.startswith(('SKILL','README','CHANGELOG','golden','known-issues','symptom','evidence','verdict')))
print('引用到的知识库文件数:', len([r for r in refs if r in known]))
print('引用了但不存在的:', missing or '（无）')
"
echo ""
echo "=== 零命中形态必须没被误用 ==="
grep -c '证实：\|排除：' $D/*.md || echo "（全 0，正确）"
```

Expected:
- 三份合计 250-290 行
- 「引用了但不存在的」为空
- `证实：` / `排除：` 全角冒号形态 = **0**（唯一例外是 `verdict-forms.md` 里那句「带全角冒号的 `证实：` / `排除：` 在全域零命中」——它是**警告文本**，`grep` 会命中 1 次，属预期）

⚠️ **最后一条的预期是 `verdict-forms.md: 1`，另两份 `0`**。若另两份也命中，说明真的按零命中形态写判据了，必须改回 `→ **证实**` 箭头加粗形态。

- [ ] **Step 6: 抽查 5 处引用是否为「引用而非复制」**

Run:
```bash
D=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/references
echo "=== 每份文件最长的 5 行（复制正文的迹象是出现整段判据原文）==="
for f in $D/*.md; do
  echo "--- $(basename $f) ---"
  awk '{print length"\t"$0}' "$f" | sort -rn | head -3 | cut -c1-160
done
```

Expected: 最长的行都是**表格行**（含 `|` 分隔），且内容是「去向 + 一句话」形态，**不出现连续的判据正文段落**。

⚠️ 判断标准（spec 契约一）：写 anchor 与一句话概括是引用；把知识库某小节的判据逐条抄进来是复制。**表格里出现三条以上具体观察值与阈值**，就该回头改成只写 anchor。

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/references/symptom-hypothesis-map.md
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/references/evidence-precheck.md
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/references/verdict-forms.md
```

提交消息建议：
```
feat(devops-plugin): dotnet-diagnose-triage 三份 references 落地
```

⚠️ 不升 `plugin.json`（Task 7 统一升）。

---

## Task 3: SKILL.md 主干六节

**Files:**
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md`（填充 Task 1 立的六个占位标题）

**Interfaces:**
- Consumes: Task 1 的骨架与占位标题、Task 2 的三个 references（本任务要写「何时加载哪一份」）
- Produces: 完整的承载层主干。**Task 4 的七个测例逐条对应本任务落地的规则**；Task 5 的 agent 正文引用本 skill 的 `name`

**主干只留「每次都要用」的部分**（spec § 2.2）：台账规则、自检四项、三结论强度、九条失败处理、交接表、合规约束。征象映射表与路由表**不留在主干**——它们只在定征象那一轮用，已在 Task 2 下钻到 references。

- [ ] **Step 1: 填「假设台账」节**

Edit SKILL.md，把 `## 假设台账` 这一行替换为：

````markdown
## 假设台账

Markdown 表，随结论一并回传（本 skill 与调用它的 agent 都无跨调用状态，**台账即交接物**）。四个字段：

| 字段 | 内容 | 为什么这样设计 |
|---|---|---|
| 假设 | 候选根因，**逐字取自决策表** | 逐字才能反查回知识库条目；自创措辞会断开与判据的对应关系 |
| 状态 | `待验` / `已证实` / `已排除` / `无法判定` | `无法判定` 独立于 `已排除`——「证据不足」与「证据表明不是」是两件事 |
| 依据 | `file § anchor` + 命中的具体判据句 | 引用不复制；也是自检环节的取证对象 |
| 证据来源 | 用户提供的哪段输出 | 可追溯每条结论建立在哪份证据上 |

### 初始化

定下征象后，**该征象「合并后完整候选集」里每一条都进台账，状态一律 `待验`**。候选集见 `references/symptom-hypothesis-map.md`（此时加载它）。

不允许凭直觉预先淘汰，也不允许因当前证据类型不支持某假设就不登记——**台账的核心价值是把「没想到」与「想到了但排除了」区分开**。

### 关闭

只有命中知识库判据才能改状态（两种书写形态见 `references/verdict-forms.md`）：

- `已排除` 必须引用一条含 `→ **排除**` 的判据行，或决策表结论列中表述排除的单元格
- `已证实` 必须引用一条含 `→ **证实**` 的判据行，或决策表结论列中表述证实的单元格
- 两者都未命中 → 停在 `待验`，或转 `无法判定`

⚠️ **不允许靠推理关闭假设。** 这会让本 skill 显得啰嗦（不能替用户跳步），是有意取舍。

### 出口条件

| 台账状态 | 出口 |
|---|---|
| 恰好一条 `已证实` | 收敛，给修复方向（按 `references/verdict-forms.md` 的四档分级转述，**不自造 anchor**） |
| 全部 `已排除` / `无法判定` | 宣告「本征象候选集已穷尽」，给三条出路（见「失败处理」） |
| 多条 `已证实` | **不强行择一**，如实并列，说明多因并存 |

多因并存在真实排查中常见（GC 压力 + 锁竞争经常同时命中），**强行择一是误报来源**。

### 跨轮续用（二次调用语义）

输入中带上一轮台账时：`已证实` / `已排除` 状态**保留**，只对 `待验` / `无法判定` 项用新证据继续裁剪。**禁止重新按「初始化」全量重建**——那会抹掉上轮结论并重复已做过的裁剪。

⚠️ 唯一例外：新证据与上轮某条 `已排除` 结论矛盾时，该项**重开为 `待验`** 并注明矛盾来源。这是唯一允许翻转已关闭假设的情形。

**输出末尾必须固定附交接块**：台账原文 + 一句「继续排查请把以下台账连同新证据一并提供」。缺此块则跟轮必然丢失状态——调用方读不到本 skill 的中间推理，只能读到输出文本。
````

- [ ] **Step 2: 填「出结论前的自检」与「三种结论强度」两节**

Edit SKILL.md，把 `## 出结论前的自检` 与 `## 三种结论强度` 两行替换为：

````markdown
## 出结论前的自检

四项逐条自答，**不通过不得出结论**：

| 自检项 | 不通过时 |
|---|---|
| 每条 `已证实`/`已排除` 是否都挂着 `file § anchor` 与命中的判据句？ | 退回 `待验`，说明缺哪条证据 |
| 结论有没有超出证据？ | 降级为「推测」，标出还需哪类证据 |
| 台账里 `待验` 的假设有没有被无声跳过？ | 显式列出未验项 |
| 运行时适用性核对过没有？（`applies_to` 是否覆盖目标运行时） | 撤下不适用的判据 |

**第二项是重心。** 诊断最典型的失败模式不是查错方向，而是**证据只够支撑「可能是」，却报成了「就是」**。

**第三项防「报喜不报忧」**：找到一条证实项就收工、台账剩余 `待验` 悄悄消失。漏报比误报更难被发现。

## 三种结论强度

必须显式标出，不得含糊：

| 强度 | 判定 |
|---|---|
| **已确认** | 命中某条含 `→ **证实**` 的判据（或决策表相应结论列），且该判据前置条件全部满足 |
| **推测** | 证据方向一致但判据未完整命中，**须写明还缺哪类证据** |
| **超出覆盖** | 知识库无对应判据（非托管泄漏细节、Linux 容器专属＝未入库、`AssemblyLoadContext` 卸载＝已登记缺口、NativeAOT＝全域未覆盖） |

⚠️ **结论末尾固定附免责声明**：诊断结论由 AI 生成、具非确定性，可能误报或漏报，投入修复前须人工复核。

理由不是形式合规——**诊断结论会驱动生产环境的修复动作，其错误代价高于代码审查建议**。
````

- [ ] **Step 3: 填「失败处理」节（九条）**

Edit SKILL.md，把 `## 失败处理` 一行替换为：

````markdown
## 失败处理

| 触发条件 | 一线处理 |
|---|---|
| 只给一句「程序崩了」，无任何证据 | 不猜。按 `references/evidence-precheck.md` 给出该征象所需证据，指向官方采集 skill 或本知识库 Framework 路径 |
| 粘的输出不是取证输出（纯业务日志：只有 `用户登录失败` 这类业务语义文字，无异常类型与堆栈帧） | 明确说明不可解读，指出该取哪类证据。**先按崩溃日志的区分线判一次**——含托管异常类型与堆栈帧的属崩溃日志，可用，不得一并判为不可解读 |
| 输出被截断 | 基于可见部分给方向，标「基于截断输出」，说明完整输出能多排除哪些假设 |
| 征象与证据矛盾（说内存涨但托管堆很小） | 不迁就描述，**指出矛盾即线索**——转非托管泄漏路径 |
| 症状不属八类征象任一 | 如实说超出覆盖，**不硬套最像的一类** |
| 台账全排除但问题仍在 | 宣告候选集穷尽，给三条出路：换征象 / 换证据类型 / 超出知识库范围 |
| 第一跳已证实但第二跳缺证据（如只有 counters，判据句要求转 `sos-*.md`） | 停在 `待验`，强度记「推测」，注明「时间序列已指向 X，确认需 `sos-*.md § N` 所需的 dump 或活体连接」。**不得记 `无法判定`**——方向已明确，只差最后一步取证 |
| 用户报「命令报错了 / 输出一堆错误」 | **先查符号与工具匹配**（`symbols-and-tool-matching.md` 四节），不要当成「证据不足」而降级结论强度——报错原因多在符号或 SOS 版本侧，与假设裁剪无关。这是知识库入口篇 `debugging-decision-tree.md` 第 7 行的显式要求 |
| 用户要求直接抓 dump 或跑 trace | 不执行，转官方 skill 或回落本知识库（见「与官方产物的交接」），并一并给出处置合规约束 |

⚠️ 「症状不属八类征象任一」那条是最大的诱惑点。八类征象覆盖不了所有现场（如「启动就闪退」既非崩溃退出也非启动阶段慢），**套近似入口会让整条推理链建立在错误的候选集上，比直接说「不覆盖」更有害**。
````

- [ ] **Step 4: 填「与官方产物的交接」与「dump 处置合规」两节**

Edit SKILL.md，把最后两个占位标题替换为：

````markdown
## 与官方产物的交接

需要新证据时，动作是**给出取证要求并指明去向，自己不执行**：

| 需要什么 | 交接去向 |
|---|---|
| dump 文件（modern .NET） | 官方 `dump-collect` skill；**官方插件未安装或用户不便使用时，无条件回落**到本知识库 `dump-capture.md § 2. dotnet-dump collect` / `§ 3. createdump` / `§ 5. DOTNET_DbgEnableMiniDump` |
| trace / counters 数据 | 官方 `dotnet-trace-collect` skill；未安装时回落到本知识库 `dotnet-counters.md` / `dotnet-trace.md` |
| dump 文件（.NET Framework 4.x） | 官方两者均不支持 Framework，只能引用本知识库 `dump-capture.md § 1. procdump` 与 `§ 4. WER LocalDumps` |

⚠️ **回落不是降级路径，是默认可用路径。** 官方插件是「若已安装则优先推荐」，而非前置依赖——本知识库 `dump-capture.md` 五节完整覆盖 procdump / dotnet-dump / createdump / WER / `DOTNET_DbgEnableMiniDump`，无官方插件亦可给出完整抓取指引。

**划界只能单向生效**：官方 `dump-collect` 的 Stop Signals 只说「本 skill 不覆盖分析」，不会指向任何替代产物——「用户在官方那边被拒后转到我们这里」这条路不存在。可控的只有反向：用户找到我们、但需求属于取证侧时，由我们指回官方。

## dump 处置合规

不执行抓取，但**只要建议用户去抓 dump，就须在同一条回复内一并给出处置约束**——dump 抓完再谈密级已经晚了。

三条按级别区分，**不可把 SHOULD 说成 MUST**：

| 约束 | 级别 | 内容 |
|---|---|---|
| `rules/01-dump-handling.md § 1. 生产 dump 的密级` | **MUST** | 生产 dump 含完整进程内存（连接字符串、令牌、用户数据），须按其密级处置；禁止随手发送至外部渠道 |
| `§ 2. 版本库隔离` | **MUST** | dump 不得落进 git 工作树，建议路径必须在仓库外 |
| `§ 4. 留存期限与销毁` | **MUST** | 分析结束后按留存期限销毁，不长期堆放 |
| `§ 3. 对外交付的类型选择` | SHOULD | 需对外交付时优先选能力足够的最小类型 |
| `§ 5. 自动抓取的落盘位置` | SHOULD | 配置自动抓取时落盘位置的选择建议 |
````

- [ ] **Step 5: 校验主干结构与「不该留在主干」的内容确实不在**

Run:
```bash
F=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md
echo "=== 二级标题（应 7 个）===" && grep -n '^## ' "$F"
echo ""
echo "=== 行数（预期 150-200）===" && wc -l "$F"
echo ""
echo "=== 三份 references 都被写明加载时机 ==="
for r in symptom-hypothesis-map evidence-precheck verdict-forms; do
  printf '%-26s' "$r"; grep -c "$r" "$F" || true
done
echo ""
echo "=== 主干不应含征象映射表与路由表（progressive disclosure 的落点判据）==="
for kw in '合并后完整候选集' '二维' '启动阶段慢' 'live-monitoring-decision.md § 6'; do
  printf '%-32s' "$kw"; grep -c "$kw" "$F" || true
done
echo ""
echo "=== 九条失败处理 ==="
sed -n '/^## 失败处理/,/^## /p' "$F" | grep -c '^| ' || true
```

Expected — 二级标题恰这 7 个，按此顺序：

```
## 概述
## 假设台账
## 出结论前的自检
## 三种结论强度
## 失败处理
## 与官方产物的交接
## dump 处置合规
```

- 行数 150-200
- 三份 references 各被提及 ≥ 1 次
- **四个「不该在主干」的关键词各 = 0**（`合并后完整候选集` 一处例外：「初始化」节引用该概念时会提到，允许 ≤ 1）
- 失败处理表行数 = **11**（表头 + 分隔行 + 9 条）

⚠️ **若征象映射表的内容出现在主干**，说明 progressive disclosure 没做到——那张表 40+ 行，留在主干会让每次调用都读一遍。**回头搬去 `references/symptom-hypothesis-map.md`**（Task 2 已建好，直接删主干副本即可）。

- [ ] **Step 6: 跑 darwin-skill 基线评估**

Run:
```bash
/darwin-skill plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage
```

（或按 darwin-skill 的实际调用方式；它是本仓 `.claude/skills/` 下的维护型 skill。）

记录：**总分 + 9 个维度各自得分 + 评估模式**（`full_test` 或 `dry_run`）。

🔴 **CHECKPOINT — 新建 skill 无「改动前分数」可比，因此不设通过门槛；但基线分过低（rubric 明显缺项）时先修再进入 Step 7。** 判据：某个维度得 0 分说明该维度对应的结构整节缺失，不是「写得不够好」而是「没写」。

- [ ] **Step 7: 建 CHANGELOG / README / known-issues**

Create `.../dotnet-diagnose-triage/CHANGELOG.md`：

```markdown
## [1.0.0] - 2026-09-06

### Added
- 新建 skill：`knowledge-base/dotnet-debugging/` 的首个消费者，承载假设台账消解循环
- 主干六节：假设台账（四字段 / 初始化 / 关闭 / 出口 / 跨轮续用）、自检四项、三结论强度、九条失败处理、与官方产物的交接、dump 处置合规
- `references/` 三份按下钻频次分文件：`symptom-hypothesis-map.md`（征象映射 + 二维路由 + 第二跳）、`evidence-precheck.md`（A/B 两组清点 + 崩溃日志定位）、`verdict-forms.md`（判据两形态 + 修复方向四档）
- `test-cases/golden.md` 七个黄金测例
```

Create `.../dotnet-diagnose-triage/known-issues.md`（照本仓既有格式，见 `plugins/optimus-decision-plugin/skills/backtracking-algorithm-template/known-issues.md`）：

```markdown
# dotnet-diagnose-triage · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

## darwin-skill 基线评估（2026-09-06）

| 项 | 值 |
|---|---|
| 总分 | <Step 6 实测分数> |
| 评估模式 | <full_test 或 dry_run> |
| 各维度得分 | <9 维逐项，格式照 darwin-skill 输出> |
| 判读 | 新建 skill 基线，无历史分可比；后续 Minor/Major 升级须 ≥ 本分数 |

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| — | 暂无记录 | — | — | — |
```

⚠️ **`known-issues.md` 必须写「评分依据与评估模式」，不能只写一个分数**（spec § 10.3）。`dry_run` 与 `full_test` 的分数不可直接比较，不注明模式会让后续门禁比对失去意义。

Create `.../dotnet-diagnose-triage/README.md` — 六章节，全 ASCII box-drawing，范式见 `plugins/optimus-decision-plugin/skills/complexity-analysis/README.md`：

- **标题与元信息**：`# dotnet-diagnose-triage` + `> 版本：1.0.0 | 分类：quality` + 一句话
- **所处层级**：quality 层，标出 `★ dotnet-diagnose-triage`，上游是 `dotnet-diagnose` agent（调用方），横向相邻是 `csharp-code-review` / `wpf-code-review`（切线：验尸 vs 预防）
- **触发词 / 内部触发条件**：抄 frontmatter description 的触发词段
- **业务逻辑流程图**：Step 1 证据清点 → Step 2 定征象 + 初始化台账 + 路由 → Step 3 裁剪 + 自检 + 出结论
- **产出物数据流**：取证输出（dump / SOS / trace / 崩溃日志）→ 本 skill → 台账 + 带强度标注的结论 + 修复方向 anchor + 交接块 → 人工接手
- **Skill 依赖关系图**：被 `dotnet-diagnose` agent 加载；读取 `knowledge-base/dotnet-debugging/`；建议取证时指向官方 `dump-collect` / `dotnet-trace-collect`

⚠️ **README 头部版本号必须与 `CHANGELOG.md` 最新条目及 `metadata.version` 三处一致**，均为 `1.0.0`。

- [ ] **Step 8: 校验三份配套文档**

Run:
```bash
D=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage
echo "=== 三处版本号必须一致（都是 1.0.0）==="
grep -o 'version: "[^"]*"' $D/SKILL.md
grep -o '^## \[[0-9.]*\]' $D/CHANGELOG.md | head -1
grep -o '版本：[0-9.]*' $D/README.md
echo ""
echo "=== README 六章节 ===" && grep -n '^## ' $D/README.md
echo ""
echo "=== README 无 Mermaid、无图片 ==="
grep -c 'mermaid\|!\[' $D/README.md || echo "（全 0，正确）"
echo ""
echo "=== known-issues 含评估模式 ==="
grep -c 'full_test\|dry_run' $D/known-issues.md || true
```

Expected:
- 三处版本号全为 `1.0.0`
- README 六个二级标题（标题与元信息不是二级标题，故这里是 5 个 `## ` + 一级标题）
- Mermaid / 图片 = **0**
- known-issues 含评估模式 ≥ 1

- [ ] **Step 9: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/CHANGELOG.md
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/README.md
plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/known-issues.md
```

提交消息建议：
```
feat(devops-plugin): dotnet-diagnose-triage 主干六节与配套文档
```

⚠️ 不升 `plugin.json`（Task 7 统一升）。

---

## Task 4: 七个黄金测例

**Files:**
- Create: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/test-cases/golden.md`
- Read (不改): `knowledge-base/dotnet-debugging/reference/sos-locks-and-async.md`（核对 `MonitorHeld` 编码规则等列名语义）

**Interfaces:**
- Consumes: Task 2 的三份 references、Task 3 的主干六节（测例考的正是这些规则）
- Produces: 可逐例人工跑的行为验收集。**Task 8 的 Step 1 就是跑这七例**——它是本次交付唯一验「诊断对不对」的手段

**为什么需要这个**：仅验「结构齐备」的验收标准，无法阻止「skill 写得漂亮但诊断结论是错的」。本任务把结构验收转化为可验证的行为目标。

**放在 skill 层而非 agent 层**：测例考的全是判据引用、台账裁剪、前置校验——这些内容都在 skill 与其 `references/` 里，测例与被测内容同目录才不会失联。

- [ ] **Step 1: 核对测例引用的列名与语义逐字取自知识库**

Run:
```bash
KB=knowledge-base/dotnet-debugging/reference
echo "=== MonitorHeld 编码规则原文（测例 1 依赖）==="
grep -n -B2 -A4 'MonitorHeld' $KB/sos-locks-and-async.md | head -30
echo ""
echo "=== !dumpheap -stat 两次对比的判据原文（测例 2 依赖）==="
grep -n -A3 'dumpheap' $KB/sos-heap-and-objects.md | head -20
echo ""
echo "=== wpf-leak-patterns § 1 的排除判据范围限定（测例 4 依赖）==="
sed -n '/^## 1\./,/^## 2\./p' $KB/wpf-leak-patterns.md | grep -n '排除' | head -10
echo ""
echo "=== debugging-decision-tree § 4 首段的四支（测例 7 依赖）==="
sed -n '/^## 4\./,/^## 5\./p' $KB/debugging-decision-tree.md | head -12
```

Expected: 四段输出都有实际内容，且与 spec § 9.2 各测例的预期结果吻合。

🔴 **CHECKPOINT — 输出片段的列名与语义必须与知识库正文一致，不得自造列名。** 若某段 grep 无输出（如 `MonitorHeld` 查不到），说明知识库该处措辞与 spec 记录不符——**先停下核对，再决定是改测例还是改 spec 记录**。测例的价值全在「预期结果可反查回知识库」，自造列名会让整份测例失效。

- [ ] **Step 2: 建 golden.md 骨架与前三例**

Create `test-cases/golden.md`：

````markdown
# dotnet-diagnose-triage 黄金测例

七例，每例四段：**输入** / **预期台账** / **预期结论强度** / **考什么**。

**跑法**：把「输入」段原样作为 prompt 提供给 `dotnet-diagnose` agent（或直接调用本 skill），比对实际输出的台账状态与结论强度是否与预期一致。**不符即为不通过**，回头修 SKILL.md 或 references，不改测例预期。

⚠️ 输出片段的列名与语义逐字取自知识库正文（如 `MonitorHeld` 编码规则取自 `sos-locks-and-async.md § 1`），**不得自造列名**。

---

## 测例 1 · Monitor 死锁（判据加粗形态 + 编码规则）

**输入**：「界面卡死」+ `!syncblk` 显示两个同步块，`MonitorHeld` 分别为 3、3，两个 `Owning Thread Info` 互为对方的等待方。

**预期台账**：「Monitor 死锁」→ `已证实`，依据挂 `sos-locks-and-async.md § 1` 并附命中的判据句。

**预期结论强度**：**已确认**。

**考什么**：能否读懂 `MonitorHeld` 的编码（等待线程数 =（值−1）/2）并识别循环等待。这是命令篇「箭头 + 加粗」判据形态的典型。

---

## 测例 2 · 单份 dumpheap 不足以判「持续增长」

**输入**：「内存一直涨」+ **单份** `!dumpheap -stat` 显示某业务类型 Count 很高。

**预期台账**：该假设停在 `待验` 或 `无法判定`，**注明需第二次采样**。

**预期结论强度**：**推测**，**不得报已确认**。

**考什么**：自检第二项「结论不得超出证据」。`sos-heap-and-objects.md § 1` 的判据明确要求两次 `-stat` 对比，单时点数据只能说明「某类型实例多」，不能说明「在增长」。

---

## 测例 3 · WPF Binding 泄漏（修复方向原样转述）

**输入**：WPF 应用「窗口关不掉」+ `!gcroot` 输出根链末端落在 `MS.Internal.Data` 命名空间的事件管理器。

**预期台账**：「Binding 泄漏」→ `已证实`，依据挂 `wpf-leak-patterns.md § 2`。

**预期结论强度**：**已确认**，且修复方向**原样转述**该判据句自带的 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`——**不改写为其他目标、不展开成修复方案**。

**考什么**：WPF 分支路由 + 修复方向第一档「判据句内引用原样转述」。这是本产物相对官方 `dump-collect` 的独有价值（官方全无 WPF 内容）。

---
````

- [ ] **Step 3: 追加测例 4-5**

Append to `test-cases/golden.md`：

````markdown

## 测例 4 · 排除判据不得越界（三期最终审查那处 Important）

**输入**：「内存一直涨」+ 全部 WPF 类型实例数均在预期内。

**预期台账**：排除 `wpf-leak-patterns.md` § 2 / § 3 / § 5 三类；**§ 4 弱事件泄漏必须仍为 `待验`**，并注明需另按内部监听表体积判断。

**预期结论强度**：无收敛结论，如实报「候选集未穷尽，§ 4 待验」。

**考什么**：`wpf-leak-patterns.md § 1` 的排除判据已显式限定范围——「全部 WPF 类型实例数正常」不足以排除弱事件泄漏（该类泄漏体现在内部监听表体积而非类型实例数）。**越界排除会漏掉真实根因**，这是三期最终审查提出的那处 Important 的落地检验。

---

## 测例 5 · 合并候选集初始化 + 第二跳断链

**输入**：「挂起」+ 只有 `dotnet-counters` 时间序列数据，显示队列长度持续 > 0、线程数顶在爬坡上限、CPU 不高。

**预期台账**：
1. 台账须含**完整 7 条**候选（含只在 dump 表出现的 Monitor 死锁）——不因当前只有 counters 数据就少登记
2. 「线程池饥饿」命中 `live-monitoring-decision.md § 5` 第一跳，但该判据句要求转 `sos-locks-and-async.md § 3` 再转 `sos-threads-and-stacks.md § 2`——**无 dump、无活体连接，第二跳断链**，故停在 `待验`
3. **不得记 `无法判定`**

**预期结论强度**：**推测**，注明「时间序列已指向线程池饥饿，确认需 `sos-locks-and-async.md § 3` 所需的 dump 或活体连接」。

**考什么**：征象映射三条规则中的 1/2（合并候选集初始化 + 证据类型不决定台账内容）+ 第二跳断链的正确降级。⚠️ **这是最容易做错的一例**——两个常见错误是「只登记活体表的 2 条候选」和「把断链记成 `无法判定`」。

---
````

- [ ] **Step 4: 追加测例 6-7 与覆盖对应表**

Append to `test-cases/golden.md`：

````markdown

## 测例 6 · dump 类型不支撑目标（B 组前置校验）

**输入**：「程序崩了」+ 提供一个 Mini 类型 dump，目标是查内存泄漏。

**预期台账**：**不进入台账循环**——不初始化任何假设。

**预期结论强度**：不出诊断结论。先报 dump 类型不支撑该目标（`dump-types-and-capability.md § 1. 四种类型的能力对照`），给出重抓 Heap / Full 的补救路径。

**考什么**：B 组证据可用性前置校验。不校验就整轮白做——Mini dump 无完整堆信息，基于它的任何泄漏结论都是假结论。

---

## 测例 7 · 崩溃日志的可用边界

**输入**：「程序自动退出」+ 一份日志，含 `System.InvalidOperationException` 的类型名与三帧托管堆栈，另混有若干条 `订单处理超时` 业务行。

**预期台账**：
1. **只取异常记录段**，业务行不参与判断
2. 定征象「崩溃退出」，按 `debugging-decision-tree.md § 4` 首段四支对上「未处理托管异常」
3. 日志只打印了最外层异常，须注明「可能存在未展开的内层异常」，**不得按最外层直接定根因**
4. 依赖堆或其余线程栈的假设一律停在 `待验`，注明「需 § 4 所列 dump 才能判定」

**预期结论强度**：**推测**（不得为已确认——`!pe` 判据只借了读法，未真正命中）。

**考什么**：崩溃日志与业务日志的区分线 + `!pe` 判据「只能借读法不能声称命中」。⚠️ `!pe` 原文判据形态是 `InnerException` 非 `<none>` → 证实链式异常，而 `<none>` 是 SOS 输出标记，日志文本里不存在该标记。

---

## 覆盖对应关系

| 被考的设计要素 | 覆盖测例 |
|---|---|
| 判据两种书写形态 | 1（命令篇加粗形态）、5（决策表结论列形态） |
| 台账按合并候选集初始化 | 5 |
| 三种结论强度 | 1（已确认）、2 与 5 与 7（推测） |
| 自检第二项「结论不得超出证据」 | 2、4、7 |
| 修复方向原样转述 | 3 |
| 第二跳断链的降级 | 5 |
| 崩溃日志的可用边界 | 7 |
| B 组证据可用性前置校验 | 6 |
| WPF 分支与跨领域修复引用 | 3、4 |

⚠️ **未被任何测例覆盖的设计要素**（如跨轮续用语义、九条失败处理中的六条、dump 处置合规话术）**按结构验收**，见实施计划 Task 8 的验收清单。测例只覆盖「结构齐备但可能算错」的部分。
````

- [ ] **Step 5: 校验测例结构齐备**

Run:
```bash
F=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/test-cases/golden.md
echo "=== 测例数（应 7）===" && grep -c '^## 测例 ' "$F"
echo ""
echo "=== 每例四段（应 7×4 = 28）==="
grep -c '^\*\*输入\*\*\|^\*\*预期台账\*\*\|^\*\*预期结论强度\*\*\|^\*\*考什么\*\*' "$F"
echo ""
echo "=== 引用的知识库 anchor 都存在 ==="
python -c "
import re, pathlib
kb = {p.name for p in pathlib.Path('knowledge-base').rglob('*.md')}
t = pathlib.Path('$F').read_text(encoding='utf-8')
refs = set(re.findall(r'\`([a-z0-9-]+\.md)', t))
missing = sorted(r for r in refs if r not in kb)
print('引用的知识库文件:', len(refs - set(missing)))
print('不存在的:', missing or '（无）')
"
echo ""
echo "=== 行数 ===" && wc -l "$F"
```

Expected:
- 测例数 = **7**
- 四段标记 = **28**
- 不存在的引用 = 无
- 行数 130-170

⚠️ 若四段标记不是 28，说明某例漏了一段——**逐例核对**，不要靠总数猜是哪一例。

- [ ] **Step 6: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅 `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/test-cases/golden.md`。

提交消息建议：
```
test(devops-plugin): dotnet-diagnose-triage 七个黄金测例
```

⚠️ 不升 `plugin.json`（Task 7 统一升）。**测例此时只是交付物，Task 8 才逐例跑。**

---

## Task 5: agent 本体与 `agents` 声明（含加载实测 CHECKPOINT）

**Files:**
- Create: `plugins/optimus-devops-plugin/agents/dotnet-diagnose.md`（**纯 `.md`，非 `.agent.md`**，≤ 80 行）
- Modify: `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`（增补 `agents` 字段）

**Interfaces:**
- Consumes: Task 1-4 落地的 skill（agent 正文要写「加载 `optimus-devops-plugin:dotnet-diagnose-triage`」，skill 不存在则那句话无处落）
- Produces: 本仓首个可调用 agent。**Task 6 的 agent-docs README 要抄 agent 的调用名与 description 触发面**；Task 8 的黄金测例通过它调用

**为什么 agent 层仍不可省**（spec § 2.3）：独立上下文提供「不受主对话推理污染的第二双眼睛」，这正是自检环节所需的性质。若只建 skill，自检与推理在同一上下文里进行，自检会倾向于确认已得结论。

⚠️ **本任务是全计划风险最高的一个**——本仓首个 agent，加载机制此前只在探针插件上验证过。Step 5 是 go / no-go CHECKPOINT。

- [ ] **Step 1: 记录改动前的 plugin.json 与官方 agent 体量参照**

Run:
```bash
echo "=== devops 两份 plugin.json 现状 ==="
cat plugins/optimus-devops-plugin/.claude-plugin/plugin.json
python -c "
import json
d=json.load(open('plugins/optimus-devops-plugin/.codex-plugin/plugin.json',encoding='utf-8'))
print('codex version:', d['version'])
print('capabilities:', d['interface']['capabilities'])
"
echo ""
echo "=== 校验脚本当前状态（应 PASS）==="
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
echo ""
echo "=== agents/ 目录当前应不存在 ==="
ls plugins/optimus-devops-plugin/agents/ 2>&1 | head -2
```

Expected:
- 两份 `version` 均为 `1.0.0`，校验 PASS
- `capabilities` 为 `["Skills"]`
- `agents/` 目录不存在

**体量参照**：官方 `optimizing-dotnet-performance.agent.md` 仅 **63 行**——它把深度内容甩给 `analyzing-dotnet-performance` skill，`tools` 因此列了 `'task'` 与 `'skill'`。本 agent 的 ≤80 行目标以此为准。

- [ ] **Step 2: 创建 agent 本体的 frontmatter**

Create `plugins/optimus-devops-plugin/agents/dotnet-diagnose.md`：

````markdown
---
name: dotnet-diagnose
description: 解读 .NET 取证输出并定位根因：SOS 命令输出逐列解读、假设台账消解、WPF 专属归因（Dispatcher 死锁与四类泄漏堆形态）、.NET Framework 4.x 分析。用于已经拿到 dump / SOS 输出 / trace 报告之后。若只需配置或抓取 dump、选择采集工具，用 dump-collect 或 dotnet-trace-collect（本 agent 不执行取证命令）。
tools: ['read', 'search', 'skill', 'Read', 'Glob', 'Grep', 'Skill', 'read_file', 'glob', 'grep_search']
---
````

⚠️ **恰三字段，一个不多**：
- **不写 `license`**——它不在官方插件 agent 的 11 字段合法清单（`name`/`description`/`model`/`effort`/`maxTurns`/`tools`/`disallowedTools`/`skills`/`memory`/`background`/`isolation`）内。官方 `dotnet-diag` 的 agent 写了 `license: MIT` 属越界，只是 `validate` 不检查未知键而已
- **不写 `metadata`**——同一份清单里也不含它（与 skill 不同：skill 有 agentskills.io 规范明确留出的 `metadata` 自由映射）。agent 版本号记在 Task 6 的 `agent-docs/dotnet-diagnose/CHANGELOG.md`
- **不写 `model` / `effort` / `maxTurns` / `disallowedTools` / `skills` / `memory` / `background` / `isolation`**——这 8 项虽在合法清单内，但均为 Claude 侧独有，写了即产生两侧能力不对等
- **`hooks` / `mcpServers` / `permissionMode` 三字段插件 agent 不支持**（官方明示的安全限制），别尝试

⚠️ **`tools` 必须含 skill 加载能力**（`'skill'` / `'Skill'`）——承载层在 skill 里，无此能力则 agent 读不到判据表。同时**不含任何写入或执行工具**（无 `Write` / `Edit` / `Bash`）：收窄后不执行诊断命令、不修改文件。**因此台账不落文件，只能靠输出自带交接块跟轮。**

⚠️ **`tools` 列跨 harness 别名**是官方做法——同一能力两侧工具名不同（Claude 侧 `Read`/`Glob`/`Grep`/`Skill`，Codex 侧 `read`/`search`/`skill`/`read_file`/`glob`/`grep_search`）。

- [ ] **Step 3: 写 agent 正文（三步主干 + 加载时机 + 边界 + 输出格式）**

Append to `agents/dotnet-diagnose.md`：

````markdown

# .NET 取证输出解读与根因定位

## 我做什么

读懂已经拿到的证据（dump / SOS 输出 / trace 报告 / 崩溃日志），按知识库判据裁剪候选根因，给出带出处与强度标注的结论。

**我不做**：不抓 dump、不选采集工具、不执行任何命令。这一半由微软官方 `dump-collect` / `dotnet-trace-collect` 覆盖且更完备（含容器与 K8s 适配）。

## 主干三步

```
Step 1  证据清点（轻量，仅分析所需）
Step 2  定征象 → 初始化台账 → 路由到判据篇目
Step 3  按判据裁剪台账 → 自检 → 出结论（含台账与下一步）
```

## 何时加载承载 skill

**Step 1 之后、进入 Step 2 之前**，用 Skill 工具加载 `optimus-devops-plugin:dotnet-diagnose-triage`。

它承载全部判据规则：台账四字段与关闭规则、自检四项、三结论强度、九条失败处理、与官方产物的交接表、dump 处置合规。其 `references/` 三份按需下钻：

| 何时下钻 | 读哪份 |
|---|---|
| 定下征象、初始化台账那一轮 | `references/symptom-hypothesis-map.md` |
| 手里有 dump 或崩溃日志 | `references/evidence-precheck.md` |
| 每轮裁剪台账、以及出结论给修复方向 | `references/verdict-forms.md` |

⚠️ **判据表不写在本文件内。** 我只负责编排与输出格式，判据的唯一出处是上面那个 skill 与它引用的 `knowledge-base/dotnet-debugging/`。

## 边界

| 情形 | 我的动作 |
|---|---|
| 仅有症状描述、无任何取证输出 | 不进入台账循环。说明该征象需要什么证据，指向官方采集 skill 或本知识库 Framework 路径 |
| 用户要我抓 dump / 跑 trace | 不执行。转官方 skill 或回落本知识库，**并在同一条回复内给出 dump 处置合规约束** |
| 症状不属八类征象任一 | 如实说超出覆盖，**不硬套最像的一类** |
| 知识库无对应判据 | 标为「超出覆盖」（非托管泄漏细节、Linux 容器专属、`AssemblyLoadContext` 卸载、NativeAOT） |

## 输出格式

每次输出固定四段，顺序不可变：

1. **结论**（含三种强度之一：已确认 / 推测 / 超出覆盖）与其 `file § anchor` 出处
2. **修复方向**：只给 anchor 与一句话方向，**不展开成修复方案**（展开即越界到 `csharp-code-review` / `wpf-code-review` 的地盘）
3. **台账交接块**：台账原文 + 一句「继续排查请把以下台账连同新证据一并提供」
4. **免责声明**：诊断结论由 AI 生成、具非确定性，可能误报或漏报，投入修复前须人工复核

⚠️ **第 3 段不可省。** 我无跨调用状态，调用方读不到我的中间推理——**台账的延续必须由输出自身携带**，缺此块则跟轮必然丢失状态。

⚠️ **二次调用是「续用」不是「重新初始化」**：输入中带上一轮台账时，`已证实` / `已排除` 状态保留，只对 `待验` / `无法判定` 项用新证据继续裁剪。唯一例外是新证据与某条 `已排除` 矛盾时，该项重开为 `待验` 并注明矛盾来源。
````

- [ ] **Step 4: 增补 `.claude-plugin/plugin.json` 的 `agents` 字段**

Edit `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`，改为：

```json
{
  "name": "optimus-devops-plugin",
  "version": "1.0.0",
  "agents": ["./agents/dotnet-diagnose.md"]
}
```

⚠️ **`version` 此步保持 `1.0.0` 不动**——Task 7 统一升到 `1.1.0`（两份同时改，避免中间态被 `check_plugin_versions.py` 判为不一致）。

⚠️ **只写文件路径，不写目录**。实测目录形态 `["./agents/"]` 被 `claude plugin validate` 判 `agents.0: Invalid input`。官方文档中 `["./commands/", "./extras/"]` 那种「用目录保留默认扫描」的范式**不适用于 `agents`**。

⚠️ **路径与实际文件名逐字一致**（`./agents/dotnet-diagnose.md`）。`agents` 是官方 **replaces** 语义——声明后默认目录扫描被完全取代，路径写错则 agent 一个都加载不到。

- [ ] **Step 5: 🔴 CHECKPOINT — agent 真实加载核验（go / no-go）**

这是本任务的**目的**。三条命令作用互补，缺一不可：

```bash
# ① 结构校验：manifest JSON、agents 路径存在性、agent frontmatter 能否解析
claude plugin validate ./plugins/optimus-devops-plugin

# ② 真实加载核验（必查项）
claude --plugin-dir ./plugins/optimus-devops-plugin -p "列出你可用的、名字含 dotnet 的 agent，只输出 agent 名"

# ③ 行数与 frontmatter 字段人工核对
wc -l plugins/optimus-devops-plugin/agents/dotnet-diagnose.md
sed -n '/^---$/,/^---$/p' plugins/optimus-devops-plugin/agents/dotnet-diagnose.md | grep -E '^[a-z]+:'
```

判定：
- ✅ **通过** — ① 无 error；② 输出 `optimus-devops-plugin:dotnet-diagnose`；③ 行数 ≤ 80，frontmatter 恰 `name` / `description` / `tools` 三行
- ❌ **不通过** — ② 未输出该 agent 名，或输出的是文件名以外的其他名字

⚠️ **`claude plugin details optimus-devops-plugin` 的 Agents 列不能用来判断加载成功**（实测两个缺陷）：① 声明 `agents` 字段时该列统计为 `0`，即便 agent 已正常加载（官方 `dotnet-diag` 0.1.1 同现象）；② 该列显示的是**文件名**，不是注册名。**用它做判据会得出「agent 加载失败」的错误结论。**

⚠️ **`validate` 通过 ≠ frontmatter 写对了**：它确实会检查 agent frontmatter 能否解析（失败时报错原文为「At runtime this agent loads with its name taken from the filename and every other frontmatter field silently dropped」），但 YAML 容错很强——`tools: [unclosed` 这类会被解析成合法值。字段名拼错、值类型不符一律查不出来，**只能靠 ③ 的人工核对**。

🔴 **不通过时停下回报，不要临场改方案。** 最可能的两类原因：`agents` 路径与实际文件名不一致（逐字比对）、frontmatter YAML 被 `tools` 数组的引号写法搞坏（试着改成多行 YAML 列表形态）。两者都排除后仍不通过，说明 CLI 行为与 spec § 2.5 的实测结论不符——**必须先与用户确认再执行**，因为那会波及 spec 的 agent 层设计前提。

- [ ] **Step 6: 校验 `agents/` 目录干净**

Run:
```bash
echo "=== agents/ 下的全部文件（应只有 1 个）==="
ls -la plugins/optimus-devops-plugin/agents/
echo ""
echo "=== 不得有 .agent.md 双扩展名 ==="
ls plugins/optimus-devops-plugin/agents/*.agent.md 2>&1 | head -2
echo ""
echo "=== 不得有 CHANGELOG / README / 任何辅助文件 ==="
ls plugins/optimus-devops-plugin/agents/ | grep -iv '^dotnet-diagnose\.md$' || echo "（无其他文件，正确）"
```

Expected: `agents/` 下只有 `dotnet-diagnose.md` 一个文件。

⚠️ **保持目录干净仍是硬要求，即便本次已显式声明 `agents`（replaces 语义使默认扫描失效）。** 理由：声明一旦被后人改回默认扫描，辅助文件会被静默降级加载成 agent——CLI 会用文件名当 agent 名、其余 frontmatter 字段全部丢弃，于是 `agents/CHANGELOG.md` 变成一个叫 `optimus-devops-plugin:CHANGELOG` 的条目。官方**未提供任何文件名黑名单或豁免机制**。

- [ ] **Step 7: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
plugins/optimus-devops-plugin/agents/dotnet-diagnose.md
plugins/optimus-devops-plugin/.claude-plugin/plugin.json
```

提交消息建议：
```
feat(devops-plugin): 新增 dotnet-diagnose agent 并显式声明 agents 字段
```

⚠️ **本次改了 `plugin.json` 但只增补 `agents` 字段、未动 `version`**——Task 7 统一升。若 `commit-cc-plugin` 第三步的校验脚本报两份不一致，说明有人提前改了某一份，**回头核对而非拿一边覆盖另一边**。

---

## Task 6: agent 配套文档（`agent-docs/`）

**Files:**
- Create: `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md`
- Create: `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md`

**Interfaces:**
- Consumes: Task 5 的 agent 本体（README 要抄它的调用名与 description 触发面）
- Produces: agent 的版本号真源（CHANGELOG 最新 `## [x.y.z]`）与六章节 README

⚠️ **位置是 `agent-docs/<name>/`，不是 `agents/`**（`.claude/rules/agent-conventions.md` 的目录硬约束）。根源：`agents/` 是「目录内容 = 可调用实体列表」，而 `skills/<name>/` 是「目录内容 = 一个实体的组成部分」——**同一份「配套文档放哪」的约定不能无差别套用到两种产物上**。SKILL.md 旁放 README/CHANGELOG 完全安全，agents/ 旁放则会被降级加载成 agent。

⚠️ **agent 层的豁免范围已收窄**：CHANGELOG / README **不再豁免**（本任务的交付物），仅 `known-issues.md` 与 darwin-skill 评分门禁仍豁免——后者是因为 `known-issues.md` 本身就是 darwin-skill 循环的输入产物，两者同进同退，而 rubric 对 agent 无对应评分维度。

- [ ] **Step 1: 建 CHANGELOG（agent 版本号真源）**

Create `agent-docs/dotnet-diagnose/CHANGELOG.md`：

```markdown
## [1.0.0] - 2026-09-06

### Added
- 新建 agent：本仓首个 agent 形态产物，编排 .NET 取证输出的根因定位流程
- 三步主干：证据清点 → 定征象与初始化台账 → 裁剪台账与自检出结论
- 承载层加载时机：Step 1 之后加载 `optimus-devops-plugin:dotnet-diagnose-triage`，判据不写在 agent 内
- 输出格式固定四段：结论与出处、修复方向 anchor、台账交接块、免责声明
- 边界四条：无证据不入循环、不执行取证、不硬套征象、知识库无判据时标「超出覆盖」
```

⚠️ **首版 `1.0.0`，与所属插件版本互不换算**。插件本次升到 `1.1.0`（Minor，新增 agent + skill），agent 自己是 `1.0.0`——两类版本号不换算、不同步、不要求任何对应关系。

- [ ] **Step 2: 建 README（六章节，两章按 agent 分栏写法）**

Create `agent-docs/dotnet-diagnose/README.md`。六章节按 `.claude/rules/doc-conventions.md` 的 agent 分栏：

**① 标题与元信息**

```markdown
# dotnet-diagnose

> 版本：1.0.0 | 产物类型：agent

在已经拿到 dump / SOS 输出 / trace 报告之后，按假设台账消解定位 .NET 应用的运行期根因，判据全部出自 `knowledge-base/dotnet-debugging/`。
```

⚠️ **无「分类」**——插件 agent 的 frontmatter 没有 `metadata` 字段，因此没有 `category` 可抄。版本号抄 CHANGELOG 最新条目，两处须一致。

**② 所处层级** — ⚠️ **按「与相邻产物的划界」画图，不用 category 六取值层级**（agent 无该字段）。图中须标出四组相邻关系：

```
┌──────────────────────────────────────────────────────────┐
│ 微软官方 dotnet-diag（只读上游）                          │
│  dump-collect / dotnet-trace-collect                     │
│  → 管「取到证据」：抓 dump、选采集工具、容器与 K8s 适配    │
│  → 明确拒绝：「Do not open, analyze, or triage dumps」     │
└────────────────────────┬─────────────────────────────────┘
                         │ 证据交接（单向：我们指回官方）
                         ▼
┌──────────────────────────────────────────────────────────┐
│ ★ dotnet-diagnose (agent · 编排)                          │
│   → 管「读懂证据并定根因」，即官方拒绝的那一半            │
└────────────────────────┬─────────────────────────────────┘
                         │ Skill 工具加载
                         ▼
┌──────────────────────────────────────────────────────────┐
│ dotnet-diagnose-triage (skill · 承载)                     │
│   台账规则 / 自检 / 强度 / 失败处理 + references 三份      │
└──────────────────────────────────────────────────────────┘

横向相邻（切线：验尸 vs 预防 / 动态单点 vs 静态全貌）：
  csharp-code-review  → 静态读源码判是否违规  ┐
  wpf-code-review     → XAML 绑定写法是否合规 ├─ 均不消费本领域
  project-analyze     → 项目结构与技术栈概览  ┘
```

**③ 触发词 / 调用方式** — ⚠️ **改为「调用方式与触发面」**（agent 无复合形态，调用机制与 skill 的 `/` 前缀不同）：

- Claude 侧：`@optimus-devops-plugin:dotnet-diagnose`
- Codex 侧：同名触发（按 description 语义匹配）
- **承担跨语言触发的技术标识符**：`dump` / `SOS` / `trace` / `WPF` / `.NET Framework`——description 主体是中文，但这些原形标识符在中英文提问里都会出现

⚠️ 须写明**语言不对称的实际影响**：官方产物全英文、本 agent 与知识库全中文，两侧不在同一语言空间做语义匹配，**触发词互抢的风险实际低于同语言场景**，代价是英文提问的用户较难命中。不做双语 description（两个 harness 均按单一 description 匹配，双语会稀释语义密度）。

**④ 业务逻辑流程图** — Step 1/2/3 竖排 ASCII 流程框，与 agent 正文的三步主干一致。

**⑤ 产出物数据流**

```
取证输出（dump / SOS / trace / 崩溃日志）
   → dotnet-diagnose (agent)
   → 加载 dotnet-diagnose-triage (skill) 取判据规则
   → 输出四段：结论+强度+出处 / 修复方向 anchor / 台账交接块 / 免责声明
   → 人工接手（修复动作由人执行；台账可作为下一轮输入续用）
```

**⑥ 依赖关系图** — ⚠️ **须标出它加载的 skill**（`tools` 含 skill 加载能力时的硬要求）：

```
用户 / 主对话 ──@调用──▶ dotnet-diagnose (agent)
                            │
                            ├──Skill 加载──▶ optimus-devops-plugin:dotnet-diagnose-triage
                            │                     │
                            │                     └──Read──▶ knowledge-base/dotnet-debugging/
                            │
                            └──建议转向（不调用）──▶ 官方 dump-collect / dotnet-trace-collect
                                                      官方未安装时回落本知识库 dump-capture.md
```

⚠️ **全部用纯 ASCII box-drawing 字符**（`┌─┐│└┘├┤▼→↓★`），不用 Mermaid、不嵌图片。

⚠️ **不写「安装」章节**——本仓产物随所属插件整体安装，无独立安装步骤。

- [ ] **Step 3: 校验配套文档**

Run:
```bash
D=plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose
echo "=== 两处版本号一致（都是 1.0.0）==="
grep -o '^## \[[0-9.]*\]' $D/CHANGELOG.md | head -1
grep -o '版本：[0-9.]*' $D/README.md
echo ""
echo "=== README 章节（应 5 个二级标题 + 1 个一级标题）==="
grep -n '^#' $D/README.md
echo ""
echo "=== agent 分栏要求：无 category、有划界图、有加载的 skill ==="
for kw in '产物类型：agent' 'dotnet-diagnose-triage' 'dump-collect' '@optimus-devops-plugin:dotnet-diagnose'; do
  printf '%-40s' "$kw"; grep -c "$kw" $D/README.md || true
done
echo ""
echo "=== 不得出现 category 或 6 取值层级 ==="
grep -c 'category\|workflow/quality/generator' $D/README.md || echo "（全 0，正确）"
echo ""
echo "=== 无 Mermaid、无图片 ==="
grep -c 'mermaid\|!\[' $D/README.md || echo "（全 0，正确）"
echo ""
echo "=== agents/ 目录仍只有一个文件（配套文档没放错位置）==="
ls plugins/optimus-devops-plugin/agents/
```

Expected:
- 两处版本号均 `1.0.0`
- README 一级标题 1 个 + 二级标题 5 个（所处层级 / 调用方式与触发面 / 业务逻辑流程图 / 产出物数据流 / 依赖关系图）
- 四个 agent 分栏关键词各 ≥ 1
- `category` = 0、Mermaid / 图片 = 0
- `agents/` 下仍只有 `dotnet-diagnose.md`

🔴 **最后一项是本任务最容易出错的地方**——把 CHANGELOG / README 建到 `agents/` 下会让它们被降级加载成假 agent。若 `ls` 输出多于一个文件，**立即移到 `agent-docs/dotnet-diagnose/` 并重跑 Task 5 Step 5 的加载核验**。

- [ ] **Step 4: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：
```
plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md
plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md
```

提交消息建议：
```
docs(devops-plugin): dotnet-diagnose agent 配套 CHANGELOG 与 README
```

⚠️ 不升 `plugin.json`（Task 7 统一升）。**agent 自己的版本号已在 CHANGELOG 里记为 `1.0.0`，那是描述性版本号，与插件版本号互不换算。**

---

## Task 7: 同期改动（版本、consumers、glob、description）

**Files:**
- Modify: `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`（`version` → `1.1.0`）
- Modify: `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`（`version` → `1.1.0` + description 两处 + `capabilities`）
- Modify: `.claude-plugin/marketplace.json`（只改 devops 的 `description`，**顶层不动**）
- Modify: `knowledge-base/catalog.json`（`dotnet-debugging` 的 `consumers` + `reviewed_at`）
- Modify: `knowledge-base/dotnet-debugging/README.md` L18
- Modify: `.claude/skills/knowledge-base-maintain/scripts/check_refs.py`（`CONSUMER_GLOBS` 增一行）
- Modify: `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py` L112（测试固件的 `.agent.md` → `.md`）

**Interfaces:**
- Consumes: Task 1-6 全部落地（版本要升的是「新增了 skill + agent」这件事，consumers 登记的是 Task 1 建的 skill 路径）
- Produces: 版本、消费者登记、脚本覆盖面三处与实际产物一致。**Task 8 的全量验收以本任务的结果为检查对象**

⚠️ **本任务混合了两类改动，版本影响不同**：`plugins/` 下的两份 `plugin.json` 要升 Minor；`.claude/`、`knowledge-base/`、以及 marketplace 的 `description` **一律不升任何版本号**（AGENTS.md 触发矩阵最后两行 + 「展示元数据不升」行）。**这不矛盾**——不升的那部分不随插件分发，harness 读不到。

- [ ] **Step 1: 两份 plugin.json 同步升到 1.1.0**

Edit `plugins/optimus-devops-plugin/.claude-plugin/plugin.json`：

```json
{
  "name": "optimus-devops-plugin",
  "version": "1.1.0",
  "agents": ["./agents/dotnet-diagnose.md"]
}
```

Edit `plugins/optimus-devops-plugin/.codex-plugin/plugin.json`，把 `"version": "1.0.0"` 改为 `"version": "1.1.0"`。

⚠️ **两份是同一次改动内一起改，没有先后主从**。幅度是 **Minor**——本次新增了一个 skill 与一个 agent（AGENTS.md 幅度表：「新增 skill / agent / hook / command」→ Minor）。

⚠️ **只改 `version` 一个字段**，codex 侧其余（`name` / `skills` / `author` / `homepage` / `license` / `interface` 的其他子字段）在下一步单独处理，不要顺手重排。

- [ ] **Step 2: codex 侧 description 两处同步 + capabilities 增补**

Edit `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` 的两处描述文字，各加入诊断能力：

- 顶层 `description`：现值 `"DevOps：Jenkins 构建、项目分析、周报转写、skill 链接同步"`
- `interface.longDescription`：现值 `"DevOps：Jenkins 构建、项目分析、周报转写、skill 链接同步。内置 Hooks：SessionStart（276条技巧智能轮播）、Notification（Windows权限通知）"`

加入 `.NET 取证输出解读与根因定位` 一项。⚠️ **两处措辞保持一致的前缀**，只在能力列表里加一项，不重写整句。

再改 `interface.capabilities`——现值 `["Skills"]`：

```bash
# 先验证 capabilities 的合法取值
codex plugin --help 2>&1 | head -30
# 或查 .agents/plugins/marketplace.json 里其他条目用了哪些取值
python -c "
import json
d = json.load(open('.agents/plugins/marketplace.json', encoding='utf-8'))
caps = set()
for p in d.get('plugins', []):
    caps |= set(p.get('interface', {}).get('capabilities', []))
print('本仓已用过的 capabilities 取值:', sorted(caps))
"
```

🔴 **CHECKPOINT — 须先验证 `"Agents"`（或对等取值）合法，不合法则不改此项**，`capabilities` 保持 `["Skills"]`。理由：这是 Codex 侧读取的字段，写入未验证的取值可能让整个插件在 Codex 端解析失败——**代价远大于少标一项能力的收益**。若无法验证，如实在提交消息里说明「capabilities 未改，取值合法性待验证」。

- [ ] **Step 3: marketplace 只改 description，顶层不动**

Edit `.claude-plugin/marketplace.json` 的 `optimus-devops-plugin` 条目的 `description`，与 Step 2 的 codex 侧措辞保持一致。

Run（改完后立即验证顶层未被波及）：
```bash
python -c "
import json
d = json.load(open('.claude-plugin/marketplace.json', encoding='utf-8'))
print('顶层 version:', d['version'])
assert d['version'] == '14.0.0', '顶层 version 被改动了！应保持 14.0.0'
with_ver = [p['name'] for p in d['plugins'] if 'version' in p]
assert not with_ver, f'插件条目不应有 version: {with_ver}'
dev = [p for p in d['plugins'] if p['name'] == 'optimus-devops-plugin'][0]
print('devops description:', dev['description'])
assert '诊断' in dev['description'] or '取证' in dev['description'], 'description 未加入诊断能力'
print('PASS: 顶层 14.0.0 未动、条目无 version、description 已更新')
"
```

Expected: `PASS: 顶层 14.0.0 未动、条目无 version、description 已更新`

⚠️ **顶层 `version` 保持 `14.0.0`**——本次是给已有插件加内容，不改集合构成。它只在增删插件时升。

⚠️ **marketplace 的插件条目内永不填写 `version`**：官方明确「同时写 `plugin.json` 与 marketplace 条目时，Claude Code 总是用 `plugin.json` 的值且不给警告」，且本仓条目 `source` 为本地相对路径时官方会额外校验并在两值不一致时报警告。不填则无从冲突。

- [ ] **Step 4: catalog.json 登记首个消费者**

Edit `knowledge-base/catalog.json` 的 `dotnet-debugging` 条目：

```json
      "consumers": ["plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage"],
      "reviewed_at": "2026-09-06",
```

⚠️ **登记 skill 层而非 agent 层**——判据引用全部落在 skill 与其 `references/` 中，agent 只负责调度、正文不含任何 `file § anchor`。登记 agent 会让「谁在消费这个领域」失真。

⚠️ **`consumers` 的路径不被脚本做存在性校验**（`check_index.py` 的 `check_catalog` 只校验 `categories` 对应的目录存在），因此写错路径不会报错。**必须人工核对拼写**，Step 7 有补充校验。

- [ ] **Step 5: 改 dotnet-debugging README 的过时陈述**

Edit `knowledge-base/dotnet-debugging/README.md` L18，把：

```markdown
- **读者**：需要定位 .NET 应用运行期问题的开发与运维人员；本领域一期无固定 skill 消费者
```

改为：

```markdown
- **读者**：需要定位 .NET 应用运行期问题的开发与运维人员；本领域的 skill 消费者是 `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage`（由 `dotnet-diagnose` agent 编排调用）
```

⚠️ **这属陈述性修正，不构成条目变更**——`index.jsonl` 不动、领域版本 **1.2.0 不变**、`knowledge-base/dotnet-debugging/CHANGELOG.md` 不加条目。领域版本号只随条目增删改升。

- [ ] **Step 6: 给 check_refs.py 补一条 glob**

Edit `.claude/skills/knowledge-base-maintain/scripts/check_refs.py` 的 `CONSUMER_GLOBS`（现 L27-32）：

```python
CONSUMER_GLOBS = (
    "plugins/*/skills/*/SKILL.md",
    "plugins/*/skills/*/*REFERENCE*.md",
    "plugins/*/skills/*/references/*.md",
    "knowledge-base/*/rules/*.md",
    "knowledge-base/*/reference/*.md",
)
```

**为什么必须补这一行**：

| 新增文件 | 是否被原有 glob 覆盖 |
|---|---|
| `skills/dotnet-diagnose-triage/SKILL.md` | ✅ **自动覆盖**（命中第一条）——这是改为两层结构的附带收益：agent 单层方案下判据引用全在 `agents/` 里，脚本一条都查不到 |
| `skills/dotnet-diagnose-triage/references/*.md` | ❌ 不覆盖（第二条 glob 是**同级** `*REFERENCE*.md`，不含子目录）。**而这三份恰是 anchor 密度最高的**，故补这一行 |
| `agents/dotnet-diagnose.md` | ❌ 不覆盖，**且不补**——agent 层只写编排，不含 `file § anchor`，无可查对象。若日后 agent 正文出现 anchor，说明分层被破坏，该由 Task 8 的「判据表不出现在 agent 内」一项拦住 |

⚠️ **补 glob 属 `.claude/` 下改动，不升任何版本号**。也不升 `knowledge-base-maintain` 这个 skill 自身的 `metadata.version`？——**要升**：它是 skill 的描述性版本号，改了脚本行为就该升 **Patch**（修改已有内容）。这与「`.claude/` 下改动不升版本号」不矛盾：后者说的是**插件版本号**。同时在 `.claude/skills/knowledge-base-maintain/CHANGELOG.md` 加对应条目。

- [ ] **Step 7: 顺手修 test_check_plugin_versions.py 的过时固件**

Edit `.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py` L112：

```python
        make_plugin(self.root, "p-agents", "1.0.0", "1.0.0",
                    claude_extra={"agents": ["./agents/x.md"]})
```

（原为 `"./agents/x.agent.md"`。）

⚠️ **这是纯固件措辞修正，不改断言**——该测试验的是「`agents` 字段被允许存在」，路径值本身不参与断言。改它的理由是避免测试固件成为 `.agent.md` 命名的残留示范。**同时升 `commit-cc-plugin` 的 `metadata.version` Patch 并加 CHANGELOG 条目。**

- [ ] **Step 8: 全量校验七处改动**

Run:
```bash
echo "########## ① 两份 plugin.json 同值 1.1.0 ##########"
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
python -c "
import json
a=json.load(open('plugins/optimus-devops-plugin/.claude-plugin/plugin.json',encoding='utf-8'))
b=json.load(open('plugins/optimus-devops-plugin/.codex-plugin/plugin.json',encoding='utf-8'))
assert a['version']==b['version']=='1.1.0', f\"应为 1.1.0: {a['version']} vs {b['version']}\"
assert a['agents']==['./agents/dotnet-diagnose.md'], f\"agents 字段异常: {a.get('agents')}\"
print('PASS: 两份同值 1.1.0，agents 声明正确')
"

echo ""
echo "########## ② marketplace 顶层未动 ##########"
python -c "
import json
d=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'))
assert d['version']=='14.0.0'
print('PASS: 顶层 14.0.0')
"

echo ""
echo "########## ③ catalog consumers 路径真实存在 ##########"
python -c "
import json, pathlib
d=json.load(open('knowledge-base/catalog.json',encoding='utf-8'))
e=[x for x in d['domains'] if x['domain']=='dotnet-debugging'][0]
print('consumers:', e['consumers'])
print('reviewed_at:', e['reviewed_at'])
for c in e['consumers']:
    assert pathlib.Path(c).is_dir(), f'路径不存在: {c}'
print('PASS: consumers 路径存在')
"

echo ""
echo "########## ④ 知识库两个校验脚本（条目数须不变）##########"
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
echo "check_index 退出码: $?"
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
echo "check_refs 退出码: $?"

echo ""
echo "########## ⑤ 新 glob 确实生效（应命中三份 references）##########"
python -c "
import pathlib
n = len(list(pathlib.Path('.').glob('plugins/*/skills/*/references/*.md')))
print('新 glob 命中文件数:', n)
assert n >= 3, '新 glob 未命中 dotnet-diagnose-triage 的三份 references'
print('PASS')
"

echo ""
echo "########## ⑥ 全部单元测试 ##########"
python -m unittest discover -s .claude/skills/commit-cc-plugin/scripts -p "test_*.py" 2>&1 | tail -3
python -m unittest discover -s .claude/skills/knowledge-base-maintain/scripts -p "test_*.py" 2>&1 | tail -3

echo ""
echo "########## ⑦ 全仓不得再有 .agent.md（docs/ 历史记录除外）##########"
grep -rn '\.agent\.md' --include='*.md' --include='*.py' --include='*.json' . 2>/dev/null \
  | grep -v '^\./docs/' | grep -v '^\./\.remember/' | grep -v '^\./\.superpowers/' \
  | grep -v 'VS Code' || echo "（无，正确）"
```

Expected:
- ① 校验 PASS，两份同值 `1.1.0`，`agents` 声明正确
- ② 顶层 `14.0.0`
- ③ consumers 路径存在，`reviewed_at` 为 `2026-09-06`
- ④ 两个脚本 PASS，**条目数不变（全局 576 / 领域 74）**
- ⑤ 新 glob 命中 ≥ 3
- ⑥ 两组测试 `OK`（11 / 141）
- ⑦ 除 `agent-conventions.md` 里那句「不要用 `.agent.md`」警告（已被 `grep -v 'VS Code'` 排除）外无残留

🔴 **④ 的条目数若变了，说明误改了知识库正文的小节标题**——Step 5 改的 L18 不是小节标题行，正确操作不会影响索引。回退重做。

🔴 **④ 的 `check_refs.py` 若因新 glob 报出既有文件的错误**，说明其他插件的 `skills/*/references/` 下有失效 anchor（本次首次纳入检查）。**逐条修那些 anchor，不要撤销 glob**——它们是真实存在的失效引用，此前只是没被检查到。

- [ ] **Step 9: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围（8 个文件）：
```
plugins/optimus-devops-plugin/.claude-plugin/plugin.json
plugins/optimus-devops-plugin/.codex-plugin/plugin.json
.claude-plugin/marketplace.json
knowledge-base/catalog.json
knowledge-base/dotnet-debugging/README.md
.claude/skills/knowledge-base-maintain/scripts/check_refs.py
.claude/skills/knowledge-base-maintain/SKILL.md
.claude/skills/knowledge-base-maintain/CHANGELOG.md
.claude/skills/commit-cc-plugin/scripts/test_check_plugin_versions.py
.claude/skills/commit-cc-plugin/SKILL.md
.claude/skills/commit-cc-plugin/CHANGELOG.md
```

提交消息建议：
```
feat(devops-plugin): dotnet-diagnose 交付收口，devops 升 1.1.0 并登记知识库消费者
```

⚠️ **本次是唯一升插件版本的任务**。若校验脚本报两份不一致，回头判断本次改动该升什么号（Minor，因新增 skill + agent），把两份都写成该值——**不要拿一边覆盖另一边**。

---

## Task 8: 黄金测例逐例跑通与全量验收

**Files:**
- Modify（仅当测例不通过时）: SKILL.md / `references/*.md` / `agents/dotnet-diagnose.md`
- Modify: `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/known-issues.md`（记录测例跑通结果）

**Interfaces:**
- Consumes: Task 1-7 全部落地
- Produces: 行为正确性已验证的完整交付。**这是唯一验「诊断对不对」的任务**——其余全是结构验收

⚠️ **本任务可能触发返工**：测例不通过时改的是 SKILL.md / references，**不改测例预期**。改完须重跑该例，并回归其余六例（改主干可能影响其他例）。

- [ ] **Step 1: 逐例跑七个黄金测例**

对 `test-cases/golden.md` 的每一例，把「输入」段原样作为 prompt：

```bash
claude --plugin-dir ./plugins/optimus-devops-plugin -p "@optimus-devops-plugin:dotnet-diagnose <测例 N 的输入段原文>"
```

（或在交互会话里 `@optimus-devops-plugin:dotnet-diagnose` 后粘输入段。）

逐例记录三项比对结果：

| # | 台账状态是否与预期一致 | 结论强度是否与预期一致 | 依据 anchor 是否挂对 |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |

🔴 **CHECKPOINT — 七例全通过才算行为验收通过。**

**三个最可能不通过的点**（按 spec 标注的风险排序）：

1. **测例 5**（台账须含完整 7 条候选、断链记「推测」不记「无法判定」）——两个常见错误是「只登记活体表的 2 条」和「断链误记 `无法判定`」。若失败，检查 `references/symptom-hypothesis-map.md` 的三条规则是否写清、SKILL.md「初始化」节是否明确指向合并候选集
2. **测例 4**（§ 4 弱事件泄漏必须仍为 `待验`）——若被越界排除，说明 `references/symptom-hypothesis-map.md` 或 SKILL.md 未传达「排除判据有范围限定」。修 SKILL.md「关闭」节，补一句「排除判据的适用范围以其原文限定为准，不得外推」
3. **测例 2 / 7**（不得报「已确认」）——若报成已确认，说明自检第二项没起作用。修 SKILL.md「出结论前的自检」节，把第二项从「结论有没有超出证据」改写为可操作的判定动作

⚠️ **失败时先判断是「规则没写清」还是「规则写了但没被读到」**。后者往往是 progressive disclosure 的落点问题——例如判据形态写在 `verdict-forms.md` 但主干没写「何时加载它」，agent 就永远不会下钻。**这类问题改主干的加载指引，不是改 references 内容。**

- [ ] **Step 2: 把测例结果记入 known-issues.md**

Edit `.../dotnet-diagnose-triage/known-issues.md`，在 darwin-skill 基线表之后追加：

```markdown
## 黄金测例首轮结果（2026-09-06）

| # | 台账 | 强度 | anchor | 备注 |
|---|---|---|---|---|
| 1 | ✅ | ✅ | ✅ | — |
| … | | | | 逐例填实测结果 |

不通过并已修正的例：<列出例号与所做修正；无则写「无」>
```

⚠️ **如实记录首轮不通过的例与所做修正**——这是后续 darwin-skill 循环的输入。掩盖首轮失败会让优化循环失去起点。

- [ ] **Step 3: agent 层结构验收（11 项）**

Run:
```bash
A=plugins/optimus-devops-plugin/agents/dotnet-diagnose.md
echo "=== ① 纯 .md，非 .agent.md ===" && ls plugins/optimus-devops-plugin/agents/
echo "=== ② frontmatter 恰三字段，不含 license ===" 
sed -n '/^---$/,/^---$/p' "$A" | grep -E '^[a-z]+:'
echo "=== ③ 正文 ≤ 80 行 ===" && wc -l "$A"
echo "=== ④ tools 含 skill 加载能力，不含写入/执行工具 ==="
grep -o "tools:.*" "$A"
echo "=== ⑤ 判据表不出现在 agent 内（不得有 file § anchor 引用知识库）==="
grep -c 'knowledge-base/dotnet-debugging' "$A" || echo "（0，正确）"
echo "=== ⑥ 台账交接块与续用语义 ==="
for kw in '台账交接块' '继续排查请把' '续用' '免责声明'; do printf '%-20s' "$kw"; grep -c "$kw" "$A" || true; done
echo "=== ⑦ description 含划界句 ==="
grep -c 'dump-collect' "$A" || true
echo "=== ⑧ agent-docs 两份 + README 版本号一致 ==="
grep -o '^## \[[0-9.]*\]' plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md | head -1
grep -o '版本：[0-9.]*' plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md
echo "=== ⑨ plugin.json 的 agents 路径逐字一致 ==="
python -c "
import json, pathlib
d = json.load(open('plugins/optimus-devops-plugin/.claude-plugin/plugin.json', encoding='utf-8'))
for p in d['agents']:
    f = pathlib.Path('plugins/optimus-devops-plugin') / p.lstrip('./')
    print(p, '→ 存在' if f.exists() else '→ ❌ 不存在')
    assert f.exists()
assert d['name'] == 'optimus-devops-plugin' and d['version'] == '1.1.0', '原有字段被覆盖'
print('PASS')
"
echo "=== ⑩ validate ===" && claude plugin validate ./plugins/optimus-devops-plugin
echo "=== ⑪ 真实加载核验（不可用 plugin details 代替）==="
claude --plugin-dir ./plugins/optimus-devops-plugin -p "列出你可用的、名字含 dotnet 的 agent，只输出 agent 名"
```

Expected:
- ① `agents/` 下只有 `dotnet-diagnose.md`
- ② frontmatter 恰 `name` / `description` / `tools` 三行，**无 `license`**
- ③ 行数 ≤ **80**
- ④ `tools` 含 `'skill'` 与 `'Skill'`，**不含 `Write` / `Edit` / `Bash`**
- ⑤ agent 内引用知识库 = **0**（判据全在 skill 层）
- ⑥ 四个关键词各 ≥ 1
- ⑦ description 含 `dump-collect` 划界
- ⑧ 两处版本号均 `1.0.0`
- ⑨ `agents` 路径存在、原有 `name` / `version` 未被覆盖
- ⑩ validate 无 error
- ⑪ 输出 `optimus-devops-plugin:dotnet-diagnose`

⚠️ **⑤ 是分层是否守住的关键判据**。若 agent 内出现知识库 anchor，说明判据渗进了编排层——**搬去 skill 层**，否则 `check_refs.py` 查不到它们（agent 路径不在 `CONSUMER_GLOBS` 里，且按 Task 7 的决定不补）。

⚠️ **⑪ 不能用 `claude plugin details` 代替**：其 Agents 列在声明 `agents` 时统计为 0（实测缺陷，官方 `dotnet-diag` 同现象），且显示文件名而非注册名。

- [ ] **Step 4: skill 层结构验收（14 项）**

Run:
```bash
D=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage
echo "=== ① frontmatter 与三处版本号 ==="
grep -E '^(name|description|compatibility|allowed-tools):' $D/SKILL.md | cut -c1-60
sed -n '/^metadata:/,/^[a-z]/p' $D/SKILL.md | grep -E '^  '
echo "=== ② README 六章节 + 全 ASCII ===" && grep -c '^#' $D/README.md && grep -c 'mermaid\|!\[' $D/README.md || true
echo "=== ③ known-issues 含评分依据与评估模式 ==="
grep -c 'full_test\|dry_run' $D/known-issues.md || true
echo "=== ④ references 三份按分工，主干无征象映射表 ==="
wc -l $D/references/*.md
grep -c '合并后完整候选集' $D/SKILL.md || true
echo "=== ⑤ B 组三项校验各挂 anchor ==="
for kw in '位数必须匹配' '四种类型的能力对照' 'symbols-and-tool-matching'; do
  printf '%-32s' "$kw"; grep -rc "$kw" $D/ | awk -F: '{s+=$2} END {print s}'
done
echo "=== ⑥ 路由表 12 个去向 + 四个「—」各配说明 ==="
grep -c '需先换一类证据\|无对应判据' $D/references/symptom-hypothesis-map.md || true
echo "=== ⑦ 第二跳去向（6 条判据句 / 7 个目标）==="
grep -c 'sos-locks-and-async.md § 3\|sos-threads-and-stacks.md § 2\|再转' $D/references/symptom-hypothesis-map.md || true
echo "=== ⑧ 修复方向四档 + 6 处判据句内引用 ==="
grep -c '判据句内\|反查表格行内\|下一步\|导语' $D/references/verdict-forms.md || true
echo "=== ⑨ wpf-leak-patterns § 6 反查表作为独立入口 ==="
grep -c 'wpf-leak-patterns.md § 6\|根链形态图鉴' $D/references/symptom-hypothesis-map.md || true
echo "=== ⑩ 崩溃日志两栏 + 与业务日志的区分线 ==="
grep -c '区分线' $D/references/evidence-precheck.md || true
echo "=== ⑪ 台账四状态 / 三强度 / 四自检 / 九失败处理 ==="
for kw in '无法判定' '超出覆盖' '自检' ; do printf '%-14s' "$kw"; grep -c "$kw" $D/SKILL.md || true; done
sed -n '/^## 失败处理/,/^## /p' $D/SKILL.md | grep -c '^| ' || true
echo "=== ⑫ 三条 MUST 级别未被抬高或降低 ==="
sed -n '/^## dump 处置合规/,$p' $D/SKILL.md | grep -c 'MUST' || true
sed -n '/^## dump 处置合规/,$p' $D/SKILL.md | grep -c 'SHOULD' || true
echo "=== ⑬ 全部引用为 file § anchor，无正文复制（抽查最长 5 行）==="
awk '{print length"\t"$0}' $D/SKILL.md | sort -rn | head -5 | cut -c1-140
echo "=== ⑭ check_refs 覆盖 SKILL.md 与 references ==="
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
```

Expected:
- ① 顶层五字段 + `metadata` 三项，`version` / CHANGELOG / README 三处均 `1.0.0`
- ② README 6 个标题、Mermaid/图片 = 0
- ③ 评估模式 ≥ 1
- ④ 三份 references 合计 250-290 行；主干的「合并后完整候选集」≤ 1 次
- ⑤ B 组三项 anchor 各 ≥ 1
- ⑥ 空格说明 ≥ 4
- ⑦ 第二跳关键词 ≥ 3
- ⑧ 四档关键词各 ≥ 1
- ⑨ § 6 反查表 ≥ 1
- ⑩ 区分线 ≥ 1
- ⑪ 三个关键词各 ≥ 1；失败处理表 **11 行**（表头 + 分隔 + 9 条）
- ⑫ **MUST 恰 3 处、SHOULD 恰 2 处**——级别不得抬高或降低
- ⑬ 最长行都是表格行（含 `|`），不出现连续判据正文段
- ⑭ `check_refs.py` PASS

⚠️ **⑫ 是最容易被无声改错的一项**。`rules/01-dump-handling.md` 的 § 1 / § 2 / § 4 是 MUST（含 3 处「禁止」），§ 3 / § 5 是 SHOULD。**把 SHOULD 说成 MUST 是过度约束用户，把 MUST 说成 SHOULD 是合规风险**——两个方向都不可接受。

- [ ] **Step 5: 全局验收**

Run:
```bash
echo "########## 版本与清单 ##########"
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
python -c "
import json
a=json.load(open('plugins/optimus-devops-plugin/.claude-plugin/plugin.json',encoding='utf-8'))
m=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'))
assert a['version']=='1.1.0', f\"devops 应为 1.1.0: {a['version']}\"
assert m['version']=='14.0.0', f\"顶层应保持 14.0.0: {m['version']}\"
print('PASS: devops 1.1.0（Minor）、marketplace 顶层 14.0.0 未动')
"

echo ""
echo "########## 知识库 ##########"
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
python -c "
import json
d=json.load(open('knowledge-base/catalog.json',encoding='utf-8'))
e=[x for x in d['domains'] if x['domain']=='dotnet-debugging'][0]
assert e['consumers']==['plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage'], e['consumers']
print('PASS: consumers 登记 skill 层')
"
echo "=== 领域版本应仍为 1.2.0（未新增判据）==="
grep -o '^## \[[0-9.]*\]' knowledge-base/dotnet-debugging/CHANGELOG.md | head -1

echo ""
echo "########## 九个插件全量 validate ##########"
for p in plugins/*/; do
  n=$(basename "$p"); printf '%-28s' "$n"
  claude plugin validate "./$p" 2>&1 | tail -1
done

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
- 版本校验 PASS；devops `1.1.0`、marketplace 顶层 `14.0.0`
- `check_index.py` / `check_refs.py` 均 PASS，**条目数不变（全局 576 / 领域 74）**
- catalog consumers 登记 skill 层；领域 CHANGELOG 最新仍为 `[1.2.0]`
- 9 个插件全部 validate 通过
- 四组测试全 `OK`（11 / 141 / 46 / 77）
- `git status --short` 为空

- [ ] **Step 6: 提交**

说「提交」触发 `commit-cc-plugin`。提交范围：仅本任务实际改动的文件（`known-issues.md` 必改；测例返工时另加被修的 SKILL.md / references / agent）。

提交消息建议：
```
test(devops-plugin): dotnet-diagnose 七个黄金测例跑通并记录基线
```

⚠️ **若 Step 1 触发了返工，改的是 `skills/` 或 `agents/` 下的文件 → 须再升 devops 两份 `plugin.json` 的 Patch（`1.1.0` → `1.1.1`，「修改或修复已有内容」），并同步升被改 skill 的 `metadata.version` Patch 或 agent CHANGELOG Patch。** 这不与 Task 7 的 Minor 冲突——那次记的是「新增」，这次记的是「修复」。

⚠️ **若返工改了 SKILL.md 且属 Minor 幅度（补了整节）→ 须重跑 darwin-skill 并确认新分数 ≥ Task 3 Step 6 的基线分**，倒退则先修正。agent 层的返工不跑 darwin-skill（rubric 无对应维度），按本任务 Step 3 的 11 项人工核验。

---

## 完成后的整体核验

全部 8 个任务完成后跑一遍，对齐 spec § 10 的四组验收标准：

```bash
echo "########## § 10.1 行为正确性（唯一验「诊断对不对」的一组）##########"
echo "→ 七个黄金测例的比对结果见 known-issues.md 的「黄金测例首轮结果」表"
grep -A 12 '黄金测例首轮结果' plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/known-issues.md

echo ""
echo "########## 零命中形态未被误用 ##########"
D=plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage
grep -c '证实：\|排除：' $D/SKILL.md $D/references/*.md $D/test-cases/golden.md 2>/dev/null

echo ""
echo "########## § 10.2 agent 层 ##########"
wc -l plugins/optimus-devops-plugin/agents/dotnet-diagnose.md
ls plugins/optimus-devops-plugin/agents/
claude --plugin-dir ./plugins/optimus-devops-plugin -p "列出你可用的、名字含 dotnet 的 agent，只输出 agent 名"

echo ""
echo "########## § 10.3 skill 层 ##########"
wc -l $D/SKILL.md $D/references/*.md $D/test-cases/golden.md
grep -o 'version: "[^"]*"' $D/SKILL.md

echo ""
echo "########## § 10.4 全局 ##########"
python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .
python .claude/skills/knowledge-base-maintain/scripts/check_index.py
python .claude/skills/knowledge-base-maintain/scripts/check_refs.py
git status --short
```

Expected:
- 黄金测例七例全通过（known-issues 表内无 ❌）
- 全角冒号形态：`verdict-forms.md` = 1（警告文本），其余全 0
- agent ≤ 80 行、`agents/` 只一个文件、无头模式输出 `optimus-devops-plugin:dotnet-diagnose`
- skill 各文件行数在预估区间，`metadata.version` 为 `1.0.0`（无返工）或 `1.0.1`（有返工）
- 三个脚本 PASS，工作树干净

⚠️ **本计划不覆盖 spec § 11「不在本次范围」的任何一项**——知识库四期（Linux 容器专属，用户已明确暂停）、取证命令执行、采集工具选型矩阵、NativeAOT 诊断、`AssemblyLoadContext` 卸载、Hook 形态自动触发（插件 agent 不支持 `hooks` 字段）、与官方 `analyzing-dotnet-performance` 的关系梳理。**实施中若发现某项「顺手做了更好」，先停下确认——它们各有独立的归属方。**
