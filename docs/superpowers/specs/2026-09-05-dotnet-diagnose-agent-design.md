# dotnet-diagnose agent 设计规约

> 日期：2026-09-05
> 状态：设计已确认，待实施计划
> 归属插件：`plugins/optimus-devops-plugin/`
> 产物类型：**agent（编排）+ skill（承载）两层**，agent 为本仓首个

## 1. 背景与定位

`knowledge-base/dotnet-debugging/` 已交付三期（版本 1.2.0，74 条索引条目，15 篇文件）。一期 spec 的「契约三：一期不建 skill」要求知识库先落地、暴露真实检索路径后再建消费者——本 spec 即该契约的兑现。兑现形态经调研后定为 **agent 编排 + skill 承载两层**（理由见 § 2）：agent 提供主对话之外的独立上下文以支撑自检，skill 承载判据表等深度内容。

`catalog.json` 中 `dotnet-debugging` 的 `consumers` 目前为空，本次交付后登记 skill 层为其首个消费者（判据引用全在该层）。

### 1.1 与官方 dotnet-diag 插件的划界

调研发现用户环境已安装微软官方 `dotnet-diag@dotnet-agent-skills`（源 `https://github.com/dotnet/skills.git`，版本 0.1.0），含 7 个 skill 与 1 个 agent。其中两个与本领域正面相邻：

| 官方产物 | 它做什么 | 明确拒绝什么 |
|---|---|---|
| `dump-collect`（96 行 + 771 行 references） | 配置与抓取 dump：CoreCLR / NativeAOT，Linux/macOS/Windows，含容器与 K8s | Stop Signals 原文：「Do not open, analyze, or triage dump files」「If the user already has a dump file, this skill does not cover analysis」「Do not trace root cause of crashes」。且**不支持 .NET Framework** |
| `dotnet-trace-collect`（252 行 + 574 行 references） | 按 OS × 运行时 × admin × 容器四维选采集工具，覆盖 PerfView / perfcollect / dotnet-monitor / dotnet-trace | 原文：「does not analyze code for anti-patterns or perform the analysis itself」「Analyzing collected trace or dump files (this skill recommends tools for analysis, but does not perform it)」 |

**划界一句话：官方管「取到证据」，我们管「读懂证据并定根因」。**

### 1.2 因此收窄的范围

本 agent **不做**以下事项——官方已覆盖且更完备：

| 收窄掉的能力 | 官方对应物 | 我们放弃的理由 |
|---|---|---|
| 抓取 dump 的命令封装与容器适配 | `dump-collect` 的 `container-dumps.md`（400 行）/ `coreclr-dumps.md` / `nativeaot-dumps.md` | 单文件体量已超过本领域四期全部计划内容 |
| 采集工具选型（PerfView / perfcollect / dotnet-monitor） | `dotnet-trace-collect` 的工具选择矩阵 | 这三者恰是本知识库明确标为「移出、后续期次」的缺口，官方已备齐 |
| 环境清点的完整问卷（OS / admin / 部署形态 / 复现特征） | `dotnet-trace-collect` 的 6 项 Inputs 表 | 比我们原设计的 3 项更细，重做即倒退 |

本 agent **专做**官方明确拒绝的那一半：

| 保留的能力 | 知识库支撑 | 官方是否覆盖 |
|---|---|---|
| SOS 输出逐列语义与判据解读 | `sos-threads-and-stacks.md` / `sos-heap-and-objects.md` / `sos-locks-and-async.md` | 明确拒绝 |
| 假设台账与跨轮消解 | 两张决策表的候选根因 + 74 条判据 | 无跨轮状态概念 |
| WPF 归因（Dispatcher 死锁、四类泄漏堆形态） | `wpf-dispatcher-deadlock.md` / `wpf-leak-patterns.md` | 全无 WPF 内容 |
| .NET Framework 4.x 的分析侧 | 全域三运行时共性层 | `dump-collect` 明确不支持 Framework |
| dump 处置合规（密级、版本库隔离、留存销毁） | `rules/01-dump-handling.md`——§ 1 密级 / § 2 版本库隔离 / § 4 留存销毁为 **MUST**（含 3 处「禁止」），§ 3 对外交付类型 / § 5 自动抓取落盘为 **SHOULD** | 不覆盖 |

### 1.3 与本仓既有 skill 的零重叠

| 既有 skill | 它负责 | 本 agent 负责 | 切线 |
|---|---|---|---|
| `csharp-code-review` | 静态读源码，判是否违反编码规范 | 读运行期取证输出，判根因 | 源码 vs 运行现场 |
| `wpf-code-review` | XAML / 绑定写法是否合规 | 已泄漏的绑定在堆上是什么形态 | 预防 vs 验尸 |
| `project-analyze` | 项目结构与技术栈概览 | 单次故障的根因定位 | 静态全貌 vs 动态单点 |

三者均不消费 `dotnet-debugging` 领域，本 agent 是该领域唯一消费者。

## 2. 产物结构：agent 编排 + skill 承载

### 2.1 两层分工（照官方范式）

单文件 agent 无法承载本设计的内容量——实测官方 `optimizing-dotnet-performance.agent.md` 仅 **63 行**，它把深度内容甩给 `analyzing-dotnet-performance` skill，`tools` 因此列了 `'task'` 与 `'skill'`，正文有「Pass 2 加载该 skill」的显式流程与 Skills 节声明加载时机。

本设计沿用该范式：

| 层 | 文件 | 承载什么 | 体量目标 |
|---|---|---|---|
| **编排层** | `agents/dotnet-diagnose.agent.md` | 三步主干、加载 skill 的时机、边界与免责声明、输出格式（含台账交接指令） | ≤ 80 行 |
| **承载层** | `skills/dotnet-diagnose-triage/SKILL.md` + `references/` | 判据两形态、征象映射表、两跳路由、B 组前置校验、崩溃日志定位、台账规则与修复方向分级、三结论强度、自检四项、失败处理、交接表 | SKILL.md 主干 + 按需下钻的 references |

agent 的 `tools` 因此**必须包含 skill 加载能力**（`'skill'` / `'Skill'`），这是与原设计的实质差异。

### 2.2 progressive disclosure 的落点

`references/` 下按下钻频次分文件，避免主干膨胀：

| 文件 | 内容 | 何时加载 |
|---|---|---|
| `references/symptom-hypothesis-map.md` | § 3.2 征象映射表（8 类 × 合并后完整候选集逐条）+ § 5.2 二维路由表 + § 5.2.1 第二跳去向清单 | 定下征象后 |
| `references/evidence-precheck.md` | § 5.1 B 组三项证据可用性校验 + 崩溃日志的能做/不能做与区分线 | 手里有 dump 或崩溃日志时 |
| `references/verdict-forms.md` | § 3.1 判据两种书写形态与检索方式 + § 4.4 修复方向四档分级与转述规则 | 每轮裁剪台账、以及出结论给修复方向时 |

SKILL.md 主干只保留台账规则（四字段 / 初始化 / 关闭 / 出口 / 跨轮续用）、自检四项、三结论强度、九条失败处理、§ 5.3 交接表与 § 5.4 合规约束——即每次都要用的部分。

