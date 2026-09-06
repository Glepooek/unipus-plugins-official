# dotnet-diagnose-triage 黄金测例

七例，每例四段：**输入** / **预期台账** / **预期结论强度** / **考什么**。

**跑法**：把「输入」段原样作为 prompt 提供给 `dotnet-diagnose` agent（或直接调用本 skill），比对实际输出的台账状态与结论强度是否与预期一致。**不符即为不通过**，回头修 SKILL.md 或 references，不改测例预期。

无头模式的具体命令形态（2026-09-06 首轮实测确立）：

```bash
# 输入段含 shell 元字符时必须走文件，不要直接内联进 -p '...'
cat > "$HOME/dd-golden/caseN-prompt.txt" <<'EOF'
直接把下面这段原样派发给 @optimus-devops-plugin:dotnet-diagnose，不要自己追问或代答：

<测例 N 的输入段原文>
EOF
claude --plugin-dir ./plugins/optimus-devops-plugin -p "$(cat "$HOME/dd-golden/caseN-prompt.txt")"
```

⚠️ **三条跑法约束，缺任一条测的就不是 agent**：

1. **prompt 必须前置「直接原样派发给 @…，不要自己追问或代答」**。无头会话是**两级**结构——外层 Claude 先读到 prompt，若它自行判断证据不足就会拦下来追问，agent 根本不被派发，实测的是外层会话的判断力。首轮测例 2 即因此空跑一轮
2. **输入段含 shell 元字符（`>` `<` `|` `&`）时，prompt 必须写入文件再以 `-p "$(cat file)"` 传入**。裸 `> 0` 这类会被权限层判为重定向歧义而拒绝执行（首轮测例 5 连续两次 denied）
3. **各例输入段的取证输出均为可直接消费的原始文本**，不是「显示某类型 Count 很高」这类转述摘要。摘要会让外层会话或 agent 合理地要求补证据，测例走不到判据裁剪那一步

**输出落盘位置**：`$HOME/dd-golden/`（**仓库外**）。dump 与 SOS 输出可能含敏感数据，按 `rules/01-dump-handling.md § 2. 版本库隔离` 不得落进 git 工作树。

⚠️ 输出片段的列名与语义逐字取自知识库正文（如 `MonitorHeld` 编码规则取自 `sos-locks-and-async.md § 1`），**不得自造列名**。

---

## 测例 1 · Monitor 死锁（判据加粗形态 + 编码规则）

**输入**：

```
界面卡死，点什么都没反应。!syncblk 输出如下：

Index SyncBlock MonitorHeld Recursion Owning Thread Info          SyncBlock Owner
    3 019f4a28            3         1 019e1b40  1a2c   5   02a41f38 MyApp.Services.CacheManager
    7 019f4c90            3         1 019e2d80  1a3f   8   02a44c10 MyApp.Services.OrderRepository
-----------------------------
Total           2
CCW             0
RCW             0
ComClassFactory 0
Free            0

另外 !clrstack -all 显示：线程 5 停在 Monitor.ReliableEnter 帧，等的是 02a44c10；线程 8 也停在 Monitor.ReliableEnter，等的是 02a41f38。
```

**预期台账**：「Monitor 死锁」→ `已证实`，依据挂 `sos-locks-and-async.md § 1` 并附命中的判据句。

**预期结论强度**：**已确认**。

**考什么**：能否读懂 `MonitorHeld` 的编码（等待线程数 =（值−1）/2）并识别循环等待。这是命令篇「箭头 + 加粗」判据形态的典型。

---

## 测例 2 · 单份 dumpheap 不足以判「持续增长」

**输入**：

```
内存一直涨。!dumpheap -stat 输出如下（只有这一份，进程已退出无法再抓）：

              MT    Count    TotalSize Class Name
00007ffa1c3d4210  1847293    206896816 MyApp.Models.OrderItem
00007ffa1b9a1188   412887      3303100 System.String
00007ffa1b9c2340    98211      1257008 System.Object[]
00007ffa1c3d5998     8291       663280 System.Collections.Generic.List`1[[MyApp.Models.OrderItem, MyApp]]
00007ffa1b9a0d10     2104        10192 Free
Total 2368986 objects
```

**预期台账**：该假设停在 `待验` 或 `无法判定`，**注明需第二次采样**。

**预期结论强度**：**推测**，**不得报已确认**。

**考什么**：自检第二项「结论不得超出证据」。`sos-heap-and-objects.md § 1` 的判据明确要求两次 `-stat` 对比，单时点数据只能说明「某类型实例多」，不能说明「在增长」。

---

## 测例 3 · WPF Binding 泄漏（修复方向原样转述）

**输入**：

```
WPF 应用，窗口关不掉，关了以后内存不降。对一个已经 Close 的窗口实例跑 !gcroot 得到：

HandleTable:
    000001f2a1b40388 (pinned handle)
    -> 000001f2b3c40120 System.Object[]
    -> 000001f2b3c51a48 MS.Internal.Data.ValueChangedEventManager
    -> 000001f2b3c51ad0 MS.Internal.Data.ValueChangedEventManager+ValueChangedRecord
    -> 000001f2b3c48e60 MyApp.ViewModels.OrderDetailViewModel
    -> 000001f2b3c48f18 MyApp.Views.OrderDetailWindow

