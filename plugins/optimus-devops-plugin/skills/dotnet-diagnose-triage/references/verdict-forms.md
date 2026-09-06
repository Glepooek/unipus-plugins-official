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