**分文件的判据是「是否每轮都要读」**：征象映射表与路由表只在定征象那一轮用（之后台账已初始化完毕），证据校验只在收到新证据时用，判据形态与修复分级则在裁剪与收尾两个时点用。三者互不重叠，且都比主干长——留在主干会让每次调用都付出全量读取成本。

### 2.3 为什么不是「只建 skill」

agent 层仍有不可替代的作用：**独立上下文提供「不受主对话推理污染的第二双眼睛」**，这正是 § 6 自检环节所需的性质。若只建 skill，自检与推理在同一上下文里进行，自检会倾向于确认已得结论。

### 2.4 台账跨轮交接

agent 无跨调用状态，因此**台账的延续必须由输出自身携带**，不能指望调用方（Claude 侧主对话 / Codex 侧 manager）主动传递——调用方读不到 agent 正文。

两条硬规则：

1. **输出末尾固定附交接块**：台账原文 + 一句「继续排查请把以下台账连同新证据一并提供」。缺此块则跟轮必然丢失状态
2. **二次调用语义：续用，不重新初始化**。输入中带上一轮台账时，`已证实` / `已排除` 状态**保留**，只对 `待验` / `无法判定` 项用新证据继续裁剪。禁止重新按 § 4.1 全量初始化——那会抹掉上轮结论并重复已做过的裁剪

⚠️ 例外：新证据与上轮某条 `已排除` 结论矛盾时，该项**重开为 `待验`** 并注明矛盾来源——这是唯一允许翻转已关闭假设的情形。

### 2.5 双 harness 均等性（已核实）

| 维度 | Claude Code | Codex |
|---|---|---|
| agent 目录 | 插件根 `agents/`，**必须在 `.claude-plugin/plugin.json` 显式声明 `agents` 文件路径数组**（该字段是 replaces 语义，取代默认扫描） | 插件根 `agents/`（官方 `dotnet-diag/0.1.0/agents/` 实证） |
| 文件命名 | 无强制规则，`name` 字段优先，文件名为 fallback。⚠️ `.agent.md` 双扩展名来自 **VS Code / Copilot 约定，非 Claude Code 官方**（官方示例为纯 `.md`），沿用它是跟随微软 `dotnet/skills` 实践 | `*.agent.md`（官方实践） |
| agent 调 skill | `Skill` 工具 | `skill` 工具（官方 agent 的 `tools` 实证含 `'skill'`） |
| 子代理能力 | Agent 工具 | subagents 2026-03-14 GA，manager-worker，最多 8 并行 |

**同一份 `*.agent.md` 两侧都能加载**，`name`/`description`/`tools` 三字段是公共交集。

**两个必须注意的约束**：

1. **插件 agent 的 frontmatter 容错是静默降级而非报错**——解析失败时不报错，而是「文件名当 name、description 变成 `Agent from <plugin> plugin`、**全部字段被忽略**」。因此交付前必须跑 `claude plugin validate ./plugins/optimus-devops-plugin`
2. **`hooks` / `mcpServers` / `permissionMode` 三字段插件 agent 不支持**（Claude 侧安全限制），hook 形态的自动触发走不通

## 3. 核心设计：假设消解循环

主数据结构是**假设台账**，不是流程步骤。依据来自知识库自身的组织方式：一期 spec 契约二规定每条命令条目第 4 段为「判据：能证实 / 排除什么假设」，这些判据在语义上就是假设集上的消解算子，两张决策表的「候选根因」就是初始假设集。

因此 agent 正文只需写清循环规则与交接格式，全部判据按 `file § anchor` 引用——契约一「引用条目 ID，不复制正文」。

### 3.1 判据的两种实际书写形态（实测）

**这是台账关闭规则能否落地的前提，必须写准。** 实测知识库中判据有两种形态，agent 需同时识别：

| 形态 | 书写样式 | 分布 | 实测量 |
|---|---|---|---|
| **命令篇判据行** | 小节标题固定为 `### 判据：能证实 / 排除什么`，正文为 `<观察> → **证实**…` 或 `<观察> → **排除**…`（箭头 + 加粗，**无冒号**） | `sos-heap-and-objects.md`(13) / `sos-threads-and-stacks.md`(11) / `sos-locks-and-async.md`(8) / `wpf-leak-patterns.md`(10) / `wpf-dispatcher-deadlock.md`(9) | 51 处 |
| **决策表结论列** | 表格第三列的文字，如「全 0 → 排除 Monitor 死锁」「→ 证实线程池饥饿，转…」，**不加粗** | `debugging-decision-tree.md`(19 行) / `live-monitoring-decision.md`(11 行) | 30 行 |

⚠️ 带全角冒号的 `证实：` / `排除：` 在全域**零命中**——引用判据时不要按该形态检索。

### 3.2 假设集规模与征象映射（实测）

知识库有**两套征象命名**：dump 决策树 6 类、活体决策表 6 类，两套之间部分同义、部分互补。agent 必须按下表做映射，**不能把用户报的征象直接当成某一张表的行名**：

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

**八类征象**是对用户可见的统一命名（上表左列），十个小节是知识库的内部分布。以下三条规则消除二者的落差：

1. **台账按「合并后完整候选集」初始化，不按单张表的候选集**——否则用户报「挂起」但只有 counters 数据时，Monitor 死锁将永无入口（该假设只在 dump 表列出）
2. 手里的证据类型只决定**当前能用哪些判据裁剪**，不决定台账里有哪些假设。证据不足以裁剪的假设停在 `待验`，并注明「需 <某类证据> 才能判定」
3. 合并后有重复语义的假设（如 dump 表「线程池饥饿」与活体表 § 5 整节）**合并为一条**，依据列同时挂两处 anchor

### 3.3 两张决策表的重叠不是冗余

「GC 暂停」「锁竞争」「线程池饥饿」「托管泄漏」在 dump 表与活体表都出现，差别在取证手段：dump 表给单时点判据，活体表给「基线形态 / 异常形态 / 区分点」三元组（二期引入的范式）。同一假设在两表对应不同裁剪算子——这是路由必须按「证据类型 × 征象」二维定位的原因。

## 4. 台账数据结构

Markdown 表，随结论一并回传（agent 无跨调用状态，台账即交接物）。四个字段：

| 字段 | 内容 | 设计理由 |
|---|---|---|
| 假设 | 候选根因，**逐字取自决策表** | 逐字才能反查回知识库条目；自创措辞会断开与判据的对应关系 |
| 状态 | `待验` / `已证实` / `已排除` / `无法判定` | `无法判定` 独立于 `已排除`——「证据不足」与「证据表明不是」是两件事 |
| 依据 | `file § anchor` + 命中的具体判据句 | 契约一：引用不复制；也是自检环节的取证对象 |
| 证据来源 | 用户提供的哪段输出 | 可追溯每条结论建立在哪份证据上 |

### 4.1 初始化规则

定下征象后，**该征象「合并后完整候选集」里每一条都进台账（见 § 3.2），状态一律 `待验`**。不允许凭直觉预先淘汰，也不允许因当前证据类型不支持某假设就不登记——台账的核心价值是把「没想到」与「想到了但排除了」区分开。

### 4.2 关闭规则

只有命中知识库判据才能改状态（两种形态见 § 3.1）：

- `已排除` 必须引用一条含 `→ **排除**` 的判据行，或决策表结论列中表述排除的单元格
- `已证实` 必须引用一条含 `→ **证实**` 的判据行，或决策表结论列中表述证实的单元格
- 两者都未命中 → 停在 `待验`，或转 `无法判定`