Found 1 unique roots.
```

**预期台账**：「Binding 泄漏」→ `已证实`，依据挂 `wpf-leak-patterns.md § 2`。

**预期结论强度**：**已确认**，且修复方向**原样转述**该判据句自带的 `knowledge-base/wpf/rules/05-data-binding.md § 2. 变更通知：INotifyPropertyChanged / ObservableCollection`——**不改写为其他目标、不展开成修复方案**。

**考什么**：WPF 分支路由 + 修复方向第一档「判据句内引用原样转述」。这是本产物相对官方 `dump-collect` 的独有价值（官方全无 WPF 内容）。

---

## 测例 4 · 排除判据不得越界（三期最终审查那处 Important）

**输入**：

```
WPF 应用，内存一直涨。已按 !dumpheap -stat 逐个核对全部 WPF 类型的实例数，结果如下，与当前实际打开的界面数量吻合，无残留：

              MT    Count    TotalSize Class Name
00007ffa2c114550        3         1608 MyApp.Views.MainWindow
00007ffa2c1187a0       12         4896 MyApp.Views.OrderPanel
00007ffa2b8f3320      486        38880 System.Windows.Data.BindingExpression
00007ffa2b8e1180        3         1272 System.Windows.Threading.DispatcherTimer

当前确实打开着 3 个窗口、12 个面板，3 个 timer 也都在用。
```

**预期台账**：排除 `wpf-leak-patterns.md` § 2 / § 3 / § 5 三类；**§ 4 弱事件泄漏必须仍为 `待验`**，并注明需另按内部监听表体积判断。

**预期结论强度**：无收敛结论，如实报「候选集未穷尽，§ 4 待验」。

**考什么**：`wpf-leak-patterns.md § 1` 的排除判据已显式限定范围——「全部 WPF 类型实例数正常」不足以排除弱事件泄漏（该类泄漏体现在内部监听表体积而非类型实例数）。**越界排除会漏掉真实根因**，这是三期最终审查提出的那处 Important 的落地检验。

---

## 测例 5 · 合并候选集初始化 + 第二跳断链

**输入**：

```
程序挂起、界面无响应。只有 dotnet-counters 采集的时间序列数据，无 dump，也无法连活体进程。采样如下（每 5 秒一行）：

Time              ThreadPool Queue Length   ThreadPool Thread Count   CPU Usage (%)
10:22:05                               58                        32             7
10:22:10                               91                        61             6
10:22:15                              117                       104             8
10:22:20                               74                       152             7
10:22:25                              103                       180             9
10:22:30                               46                       180             6
10:22:35                               88                       180             8
10:22:40                              112                       180             7

队列长度全程在 40 到 120 之间波动，从未回落到 0；线程数爬到 180 后顶住不动；CPU 全程个位数。
```

**预期台账**：
1. 台账须含**完整 7 条**候选（含只在 dump 表出现的 Monitor 死锁）——不因当前只有 counters 数据就少登记
2. 「线程池饥饿」命中 `live-monitoring-decision.md § 5` 第一跳，但该判据句要求转 `sos-locks-and-async.md § 3` 再转 `sos-threads-and-stacks.md § 2`——**无 dump、无活体连接，第二跳断链**，故停在 `待验`
3. **不得记 `无法判定`**

**预期结论强度**：**推测**，注明「时间序列已指向线程池饥饿，确认需 `sos-locks-and-async.md § 3` 所需的 dump 或活体连接」。

**考什么**：征象映射三条规则中的 1/2（合并候选集初始化 + 证据类型不决定台账内容）+ 第二跳断链的正确降级。⚠️ **这是最容易做错的一例**——两个常见错误是「只登记活体表的 2 条候选」和「把断链记成 `无法判定`」。

---

## 测例 6 · dump 类型不支撑目标（B 组前置校验）

**输入**：

```
程序崩了。我这边有一个 dump 文件，是用 procdump 抓的，命令就是 procdump -e 4152 C:\dumps\，没加别的开关，实际写出来的文件只有 4 MB。我想查的是内存泄漏，看看是哪个类型的对象占满了内存。
```

⚠️ 输入里「procdump 不带参数」是关键——`dump-capture.md § 1` 的开关表原文即写明默认写 `-mm` Mini dump、无堆对象数据。4 MB 的体积也在 Mini 的量级区间内（Heap 为数十至数百 MB）。

**预期台账**：**不进入台账循环**——不初始化任何假设。

**预期结论强度**：不出诊断结论。先报 dump 类型不支撑该目标（`dump-types-and-capability.md § 1. 四种类型的能力对照`），给出重抓 Heap / Full 的补救路径。

**考什么**：B 组证据可用性前置校验。不校验就整轮白做——Mini dump 无完整堆信息，基于它的任何泄漏结论都是假结论。

---

## 测例 7 · 崩溃日志的可用边界

**输入**：

```
程序自动退出了，没有任何提示。我从日志文件里翻到这几行：

2026-09-05 14:22:01 INFO  订单处理超时，订单号 SO-20260905-8871
2026-09-05 14:22:03 INFO  订单处理超时，订单号 SO-20260905-8872
2026-09-05 14:22:07 WARN  用户会话即将过期
2026-09-05 14:22:09 FATAL Unhandled exception: System.InvalidOperationException: Collection was modified; enumeration operation may not execute.
   at System.Collections.Generic.List`1.Enumerator.MoveNext()
   at MyApp.Services.OrderSyncService.FlushPending()
   at MyApp.Workers.SyncWorker.OnTimerTick(Object sender, ElapsedEventArgs e)
```

⚠️ **异常行必须是日志的最后一行**——进程随即终止，其后不应再有任何业务行。首轮实测时异常行之后还留了一条 INFO，agent 据此正确推断「该行非 CLR 崩溃路径产生」并否掉了因果链；那是构造缺陷，会掩盖本例真正要考的边界。

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
