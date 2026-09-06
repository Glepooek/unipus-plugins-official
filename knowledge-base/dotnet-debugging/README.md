# .NET 高级调试知识库

> 版本：1.2.0

> 面向 **.NET 应用事后诊断与定位**的知识库。覆盖 .NET Framework 4.x、.NET 6/8+ 与 Linux 容器三种运行时，收录从运行中进程或 dump 中取证的命令、输出解读与判据。

本领域以三运行时共性层为主干，**WPF 专属归因作为独立分支收录**（`reference/wpf-*.md` 两篇，仅 Windows）——WPF 是本仓库核心技术栈，其 Dispatcher 死锁与四类泄漏的根链形态无法由通用 SOS 读法直接得出。

本领域负责「程序已经出问题之后，如何取证并定位根因」。预防性的编码规范不在本领域——那属于 `knowledge-base/csharp/` 与 `knowledge-base/wpf/`。

## 文档目的

让排查者能按「征象 → 候选根因 → 取证命令 → 输出解读 → 判据」这条链路自助定位问题，而不必每次依赖个人经验重新摸索。目标读者读完 `reference/debugging-decision-tree.md` 即可确定该用哪条命令，再按命令条目读懂输出含义。

## 适用范围与读者

- **适用范围**：生产或测试环境出现内存持续增长、进程挂起、CPU 打满、崩溃退出、句柄耗尽等问题时的诊断取证
- **读者**：需要定位 .NET 应用运行期问题的开发与运维人员；本领域的 skill 消费者是 `plugins/optimus-devops-plugin/skills/dotnet-diagnose-triage`（由 `dotnet-diagnose` agent 编排调用）

## 收录判据

**单命令粒度进知识库，多命令编排进 skill。**

检验标准：这条内容能独立成为一个「查一下就照着用」的条目吗？能 → 本领域。它是否必须知道「上一步做了什么」才有意义？是 → 属 skill，不收。

据此，抓取 dump 的完整命令行（`procdump`、`dotnet-dump collect`、`createdump` 等）**收录**——单条可查；而「先判断征象 → 决定抓哪种 dump → 引导装工具 → 抓 → 分析 → 回报」这条编排**不收**。

## 与既有领域的边界

| 已有资产 | 它负责 | 本领域负责 | 切线 |
|---|---|---|---|
| `knowledge-base/csharp/rules/06-memory-resource.md` § 4 / § 6 / § 9 | 怎么写才不泄漏 | 已经泄漏了，如何在托管堆里认出它 | 写代码时 vs 读现场时 |
| `knowledge-base/csharp/rules/11-observability.md` § 7 | 应用内部该埋什么指标 | 从外部读取运行中进程的计数器与事件流 | 埋点 vs 采集 |
| `knowledge-base/wpf/rules/12-exceptions-crash.md` § 1–3 | 怎么捕获并优雅退出 | 崩溃 dump 里如何找到抛出点与第一现场 | 兜住 vs 验尸 |
| `knowledge-base/dotnet/` | 目标框架能跑在哪 | 目标框架决定用哪套工具链 | 能不能跑 vs 用什么诊断 |

引用单向：本领域正文可指向上述领域，被指向方不反向声明。

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义，与 `knowledge-base/csharp/README.md` 同一套定义。

| 级别 | 措辞 | 含义 |
|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 |
| **建议 MAY** | "可以"、"建议" | 可选做法，不强制 |

本领域仅 `rules/01-dump-handling.md` 一篇规范文件，其余为 `reference/` 描述性内容。调试知识绝大多数是判据而非规范——"内存涨了应该先看 `!dumpheap -stat`" 是判据不是规则，写成 rule 即是假规范。

## 阅读路径

| 场景 | 参考文档 |
|---|---|
| 不知道从哪下手，先定位问题类别 | `reference/debugging-decision-tree.md` |
| 读懂命令输出前的术语基础 | `reference/clr-runtime-anatomy.md` |
| 决定抓哪种 dump | `reference/dump-types-and-capability.md` |
| 实际抓取 dump | `reference/dump-capture.md` |
| 命令报错、符号加载不出来 | `reference/symbols-and-tool-matching.md` |
| 进程挂起 / 查线程在等什么 | `reference/sos-threads-and-stacks.md` |
| 内存持续增长 / 找泄漏持有者 | `reference/sos-heap-and-objects.md` |
| 死锁 / 异步卡住 / 线程池饥饿 | `reference/sos-locks-and-async.md` |
| 间歇性问题 / 需要时间线数据 | `reference/live-monitoring-decision.md` |
| 采集机制与基线概念 | `reference/eventpipe-and-diagnostic-port.md` |
| WPF 界面无响应 / UI 线程卡死 | `reference/wpf-dispatcher-deadlock.md` |
| WPF 内存泄漏 / 窗口关不掉还在堆上 | `reference/wpf-leak-patterns.md` |
| 处理生产 dump 文件（合规） | `rules/01-dump-handling.md` |