**不允许靠推理关闭假设。** 这会让 agent 显得啰嗦（不能替用户跳步），是有意取舍。

### 4.3 出口条件

| 台账状态 | 出口 |
|---|---|
| 恰好一条 `已证实` | 收敛，给修复方向（跨领域引用 `knowledge-base/csharp/` 或 `wpf/`） |
| 全部 `已排除` / `无法判定` | 宣告「本征象候选集已穷尽」，给三条出路（见 § 7 的「台账全排除但问题仍在」一条） |
| 多条 `已证实` | **不强行择一**，如实并列，说明多因并存 |

多因并存在真实排查中常见（GC 压力 + 锁竞争经常同时命中），强行择一是误报来源。

### 4.4 修复方向从哪来：转述而非自造（实测）

「给修复方向」若靠 agent 自行推理，会产出无出处的建议。实测知识库**已把跨领域修复 anchor 内嵌在判据句里**，agent 的动作是原样转述，不是自己找映射。

例如 `wpf-leak-patterns.md § 2` 的证实判据句末尾原文即为：「修复方向（跨领域引用）见 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`」。

覆盖不均，且引用出现的**位置**决定了能不能当修复方向用。实测四种位置（逐处核对所在小节）：

| 位置 | 实测分布 | agent 怎么用 |
|---|---|---|
| **判据句内**（`→ **证实** … 修复方向见 X`） | 共 6 处：`wpf-leak-patterns.md § 2`、`wpf-dispatcher-deadlock.md § 3`（证实长任务）、`§ 4`（证实互等闭环）、`sos-heap-and-objects.md § 2`（静态集合字段）、`sos-locks-and-async.md § 3`（证实线程池饥饿）、`sos-threads-and-stacks.md § 4`（UI 线程异常） | **原样转述该 anchor**，不改写、不替换为自己认为更合适的目标。此档最可靠——修复方向与被证实的假设一对一绑定 |
| **反查表格行内** | `sos-heap-and-objects.md § 4. !gcroot` 的根链形态表两行：静态字段 → `csharp/rules/06-memory-resource.md § 5. 静态引用`；事件 `_invocationList` → `§ 4. 事件与委托泄漏` | 与判据句内同等可靠——按根链末端形态一对一反查 |
| **小节末「下一步」段** | `wpf-leak-patterns.md § 3`（`wpf/rules/10-performance.md § 7` + `wpf/rules/03-mvvm.md § 7`）、`§ 5`（`wpf/rules/09-threading.md § 7`） | 同样原样转述，但须注明它对应整节而非某一条判据 |
| **文件导语或正文叙述段** | 五篇 reference 导语各一处（`clr-runtime-anatomy` / `sos-heap-and-objects` / `sos-locks-and-async` / `wpf-dispatcher-deadlock` / `wpf-leak-patterns`）；另 `clr-runtime-anatomy § 5`、`wpf-dispatcher-deadlock § 2` 为正文叙述 | ⚠️ **粒度太粗，只能作兜底**——导语引用的是整份 rules 文件或宽泛章节，用它回答「怎么修这条具体根因」会给出跑偏的指向 |
| 四档都没有 | 两张决策表与取证工具篇（`dump-capture` / `dotnet-counters` / `dotnet-trace` / `dump-types-and-capability` / `symbols-and-tool-matching`）全篇无跨领域引用 | 回落到 `dotnet-debugging/README.md` 的相邻领域划界表（三行：`csharp/rules/06-memory-resource.md § 4/§6/§9`、`csharp/rules/11-observability.md § 7`、`wpf/rules/12-exceptions-crash.md § 1–3`）。**该表也覆盖不到时，如实说「本领域未登记该根因的修复侧引用」**，不自造 anchor |

⚠️ 硬约束：**修复方向只给 anchor 与一句话方向，不展开成修复方案**。展开即越界到 `csharp-code-review` / `wpf-code-review` 的地盘（§ 1.3 的切线是「验尸 vs 预防」），也会复制那两个领域的正文，违反契约一。

**另一处未被引用的资产**：`wpf-leak-patterns.md § 6. 根链形态图鉴速查表` 是六行「根链末端标志物 → 泄漏类型」的反查表，用途与前向路由相反——用户已有 `!gcroot` 输出但说不清征象时，从末端标志物直接反查类型。因此它挂在 § 5.2 路由表之外单列一条入口：**手里已有 `!gcroot` 输出的 WPF 场景，先走 § 6 反查表**，反查失败再回 § 1 常规起点（该表原文已给反查失败的出路）。

## 5. 主干流程

三步，收窄后不含取证执行：

```
Step 1  证据清点（轻量，仅分析所需）
Step 2  定征象 → 初始化台账 → 路由到判据篇目
Step 3  按判据裁剪台账 → 自检 → 出结论（含台账与下一步）
```

### 5.1 Step 1：证据清点

清点分为两组，**与官方 `dotnet-trace-collect` 的 6 项 Inputs 表不重叠**——官方问的是「采集前该用什么工具」（OS / admin / 部署形态 / 复现特征），本 agent 问的是「手里这份证据够不够支撑分析」。后者官方压根不问，因为它抓完即停。

**A 组 · 路由所需（3 项）**

| 清点项 | 取值 | 影响 |
|---|---|---|
| 手里有什么证据 | 命令输出 / dump 文件 / 崩溃日志 / 仅症状描述 | 决定能否进入判据裁剪 |
| 证据类型 | 单时点（dump / SOS 输出） / 时间序列（counters / trace 报告） | 决定用哪张表的判据裁剪（**不决定台账内容**，见 § 3.2 规则 2） |
| 运行时 | .NET Framework 4.x / .NET 6+ / 未知 | 决定哪些判据适用 |

**B 组 · 证据可用性前置校验（3 项，仅当手里有 dump 时）**

这三项都是「不校验就会白做整轮分析」的坎，且全部落在官方明确拒绝的分析侧：

| 校验项 | 判据来源 | 不校验的后果 |
|---|---|---|
| dump 位数与调试器是否匹配 | `dump-types-and-capability.md § 2. 位数必须匹配` | **静默失败**——不报错，只给出损坏的托管栈，极易误判为「dump 损坏」而重抓 |
| dump 类型是否支撑本次目标 | `dump-types-and-capability.md § 1. 四种类型的能力对照` | 用 Mini / Triage 查内存泄漏＝白做；OOM 崩溃须 Heap 或 Full（`debugging-decision-tree.md § 4` 末段） |
| 符号与 SOS 版本是否就位 | `symbols-and-tool-matching.md` 全篇四节 | 命令报错但原因在符号侧，会被误当成「命令不适用」。**知识库入口篇 `debugging-decision-tree.md` 第 7 行显式要求：「命令报错先查 `reference/symbols-and-tool-matching.md`」** |

B 组任一项不满足时，先给出补救路径（补符号 / 换调试器位数 / 重抓正确类型的 dump），**不进入台账循环**——基于不可用证据的裁剪结论是假结论。缺符号可降级分析的情形按 `symbols-and-tool-matching.md § 4. 缺符号时的降级读法` 判断：结论只依赖托管栈时不必补符号。

运行时未知**不阻塞**：按 `applies_to` 交集给通用判据，说明「若为 Framework 4.x 则以下第 N 条不适用」。`index.jsonl` 对 reference 强制必填 `applies_to` 正为此场景——二期活体篇全部标 `.NET 5+`，对 Framework 4.x 整章不适用。

**崩溃日志的定位（A 组列了它，必须给出去向）**

崩溃日志既不是 SOS 输出也不是 dump，B 组三项校验对它不适用，而 § 7 又把「业务日志」判为不可解读——若不单独规定，它会成为「合法输入但无处可去」的一类。规定如下：

| 是什么 | 能做什么 | 不能做什么 |
|---|---|---|
| .NET 未处理异常记录（异常类型 + 托管堆栈 + `InnerException` 链）、WER 记录的错误代码与故障模块 | ① 定征象为「崩溃退出」；② 按异常类型初筛——`debugging-decision-tree.md § 4` 首段把该征象拆为「未处理托管异常 / `StackOverflowException` / `OutOfMemoryException` / 原生代码崩溃」四支，日志里的异常类型直接对上其中一支；③ 借 `sos-threads-and-stacks.md § 4. !pe` 的 `InnerException` 链读法找根因异常层 | 裁剪任何依赖堆或线程状态的假设——日志无托管堆快照、无其余线程栈。这些假设必须停在 `待验` 并注明「需 § 4 所列 dump 才能判定」 |

⚠️ `!pe` 那条判据的**原文形态是 `InnerException` 非 `<none>` → 证实存在链式异常**，而 `<none>` 是 SOS 输出的标记，日志文本里不存在。因此只能迁移「链式异常须逐层展开才见根因」这一读法，不能声称命中了该判据：日志已完整打印异常链时可据链末层定位；只打印了最外层时须注明「可能存在未展开的内层异常」，不得按最外层异常直接定根因。

**与「业务日志不可解读」的区分线**：含托管异常类型与堆栈帧的是崩溃日志（可用），只含业务语义文字（`用户登录失败`、`订单处理超时`）的是业务日志（不可用）。同一个文件里两者混排时，只取异常记录段。

**仅有症状描述、无任何取证输出时**：不进入台账循环。给出该征象需要什么证据（引用对应决策表的取证命令列），并明确告知取证由用户自行完成或转官方 `dump-collect` / `dotnet-trace-collect`。这是收窄后的硬边界。

### 5.2 Step 2：路由表

按 `证据类型 × 征象` 二维定位，只写去向不写内容（知识库 README 认可的「固定映射」消费模式）：

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

**异常风暴格是「部分可用」，不是空格。** `live-monitoring-decision.md § 4` 原文：「dump 只能看到抓取那一刻**当前未处理**的异常（`debugging-decision-tree.md § 4` 里 `!threads` 的 `Exception` 列），对已经被 `catch` 吞掉的异常没有任何痕迹留存」。据此拆分：

| 异常风暴的候选根因 | dump 能否覆盖 |
|---|---|
| 依赖不可用（持续抛出、未被吞） | ✅ 可用——`!threads` 的 `Exception` 列 + `sos-threads-and-stacks.md § 4. !pe` 展开 `InnerException` 链 |
| 参数校验失败风暴 | ✅ 同上 |
| 吞异常的重试循环（`catch` 后立即重试） | ❌ **天生盲**——吞掉的异常在抓取时刻已不存在于任何线程的当前异常状态 |

因此该格的正确话术是「dump 可证实前两类、**无法排除**第三类」——第三类须停在 `无法判定` 并注明需 first-chance 异常计数器（时间序列）才能判定，不得因 dump 未见异常就报「无异常风暴」。

### 5.2.1 路由是两跳而非一跳（实测）

上表右列不是终点。实测活体篇有 **6 条判据句**写成「→ 证实 X，**转** `sos-*.md § N`」形式（§1 两条、§3 两条、§4 一条、§5 一条），共指向 7 个第二跳目标；最长的一条是 `live-monitoring-decision.md § 5`：「证实线程池饥饿，转 `sos-locks-and-async.md § 3. !threadpool` 核对当前线程状态，**再转** `sos-threads-and-stacks.md § 2. !clrstack` 找出占用工作线程却卡在同步等待的调用栈」。

据此两条规则：

1. **第一跳定征象与候选集，第二跳才拿到可裁剪的判据**。路由表给的是第一跳；第二跳去向写在判据句里，agent 须原样跟随，不得停在第一跳就下结论
2. ⚠️ **第二跳往往需要另一类证据**——SOS 命令篇要么读 dump、要么连活体进程。只有 counters 数据的用户走到第二跳会断链，此时该假设停在 `待验`，注明「时间序列已指向 X，确认需 `sos-*.md § N` 所需的 dump 或活体连接」。**这不是 `无法判定`**：证据方向已明确，只是差最后一步取证，结论强度记为「推测」

这与 § 5.2「只写去向不写内容」不冲突：写的仍是去向，只是去向是一条链而非单点。链的中间节点逐个列出，链上每一跳的内容仍不复制。

### 5.3 与官方产物的交接点

需要新证据时，agent 的动作是**给出取证要求并指明去向**，自己不执行：

| 需要什么 | 交接去向 |
|---|---|
| dump 文件（modern .NET） | 官方 `dump-collect` skill；**官方插件未安装或用户不便使用时，无条件回落**到本知识库 `dump-capture.md § 2. dotnet-dump collect` / `§ 3. createdump` / `§ 5. DOTNET_DbgEnableMiniDump` |
| trace / counters 数据 | 官方 `dotnet-trace-collect` skill；未安装时回落到本知识库 `dotnet-counters.md` / `dotnet-trace.md` |
| dump 文件（.NET Framework 4.x） | 官方两者均不支持 Framework，只能引用本知识库 `dump-capture.md § 1. procdump` 与 `§ 4. WER LocalDumps` |

**回落不是降级路径，是默认可用路径。** 官方插件是「若已安装则优先推荐」，而非前置依赖——本知识库 `dump-capture.md` 五节完整覆盖 procdump / dotnet-dump / createdump / WER / `DOTNET_DbgEnableMiniDump`，无官方插件亦可给出完整抓取指引。这是 § 8.6「不依赖官方插件为硬前置」得以成立的实际保障。

### 5.4 dump 处置合规：建议抓取时必须一并给出

agent 不执行抓取，但**只要它建议用户去抓 dump，就须同时给出处置约束**——否则 § 1.2 承诺的「dump 处置合规」无落点。三条按级别区分，不可把 SHOULD 说成 MUST：

| 约束 | 级别 | 内容 |
|---|---|---|
| `rules/01-dump-handling.md § 1. 生产 dump 的密级` | **MUST** | 生产 dump 含完整进程内存（连接字符串、令牌、用户数据），须按其密级处置；禁止随手发送至外部渠道 |
| `§ 2. 版本库隔离` | **MUST** | dump 不得落进 git 工作树，建议路径必须在仓库外 |
| `§ 4. 留存期限与销毁` | **MUST** | 分析结束后按留存期限销毁，不长期堆放 |
| `§ 3. 对外交付的类型选择` | SHOULD | 需对外交付时优先选能力足够的最小类型 |
| `§ 5. 自动抓取的落盘位置` | SHOULD | 配置自动抓取时落盘位置的选择建议 |

时机：给出抓取建议的同一条回复内一并给出，不等用户询问——dump 抓完再谈密级已经晚了。

`tools` 不含 `Bash`——收窄后 agent 不执行任何诊断命令，只读文件与推理。这消除了原设计中「重量级动作 CHECKPOINT」的整块复杂度，但**不消除处置合规的告知义务**（见 § 5.4）。

## 6. 自检环节

AGENTS.md 要求新产物自检「引导器 / 传感器」配对。本 agent 是引导器，传感器**内建为出结论前的强制环节**——agent 的独立上下文本身就提供了「不受主对话推理污染」的性质，无需另建产物。

四项逐条自答，不通过不得出结论：

| 自检项 | 不通过时 |
|---|---|
| 每条 `已证实`/`已排除` 是否都挂着 `file § anchor` 与命中的判据句？ | 退回 `待验`，说明缺哪条证据 |
| 结论有没有超出证据？ | 降级为「推测」，标出还需哪类证据 |
| 台账里 `待验` 的假设有没有被无声跳过？ | 显式列出未验项 |
| 运行时适用性核对过没有？（`applies_to` 是否覆盖目标运行时） | 撤下不适用的判据 |

第二项是重心。诊断最典型的失败模式不是查错方向，而是**证据只够支撑「可能是」，却报成了「就是」**。因此强制区分三种结论强度并显式标出：

| 强度 | 判定 |
|---|---|
| **已确认** | 命中某条 `证实：…` 判据，且该判据前置条件全部满足 |
| **推测** | 证据方向一致但判据未完整命中，须写明还缺哪类证据 |
| **超出覆盖** | 知识库无对应判据（非托管泄漏细节、Linux 容器专属＝四期未做、`AssemblyLoadContext` 卸载＝一期已登记缺口、NativeAOT＝全域未覆盖） |

第三项防「报喜不报忧」：找到一条证实项就收工、台账剩余 `待验` 悄悄消失。漏报比误报更难被发现。

### 6.1 结论免责声明

沿用官方 agent 的做法（`optimizing-dotnet-performance.agent.md` 强制结尾挂免责声明），本 agent 结论末尾同样固定附一句：诊断结论由 AI 生成、具非确定性，可能误报或漏报，投入修复前须人工复核。

理由不是形式合规——诊断结论会驱动生产环境的修复动作，其错误代价高于代码审查建议。

## 7. 失败处理

| 触发条件 | 一线处理 |
|---|---|
| 只给一句「程序崩了」，无任何证据 | 不猜。按 § 5.1 给出该征象所需证据，指向官方采集 skill 或本知识库 Framework 路径 |
| 粘的输出不是取证输出（纯业务日志：只有 `用户登录失败` 这类业务语义文字，无异常类型与堆栈帧） | 明确说明不可解读，指出该取哪类证据。**先按 § 5.1 的区分线判一次**——含托管异常类型与堆栈帧的属崩溃日志，可用，不得一并判为不可解读 |
| 输出被截断 | 基于可见部分给方向，标「基于截断输出」，说明完整输出能多排除哪些假设 |
| 征象与证据矛盾（说内存涨但托管堆很小） | 不迁就描述，指出矛盾即线索——转非托管泄漏路径 |
| 症状不属八类征象任一 | 如实说超出覆盖，**不硬套最像的一类** |
| 台账全排除但问题仍在 | 宣告候选集穷尽，给三条出路：换征象 / 换证据类型 / 超出知识库范围 |
| 第一跳已证实但第二跳缺证据（如只有 counters，判据句要求转 `sos-*.md`） | 停在 `待验`，结论强度记「推测」，注明「时间序列已指向 X，确认需 `sos-*.md § N` 所需的 dump 或活体连接」。**不得记 `无法判定`**——方向已明确，只差最后一步取证（§ 5.2.1 规则 2） |
| 用户报「命令报错了 / 输出一堆错误」 | **先查符号与工具匹配**（`symbols-and-tool-matching.md` 四节），不要当成「证据不足」而降级结论强度——报错原因多在符号或 SOS 版本侧，与假设裁剪无关。这是知识库入口篇 `debugging-decision-tree.md` 第 7 行的显式要求 |
| 用户要求直接抓 dump 或跑 trace | 收窄后不执行，转官方 skill 或回落本知识库（§ 5.3），并一并给出处置合规约束（§ 5.4） |

「症状不属八类征象任一」那条是最大的诱惑点：八类征象覆盖不了所有现场（如「启动就闪退」既非崩溃退出也非启动阶段慢），套近似入口会让整条推理链建立在错误的候选集上，比直接说「不覆盖」更有害。

## 8. 交付物清单

### 8.1 新增文件

| 文件 | 内容 | 适用规范 |
|---|---|---|
| `plugins/optimus-devops-plugin/agents/dotnet-diagnose.agent.md` | 编排层：三步主干、加载 skill 时机、边界、输出格式（含台账交接块）、免责声明。**≤ 80 行** | `.claude/rules/agent-conventions.md`（四字段 frontmatter，**有 CHANGELOG/README，位置在 `agent-docs/`**） |
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/CHANGELOG.md` | 初始 `[1.0.0]` — **agent 版本号真源** | `.claude/rules/doc-conventions.md` |
| `plugins/optimus-devops-plugin/agent-docs/dotnet-diagnose/README.md` | 六章节，其中「所处层级」按与相邻产物的划界画图、「触发词」改为调用方式与触发面 | `.claude/rules/doc-conventions.md`（agent 分栏） |
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | **已在本次规范实施时新建**（`name` + `version`）；本次只需**增补** `"agents": ["./agents/dotnet-diagnose.agent.md"]` | `.claude/rules/agent-conventions.md` |
| `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/SKILL.md` | 承载层主干：台账规则（含跨轮续用）、自检四项、三结论强度、九条失败处理、交接表、合规约束 | **skill 完整规范**（六字段 + metadata.version 1.0.0） |
| `.../skills/dotnet-diagnose-triage/references/symptom-hypothesis-map.md` | 征象映射表（8 类 × 合并候选集）+ 二维路由表 + 第二跳去向清单 | — |
| `.../skills/dotnet-diagnose-triage/references/evidence-precheck.md` | B 组三项证据可用性校验 + 崩溃日志定位与区分线 | — |
| `.../skills/dotnet-diagnose-triage/references/verdict-forms.md` | 判据两种书写形态 + 修复方向四档分级与转述规则 | — |
| `.../skills/dotnet-diagnose-triage/CHANGELOG.md` | 初始 `[1.0.0]` | skill 规范强制 |
| `.../skills/dotnet-diagnose-triage/README.md` | 六章节（含 ASCII 层级图与依赖图） | skill 规范强制（`plugins/*/skills/` 下必须） |
| `.../skills/dotnet-diagnose-triage/known-issues.md` | darwin-skill 基线评估记录（含评分依据与评估模式） | 持续优化机制（2026-08-30 起新建 skill 适用） |
| `.../skills/dotnet-diagnose-triage/test-cases/golden.md` | 七个黄金测例（见 § 9） | 本 spec 自行引入 |

**结构变化的连带后果**：skill 层回归 skill 的完整规范，因此 CHANGELOG / README / known-issues / **darwin-skill 基线评估**全部适用。**agent 层的豁免范围已收窄**：CHANGELOG / README **不再豁免**（位置在 `agent-docs/dotnet-diagnose/`），仅 `known-issues.md` 与 darwin-skill 评分门禁仍豁免（§ 8.5）。

### 8.2 frontmatter 规格

照官方 `dotnet-diag` 范式，仅用两侧公共交集字段：

```yaml
---
name: dotnet-diagnose
description: <见 § 8.3>
tools: ['read', 'search', 'skill', 'Read', 'Glob', 'Grep', 'Skill', 'read_file', 'glob', 'grep_search']
license: MIT
---
```

- **`tools` 必须含 skill 加载能力**（`'skill'` / `'Skill'`）——承载层在 skill 里，无此能力则 agent 读不到判据表（官方 `optimizing-dotnet-performance.agent.md` 同理列了 `'task'`、`'skill'`）
- **不含任何写入或执行工具**：收窄后不执行命令、不修改文件。**因此台账不落文件，只能靠输出自带交接块跟轮**（§ 2.4）
- **`tools` 列跨 harness 别名**：官方做法，同一能力两侧工具名不同
- **不加 `metadata.version`**：插件 agent 的 11 个合法字段里**不含 `metadata`**（与 skill 不同——skill 有 agentskills.io 规范明确留出的 `metadata` 自由映射）；且 Claude 侧 frontmatter 容错是静默降级（解析失败则全部字段被忽略），加未知键是在赌文档空白。**agent 版本号记在 `agent-docs/dotnet-diagnose/CHANGELOG.md` 的最新 `## [x.y.z]`**，首版 `1.0.0`，与所属插件版本互不换算
- **不加 `model` / `effort` / `maxTurns`**：Claude 侧独有，加入即产生两侧不对等