## 文件地图

| 文件 | 主题 |
|---|---|
| `reference/clr-runtime-anatomy.md` | 托管堆分代、LOH/POH、同步块表、终结队列、线程池结构、GC 模式、句柄表 |
| `reference/dump-types-and-capability.md` | 四种 dump 类型的取证能力边界、位数匹配、快照时点性 |
| `reference/dump-capture.md` | procdump / dotnet-dump collect / createdump / WER LocalDumps / DOTNET_DbgEnableMiniDump 的完整命令与开关 |
| `reference/symbols-and-tool-matching.md` | PDB 类型、符号服务器配置、SOS 与运行时版本匹配、缺符号降级读法 |
| `reference/sos-threads-and-stacks.md` | !threads / !clrstack / !dumpstack / !pe / !dso 的开关、输出逐列语义与判据 |
| `reference/sos-heap-and-objects.md` | !dumpheap / !dumpobj / !objsize / !gcroot / !eeheap / !gchandles 的开关、输出语义与泄漏判据 |
| `reference/sos-locks-and-async.md` | !syncblk / !dumpasync / !threadpool 的开关、输出语义与死锁/饥饿判据 |
| `reference/debugging-decision-tree.md` | 六类征象（挂起 / 内存增长 / CPU 打满 / 崩溃 / 间歇抖动 / 句柄耗尽）→ 候选根因 → 取证命令查表 |
| `reference/eventpipe-and-diagnostic-port.md` | EventPipe 与 ETW 的能力边界、诊断端口、Provider 三级过滤、两套计数器体系、缓冲区、基线采集 |
| `reference/dotnet-counters.md` | dotnet-counters monitor / collect 的开关与输出，内置计数器双版本命名与形态判据对照 |
| `reference/dotnet-trace.md` | dotnet-trace collect / profile 选择 / report topN / 格式转换，含 cpu-sampling 移除的迁移写法 |
| `reference/live-monitoring-decision.md` | 六类征象（延迟尖峰 / 内存增长 / CPU 打满 / 异常风暴 / 线程池饥饿 / 启动阶段）→ 采集方案查表 |
| `reference/wpf-dispatcher-deadlock.md` | 认出 UI 线程、三类等待形态、队列积压与真死锁的区分、持锁方定位闭环（仅 WPF/Windows） |
| `reference/wpf-leak-patterns.md` | 四类 WPF 泄漏（Binding / 可视化树 / 弱事件 / DispatcherTimer）的堆上特征、根链形态与反查速查表（仅 WPF/Windows） |
| `rules/01-dump-handling.md` | dump 作为数据资产的处置：密级、版本库隔离、对外交付类型、留存销毁、自动抓取落盘 |

## 内容来源

- **主干**：微软官方诊断文档（learn.microsoft.com 的 .NET diagnostics 专区）与 `dotnet/diagnostics` 仓库
- **深度补充**：《Advanced .NET Debugging》等书籍知识体系（CLR 内部、GC 堆结构、同步块表）。凡出自该来源且无官方文档佐证的内容，正文中标注为经验性知识

## 索引与机器消费

本领域 `index.jsonl` **按命令/征象分片登记**，而非按整篇文档登记——调试知识天然按这两个维度被检索。字段说明与维护约定见 `knowledge-base/README.md`。

`applies_to` 在本领域对 `reference` 条目**同样必填**：同一条命令在不同运行时的可用性不同（`!dumpasync` 需较新 SOS、`procdump` 仅 Windows、`createdump` 仅 .NET Core+），不标运行时等于没给出可用信息。

## 更新与维护

- 新增/修改内容时，同一次提交里同步更新 `index.jsonl`
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" dotnet-debugging`
- 每条命令条目遵循四段固定结构：用途与前置条件 / 语法与关键开关 / 输出逐列语义 / 判据（能证实或排除什么假设）