### 8.3 description 须写明划界

description 是两侧唯一的触发匹配依据，必须显式写清与官方 `dotnet-diag` 的分工，避免触发词互抢：

> 解读 .NET 取证输出并定位根因：SOS 命令输出逐列解读、假设台账消解、WPF 专属归因（Dispatcher 死锁与四类泄漏堆形态）、.NET Framework 4.x 分析。**用于已经拿到 dump / SOS 输出 / trace 报告之后**。若只需配置或抓取 dump、选择采集工具，用 `dump-collect` 或 `dotnet-trace-collect`（本 agent 不执行取证命令）。

**划界只能单向生效，须如实承认**：我们改不了官方插件的 description（它是只读的上游产物），因此「用户在官方 skill 那边被拒后转到我们这里」这条路不存在——官方 `dump-collect` 的 Stop Signals 只说「本 skill 不覆盖分析」，不会指向任何替代产物。可控的只有反向：**用户找到我们、但需求属于取证侧时，由我们指回官方**（§ 5.3 的交接表）。

两条随之而来的设计约束：

1. **description 必须自带「什么时候不该用我」**——不能指望官方那边把用户拦到我们门口，只能靠我们自己的 description 精确到「已经拿到证据之后」，避免取证阶段的用户误触发后浪费一轮
2. ⚠️ **语言不对称的实际影响**：官方产物全英文，本 agent 与知识库全中文。两侧 description 不在同一语言空间做语义匹配，**触发词互抢的风险实际低于同语言场景**，但代价是英文提问的用户较难命中我们。取舍：description 主体保持中文（与知识库、其余 48 个 skill 一致），**仅在其中保留 `dump` / `SOS` / `trace` / `WPF` / `.NET Framework` 等原形技术标识符**——这些词在中英文提问里都会出现，是跨语言的公共触发面。不做双语 description（两个 harness 均按单一 description 匹配，双语会稀释语义密度）

### 8.4 同期必须改动的既有文件

| 文件 | 改动 | 不改的后果 |
|---|---|---|
| `plugins/optimus-devops-plugin/.claude-plugin/plugin.json` | `version` `1.0.0` → **`1.1.0`**（Minor，新增 agent + skill）；增补 `"agents": ["./agents/dotnet-diagnose.agent.md"]` | 「功能变了版本号不变 = 不完整交付」；不声明 `agents` 则失去 replaces 语义的防假 agent 保护 |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `version` **同一次改动内一起升到 `1.1.0`**（与上一行同值，无先后主从）；`description` 与 `interface.longDescription` 两处同步；`interface.capabilities` 由 `["Skills"]` 增补 agent 能力（**须先验证该取值合法，不合法则不改此项**） | 两份不同值会被 `commit-cc-plugin` 的同值校验阻断 |
| `.claude-plugin/marketplace.json` | **顶层 `version` 保持 `14.0.0` 不动**；只改 `optimus-devops-plugin` 的 `description` 加入诊断能力 | 顶层仅在增删插件时升——本次是给已有插件加内容，不改集合构成；description 不改则用户看不到该能力 |
| `knowledge-base/catalog.json` | `dotnet-debugging` 的 `consumers` 由 `[]` 改为 `["plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage"]`（**登记 skill 层而非 agent 层**——判据引用全部落在 skill 与其 `references/` 中，agent 只负责调度）；`reviewed_at` 更新 | 领域首个消费者未登记 |
| `knowledge-base/dotnet-debugging/README.md` | 「适用范围与读者」段的「本领域一期无固定 skill 消费者」改为指向本 agent | 该句已过时，属陈述性错误 |
| `AGENTS.md` | ✅ **已完成**（本 spec 撰写期间同步补入）：① 版本管理表「新增 skill/agent/hook/command」；② darwin-skill 门禁只约束 skill 的说明；③ Skill 分层节点出 agent 为第三种产物形态并指向细则 | 本仓首个 agent 无规范可依，后续 agent 各行其是 |
| `.claude/rules/agent-conventions.md` | ✅ **已完成**（由 `2026-09-06-rules-split-and-agent-docs-design.md` 交付）：agent 规范已从 `skill-conventions.md` 拆出为独立文件，`paths` 为 `plugins/*/agents/*.md` 与 `plugins/*/agents/**/*.md` 两条（用 `*.md` 而非 `*.agent.md`，纯 `.md` 的 agent 也能命中；两条并存是因为平铺文件在严格 `**` 语义下不匹配单条 `**/*.md`）；含选型判据、`agents/` 目录硬约束、frontmatter、配套文档位置、独立版本化、darwin-skill 豁免 | 同上 |
| `.claude/skills/knowledge-base-maintain/scripts/check_refs.py` | `CONSUMER_GLOBS` 增 `plugins/*/skills/*/references/*.md` 一行 | 见下 |

**`check_refs.py` 覆盖面（实测）**：现有 `CONSUMER_GLOBS` 四条为 `plugins/*/skills/*/SKILL.md`、`plugins/*/skills/*/*REFERENCE*.md`、`knowledge-base/*/rules/*.md`、`knowledge-base/*/reference/*.md`。

| 新增文件 | 是否被现有 glob 覆盖 |
|---|---|
| `skills/dotnet-diagnose-triage/SKILL.md` | ✅ **自动覆盖**（命中第一条 glob）——这是改为两层结构的一个附带收益：agent 单层方案下判据引用全在 `agents/` 里，脚本一条都查不到 |
| `skills/dotnet-diagnose-triage/references/*.md` | ❌ 不覆盖（第二条 glob 是同级 `*REFERENCE*.md`，不含子目录）。**而这三个文件恰是 anchor 密度最高的**（征象映射表逐条挂 anchor），因此补 glob 一行 |
| `agents/dotnet-diagnose.agent.md` | ❌ 不覆盖，**且不补**——agent 层按 § 2.1 只写编排，不含 `file § anchor` 引用，无可查对象。若日后 agent 正文出现 anchor，说明分层被破坏，该由 § 10.2 的「判据表不出现在 agent 内」一项拦住 |

补 glob 属 `.claude/` 下改动，**不升版本号**（AGENTS.md 版本管理表第一行）。改动后须回归跑一次全库 `check_refs.py`，确认新纳入的 glob 未让既有文件报错。

### 8.5 版本升级的规范空白（已消除）与 darwin-skill 门禁的实际落点

AGENTS.md 的版本管理节已由 `2026-09-06-rules-split-and-agent-docs-design.md` 整节重写：版本落点下移至每插件的两份 `plugin.json`，含「什么改动升哪一层」的触发矩阵；`darwin-skill` 评分门禁只约束 skill——其 9 维 rubric 针对 SKILL.md 结构，对 agent 无对应维度。

**agent 层的豁免范围已收窄，须按项区分**：CHANGELOG / README **不再豁免**（`agent-conventions.md` 定为必须，位置在 `agent-docs/<name>/`），仅 `known-issues.md` 与 darwin-skill 评分门禁仍豁免——后者是因为 `known-issues.md` 本身就是 darwin-skill 循环的输入产物，两者同进同退。

**darwin-skill 按层区分：**

| 层 | darwin-skill | 依据 |
|---|---|---|
| `agents/dotnet-diagnose.agent.md` | **不跑**，按 § 10 验收清单人工核验 | rubric 无对应维度 |
| `skills/dotnet-diagnose-triage/` | **必须跑基线评估**，结果记入 `known-issues.md`（含评分依据与评估模式 `full_test`/`dry_run`） | 新建 skill，按 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md § 1. 创建后强制基线评估` |

新建 skill 无「改动前分数」可比，因此不设通过门槛；但基线分过低（rubric 明显缺项）时先修再提交。

### 8.6 明确不改动

- **不改 `knowledge-base/dotnet-debugging/` 正文与 `index.jsonl`**：本 agent 只消费不新增判据。领域版本 1.2.0 不变（README 消费者一句属陈述性修正，不构成条目变更）
- **不建配对校验产物**：传感器已内建为 § 6 自检环节
- **不写四期内容**：Linux 容器专属判据未入库，agent 内标为「超出覆盖」
- **不依赖官方插件为硬前置**：§ 5.3 的交接是建议性指引；官方插件未安装时 agent 仍可正常工作（只是取证需用户自行完成）

## 9. 黄金测例集

**存在理由**：仅验「结构齐备」的验收标准，无法阻止「agent 正文写得漂亮但诊断结论是错的」。本节把结构验收转化为可验证的行为目标（对齐 CLAUDE.md 行为准则第 4 条「目标驱动执行」）。

### 9.1 交付形态

文件：`plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage/test-cases/golden.md`

放在 skill 层而非 agent 层：测例考的全是判据引用、台账裁剪、前置校验——这些内容都在 skill 与其 `references/` 里，测例与被测内容同目录才不会失联。

每例四段：**输入**（症状 + 取证输出片段）/ **预期台账**（各假设的目标状态）/ **预期结论强度** / **考什么**。输出片段的列名与语义须与知识库正文一致（如 `!syncblk` 的 `MonitorHeld` 编码规则取自 `sos-locks-and-async.md § 1`），不得自造列名。

交付时逐例人工跑一遍，实际输出与预期不符即为不通过。

### 9.2 七个测例

| # | 输入 | 预期结果 | 考什么 |
|---|---|---|---|
| 1 | 「界面卡死」+ `!syncblk` 显示两个同步块 `MonitorHeld` 分别为 3、3，两个 `Owning Thread Info` 互为对方的等待方 | 台账「Monitor 死锁」→ `已证实`，依据挂 `sos-locks-and-async.md § 1`；结论强度 **已确认** | 能否读懂 `MonitorHeld` 编码（等待线程数 =(值−1)/2）并识别循环等待 |
| 2 | 「内存一直涨」+ **单份** `!dumpheap -stat` 显示某业务类型 Count 很高 | 该假设停在 `待验` 或 `无法判定`，注明需第二次采样；结论强度 **推测**，**不得报已确认** | § 6 自检第二项：单时点数据不足以支撑「持续增长」判断（`sos-heap-and-objects.md § 1` 判据要求两次 `-stat` 对比） |
| 3 | WPF 应用「窗口关不掉」+ `!gcroot` 输出根链末端落在 `MS.Internal.Data` 命名空间的事件管理器 | 「Binding 泄漏」→ `已证实`，依据挂 `wpf-leak-patterns.md § 2`；修复方向**原样转述**该判据句自带的 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`，不改写为其他目标 | WPF 分支路由 + § 4.4 第一档「判据句内引用原样转述」（本 agent 相对官方的独有价值） |
| 4 | 「内存一直涨」+ 全部 WPF 类型实例数均在预期内 | 排除 § 2/§3/§5 三类，**§ 4 弱事件泄漏必须仍为 `待验`** 并注明需另按内部监听表体积判断 | 三期最终审查那处 Important 的落地检验——`wpf-leak-patterns.md § 1` 的排除判据已显式限定范围，agent 不得越界排除 |
| 5 | 「挂起」+ 只有 `dotnet-counters` 时间序列数据显示队列长度持续 > 0、线程数顶在爬坡上限、CPU 不高 | ① 台账须含**完整 7 条**候选（含只在 dump 表出现的 Monitor 死锁）；② 「线程池饥饿」命中 `live-monitoring-decision.md § 5` 第一跳，但该判据句要求转 `sos-locks-and-async.md § 3` 再转 `sos-threads-and-stacks.md § 2`——**无 dump 无活体连接，第二跳断链**，故停在 `待验`、强度记 **推测**，注明所需证据；③ **不得记 `无法判定`** | § 3.2 规则 1/2 + § 5.2.1 规则 2：合并候选集初始化 + 第二跳断链的正确降级 |
| 6 | 「程序崩了」+ 提供一个 Mini 类型 dump，目标是查内存泄漏 | **不进入台账循环**，先报 dump 类型不支撑该目标（`dump-types-and-capability.md § 1`），给出重抓 Heap/Full 的补救路径 | § 5.1 B 组前置校验：不校验证据可用性就整轮白做 |
| 7 | 「程序自动退出」+ 一份日志，含 `System.InvalidOperationException` 的类型名与三帧托管堆栈，另混有若干条 `订单处理超时` 业务行 | ① **只取异常记录段**，业务行不参与判断；② 定征象「崩溃退出」并按 `debugging-decision-tree.md § 4` 首段四支对上「未处理托管异常」；③ 日志只打印了最外层异常，须注明「可能存在未展开的内层异常」，**不得按最外层直接定根因**；④ 依赖堆或其余线程栈的假设一律停在 `待验` | § 5.1 崩溃日志条：与业务日志的区分线 + `!pe` 判据只能借读法不能声称命中 |

### 9.3 测例覆盖对应关系

| 设计要素 | 覆盖测例 |
|---|---|
| 判据两种书写形态（§ 3.1） | 1（命令篇加粗形态）、5（决策表结论列形态） |
| 台账按合并候选集初始化（§ 3.2） | 5 |
| 三种结论强度（§ 6） | 1（已确认）、2 与 5（推测） |
| 自检第二项「结论不得超出证据」（§ 6） | 2、4、7 |
| 修复方向原样转述（§ 4.4） | 3 |
| 第二跳断链的降级（§ 5.2.1） | 5 |
| 崩溃日志的可用边界（§ 5.1） | 7 |
| B 组证据可用性前置校验（§ 5.1） | 6 |
| WPF 分支与跨领域修复引用（§ 5.2） | 3、4 |

## 10. 验收标准

### 10.1 行为正确性（唯一验「诊断对不对」的一组）

- [ ] **七个黄金测例逐例人工跑通**（§ 9.2），实际台账与结论强度须与预期一致——其余各项只验结构
- [ ] 判据引用按实测形态（`→ **证实**` / `→ **排除**` 或决策表结论列），**未使用全域零命中的 `证实：` 形态**
- [ ] 台账初始化按 § 3.2 的「合并后完整候选集」，八类征象与十个知识库小节的映射表已落地
- [ ] 二次调用为「续用」语义：带上轮台账时 `已证实`/`已排除` 保留，仅重裁 `待验`/`无法判定`（§ 2.4）

### 10.2 agent 层（编排）

- [ ] `agents/dotnet-diagnose.agent.md` 交付，frontmatter 仅 `name`/`description`/`tools`/`license` 四字段
- [ ] 正文 **≤ 80 行**，只含三步主干、加载 skill 时机、边界、输出格式、免责声明——判据表不出现在 agent 内
- [ ] `tools` 含 skill 加载能力（`'skill'` / `'Skill'`），**不含任何写入 / 执行类工具**
- [ ] 输出末尾固定含台账交接块与「继续排查请把台账连同新证据一并提供」（§ 2.4）
- [ ] 结论免责声明已固定在输出末尾
- [ ] description 含与官方 `dump-collect` / `dotnet-trace-collect` 的划界句
- [ ] `agent-docs/dotnet-diagnose/CHANGELOG.md` 初始 `[1.0.0]`；`README.md` 六章节齐备，「所处层级」按与相邻产物的划界画图（非 category 层级图）、「触发词」为调用方式与触发面
- [ ] README 头部的版本号与 `agent-docs/dotnet-diagnose/CHANGELOG.md` 最新条目**一致**
- [ ] `agents/` 目录下**只有** `dotnet-diagnose.agent.md` 一个文件，无 CHANGELOG / README / 任何辅助文件（否则会注册成假 agent）
- [ ] `.claude-plugin/plugin.json` 已含 `"agents": ["./agents/dotnet-diagnose.agent.md"]`，且原有 `name` / `version` 未被覆盖
- [ ] `claude plugin validate ./plugins/optimus-devops-plugin` 通过——**必查项**：frontmatter 解析失败是静默降级而非报错，肉眼看不出

### 10.3 skill 层（承载）

- [ ] `SKILL.md` 六字段 frontmatter，`metadata.version: "1.0.0"`、`author: desktop client team`、`category: quality`
- [ ] `CHANGELOG.md` 初始 `[1.0.0]`；`README.md` 六章节齐备且全 ASCII box-drawing
- [ ] **darwin-skill 基线分已取得**，`known-issues.md` 含评分依据与评估模式（非仅分数）——§ 8.5 该门禁只对本层生效
- [ ] `references/` 三文件按 § 2.2 分工，SKILL.md 主干只留每次都用的部分（台账规则 / 自检四项 / 三结论强度 / 九条失败处理 / 交接表 / 合规约束）——征象映射表与路由表**不留在主干**
- [ ] § 5.1 B 组三项证据可用性校验（位数 / dump 类型 / 符号）在正文中出现，且各挂对应 anchor
- [ ] `symbols-and-tool-matching.md` 与 `dump-types-and-capability.md` 已被引用（知识库入口篇第 7 行显式要求）
- [ ] 全部知识库引用均为 `file § anchor` 形式，**无正文复制**（抽查 5 处逐字比对）
- [ ] 路由表 8 行 × 2 列的 12 个去向全部实测存在（`check_refs.py` 补 glob 后覆盖 SKILL.md 与 `references/`，以脚本 PASS 为准）
- [ ] § 5.2.1 的第二跳去向（6 条判据句共 7 个 `sos-*.md § N` 目标）已落地，且写明第二跳可能需另一类证据
- [ ] § 4.4 的修复方向四档分级已落地：判据句内 6 处与反查表 2 行原样转述，导语级引用只作兜底，无自造 anchor
- [ ] `wpf-leak-patterns.md § 6` 反查表作为「已有 `!gcroot` 输出」的独立入口已落地（§ 4.4）
- [ ] 崩溃日志的能做 / 不能做两栏已落地，且与「业务日志不可解读」的区分线写明（§ 5.1）
- [ ] 四个「—」如实保留，各配一句「需先换一类证据」说明
- [ ] 台账四状态、三结论强度、四自检项、**九条**失败处理全部落地
- [ ] `rules/01-dump-handling.md § 1/§2/§4` 三条 MUST 在 § 5.4 建议抓取的话术中出现，级别未被抬高或降低

### 10.4 全局

- [ ] `python .claude/skills/knowledge-base-maintain/scripts/check_index.py` PASS，条目数不变（全局 576 / 领域 74）
- [ ] `check_refs.py` PASS（含新补的 `plugins/*/skills/*/references/*.md` glob，回归确认既有文件未被新 glob 带出报错）
- [ ] devops 两份 `plugin.json`（`.claude-plugin/` 与 `.codex-plugin/`）版本**同值**且已升 **Minor**（新增 agent + skill）；`marketplace.json` 顶层 `version` **保持 `14.0.0` 未动**
- [ ] `python .claude/skills/commit-cc-plugin/scripts/check_plugin_versions.py .` 通过（两份同值校验）
- [ ] `catalog.json` consumers 已登记为 skill 层路径，JSON 可解析
- [ ] `AGENTS.md` 与 `.claude/rules/agent-conventions.md` 的 agent 规范已就位（由 `2026-09-06-rules-split-and-agent-docs-design.md` 交付，实施时只需复核未被回退）
- [ ] 全部改动经 `commit-cc-plugin` 推送

## 11. 不在本次范围

| 项 | 归属 |
|---|---|
| 知识库四期（Linux 容器专属） | 用户已明确暂停 |
| 取证命令的执行与 dump 抓取 | 官方 `dump-collect` / `dotnet-trace-collect`（Framework 4.x 除外，引用本知识库） |
| 采集工具选型矩阵（PerfView / perfcollect / dotnet-monitor） | 官方 `dotnet-trace-collect` |
| NativeAOT 诊断 | 官方 `dump-collect` 的 `nativeaot-dumps.md`；本知识库全域未覆盖 |
| `AssemblyLoadContext` 与可收集程序集卸载 | 一期已登记的知识库缺口 |
| Hook 形态自动触发 | 插件 agent 不支持 `hooks` 字段（Claude 侧安全限制） |
| 与官方 `analyzing-dotnet-performance` 的关系梳理 | 该 skill 属源码反模式扫描，与本仓 `csharp-code-review` 相邻，非本次范围 |
