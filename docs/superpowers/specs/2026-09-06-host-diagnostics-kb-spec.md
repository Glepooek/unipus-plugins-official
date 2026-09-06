# 实现 Spec：宿主进程外部故障诊断知识库

> 状态：待评审
> 日期：2026-09-06
> 目标领域名：`host-diagnostics`（已确认）
> 消费者：待建的 .NET/WPF 诊断工具
> 目标框架：.NET 8+，兼容 .NET Framework 4.6.2+

---

## 1. 背景与目标

### 1.1 要解决什么

计划开发一个 **Windows 平台、.NET/WPF 实现的可执行程序诊断工具**，用于诊断**宿主进程跑不动**——故障源在被诊断进程的**外部**：第三方 DLL 注入、安全软件拦截、网络不通、硬件资源不足、系统环境劫持。

本 spec 只定义**知识库**，不涉及工具本身的开发。知识库先行，工具据其判据实现。

### 1.2 与 aha_doctor 的关系

知识来源是对飞书内置「AHA 电脑医生」（`D:\Feishu\app\aha_doctor`）的只读静态分析，分析文档已迁入 `knowledge-base/host-diagnostics/reference/aha-doctor-teardown.md`（原 `docs/aha-doctor-analysis.md`，已于收口阶段删除）。

**可继承的**：故障源分类、检测项清单、网络分层排查序列、环境劫持检测点、双进程提权架构。

**不可继承的**：四个加密规则包（`ModuleDetect.dat` / `SoftwareDetect.dat` / `3partyAppDetect.dat` / `BrowserPlugin.dat`）内的**具体特征库**。这是静态分析的天花板，也直接决定了本知识库的一条核心设计约束（见 § 1.3）。

### 1.3 核心设计约束：判据可自持

aha_doctor 的特征库是海量线上故障案例沉淀的产物，无法复制。因此本知识库**不追求"内置一份可疑模块黑名单"**，而是：

- **收录判断框架**——如何认定一个模块可疑（签名、路径、厂商、加载方式）
- **收录已知冲突形态**——按类别而非具体产品（如"安全软件的 HIPS 模块注入导致 D3D 初始化失败"）
- **把具体名单外置为可维护数据**——由使用方按自己的故障回流逐步积累

这条约束贯穿全部领域设计：**知识库给方法，不给名单**。

---

## 2. 领域归属决策

### 2.1 新建独立领域，不并入 `dotnet-debugging`

**决策**：新建 `knowledge-base/host-diagnostics/`。

**理由**：`dotnet-debugging` 的领域职责在 `catalog.json` 中明确为「事后诊断与定位：征象判据、CLR 可观测结构、dump 抓取与分析命令、SOS 输出解读」，其 README 进一步限定为「**程序已经出问题之后，如何取证并定位根因**」，取证对象是**托管运行时内部结构**（托管堆、线程、锁、Dispatcher）。

本领域的取证对象是**进程外部的系统环境**（注入模块、安全软件、网络栈、注册表、硬件）。两者：

| 维度 | `dotnet-debugging` | `host-diagnostics` |
|---|---|---|
| 故障源位置 | 进程内部（代码/运行时） | 进程外部（系统环境） |
| 取证手段 | SOS / CLRMD / dump / EventPipe | Win32 API / 注册表 / WMI / ETW |
| 被诊断对象 | 托管进程自身 | 任意宿主进程 + 系统 |
| 结论形态 | 定位到代码或对象图 | 定位到环境因素或第三方软件 |
| 是否需要 dump | 通常需要 | 通常不需要 |

混入会让动态检索互相干扰——查"卡顿"时同时命中"线程池饥饿"与"安全软件行为拦截"，而两者的取证路径毫无交集。

**符合 README 既有原则**：「领域可以相互引用，但不得复制同一事实或规则」。

### 2.2 领域名候选

| 候选 | 优点 | 缺点 |
|---|---|---|
| `host-diagnostics` ✅ | 准确表达"诊断宿主进程"；与 aha_doctor 定位一致 | 略抽象 |
| `windows-environment` | 直白 | 弱化了"诊断"这一目的 |
| `process-environment` | 强调外部环境 | 与 `architecture` 领域用词易混 |

**建议 `host-diagnostics`**，`catalog.json` 中 title 写「宿主进程环境诊断」。

### 2.3 与既有领域的边界（须写入领域 README）

| 已有领域 | 它负责 | 本领域负责 | 切线 |
|---|---|---|---|
| `dotnet-debugging` | 进程内部：托管堆、线程、锁的取证 | 进程外部：注入、拦截、网络、硬件 | 内 vs 外 |
| `dotnet` | 目标框架能跑在哪 | 运行环境是否被干扰 | 能不能跑 vs 跑不跑得动 |
| `csharp` / `wpf` | 怎么写才不出问题 | 代码没问题但环境有问题 | 预防 vs 环境排查 |

引用单向：本领域正文可指向上述领域，被指向方不反向声明。

---

## 3. 目录结构

遵循 `knowledge-base/README.md` 的统一模式——元数据在领域根，内容按类型分目录：

```
host-diagnostics/
├── README.md            # 领域说明、版本行、边界、收录判据
├── CHANGELOG.md         # 领域独立版本历史
├── index.jsonl          # rule + reference 统一编目
├── rules/               # 规范条款（MUST/SHOULD/MAY）
│   ├── 01-diagnostic-safety.md
│   ├── 02-evidence-standards.md
│   └── 03-conclusion-strength.md
└── reference/           # 描述性判据与机制
    ├── symptom-routing.md
    ├── module-injection.md
    ├── security-software.md
    ├── network-layered-probe.md
    ├── system-environment-hijack.md
    ├── hardware-thresholds.md
    ├── vdi-environment.md
    ├── dotnet-probing-techniques.md
    └── aha-doctor-teardown.md      # 外部工具分析，见 § 5.9
```

**为什么 rules 只有 3 篇**：本领域绝大多数内容是**判据**（"看到 X 说明 Y"），属描述性知识，归 `reference/`。真正带规范语气的只有三类：诊断行为本身的安全约束、取证质量要求、结论强度纪律。

**不预建空目录**——`reference/` 首篇内容产生时才建，符合 README § 目录约束。

---

## 4. rules/ 内容设计

### 4.1 `01-diagnostic-safety.md` — 诊断行为的安全约束

诊断工具会读取其他进程与系统状态，且模块屏蔽是写操作。这些必须有硬性约束。

| § | 标题 | level | enforcement | 要点 |
|---|---|---|---|---|
| 1 | 只读优先 | MUST | review | 诊断阶段禁止任何系统写操作；修复动作必须与诊断分离，由用户显式触发 |
| 2 | 写操作的确认与回滚 | MUST | review | 模块屏蔽等写操作须：明示影响、可撤销、记录原状态 |
| 3 | 提权最小化 | MUST | review | 主进程不以管理员权限常驻；提权操作外包给独立子进程 |
| 4 | 采集数据的密级 | MUST | review | 进程模块列表、网络配置含环境指纹；禁止未脱敏上报或提交版本库 |
| 5 | 禁止进程内注入 | SHOULD | review | 不使用 API Hook 等注入手段采集数据；优先 ETW 等旁路机制 |

> § 5 的依据来自 aha_doctor 分析——它确实具备 Detours hook 能力用于 DNS/剪贴板/键鼠监控。本知识库**不继承这一手法**：托管环境做 hook 不稳、杀软误报率高，且 ETW 可替代。

### 4.2 `02-evidence-standards.md` — 取证质量要求

| § | 标题 | level | enforcement | 要点 |
|---|---|---|---|---|
| 1 | 原始输出优先 | MUST | review | 判据必须基于可复核的原始数据，不接受转述摘要 |
| 2 | 采样而非瞬时值 | MUST | review | CPU/内存/磁盘等波动指标须多次采样，禁止单点判定 |
| 3 | 故障机器上的降级 | MUST | review | 取证手段本身可能失败（WMI 服务异常、权限不足），须有超时与兜底路径 |
| 4 | 时间窗口对齐 | SHOULD | review | 多源证据须记录采集时刻，跨源比对前确认窗口重叠 |
| 5 | 环境基线 | SHOULD | advisory | 有条件时采集正常机器基线用于对比 |

> § 3 直接来自 aha_doctor 的设计观察：它刻意绕开 WMI（除 SecurityCenter2 外），因为诊断工具面对的恰恰是故障机器。这条在 C# 实现中尤其重要——WMI 是 .NET 最顺手的路径，但也最容易在故障机器上挂住。

### 4.3 `03-conclusion-strength.md` — 结论强度纪律

复用仓库已建立的假设台账机制（见 `dotnet-diagnose-triage`），保持一致：

| § | 标题 | level | enforcement | 要点 |
|---|---|---|---|---|
| 1 | 三档结论强度 | MUST | review | 已确认 / 推测 / 超出覆盖，不得混用 |
| 2 | 相关性不等于因果 | MUST | review | "检测到 X 且现象为 Y"不足以判定 X 导致 Y |
| 3 | 超出覆盖必须显式声明 | MUST | review | 无判据支撑时输出"超出覆盖"，禁止强行给结论 |
| 4 | 风险计数不是故障计数 | SHOULD | review | 检出项 ≠ 根因；呈现时须区分"发现异常"与"确认致因" |

> § 4 针对 aha_doctor 的「共发现 N 项风险信息」模型——这个模型对用户友好，但容易让人把"检出 47 个第三方模块"读成"有 47 个问题"。

---

## 5. reference/ 内容设计

> **全篇固定收尾**：每篇 reference 的**最后一节**统一为「本篇覆盖边界」，写明该篇判不了什么。这是 `rules/03 § 3 超出覆盖必须显式声明` 的落地形态——没有这一节，消费者无从知道判据的尽头在哪。下列各表中未逐一列出该节，实施时一律追加。

### 5.1 `symptom-routing.md` — 现象反查表（引导器）

**为什么它排第一**：用户报的是现象，不是"请扫描"。这篇是整个知识库的入口。

| § | 内容 |
|---|---|
| 1 | 反查表：现象 → 优先检测项（按命中率排序） |
| 2 | 白屏：模块注入（D3D/DWM 干扰）→ 硬件加速开关 → GPU 驱动 → 渲染层降级 |
| 3 | 启动失败：IFEO 劫持 → 安全软件隔离 → 文件完整性 → 依赖缺失 |
| 4 | 卡顿/卡死：模块注入 → CPU/内存/磁盘饱和 → 安全软件行为拦截 |
| 5 | 网络类现象：按 `network-layered-probe.md` 的分层序列 |
| 6 | 崩溃：模块注入 → 系统崩溃记录 → dump 抓取（转 `dotnet-debugging`） |
| 7 | 多现象并发时的优先级判断 |

> § 2 的排序依据是 aha_doctor 官方文档的根因判断：白屏/卡顿「通常是部分第三方软件引起」。这是官方认定的头号故障源，反查表应据此排序。

> § 6 是**跨领域交接点**：一旦确认故障源在进程内部，转交 `dotnet-debugging`。本领域到此为止。

### 5.2 `module-injection.md` — 模块注入检测（价值最高）

| § | 内容 |
|---|---|
| 1 | 检测框架：枚举 → 验签 → 分类 → 判定 |
| 2 | 可疑判定维度：签名状态、签名主体、文件路径、加载时机、是否在系统目录 |
| 3 | 注入手法识别：AppInit_DLLs、SetWindowsHookEx 全局钩子、CreateRemoteThread、IFEO、DLL 劫持 |
| 4 | 常见注入源分类（按类别，非具体产品）：安全软件 HIPS/沙箱、输入法、屏幕取词/翻译、录屏、远程控制、UI 增强外挂 |
| 5 | 对 WPF 宿主的特有影响：D3D/DWM 干扰 → 白屏；消息钩子 → 输入异常；GDI 拦截 → 渲染错乱 |
| 6 | 排除法：如何确认某模块与现象无关 |
| 7 | 冲突名单的外置与维护——由使用方按故障回流积累 |

> § 7 是 § 1.3 核心约束的落点：知识库给判断维度，具体名单由使用方维护为外部数据文件。

### 5.3 `security-software.md` — 安全软件干扰

| § | 内容 |
|---|---|
| 1 | 检测面：AV 产品清单、防火墙三 profile（域/专用/公用）、WFP 过滤器 |
| 2 | 拦截现象映射：文件隔离 → 启动失败；网络拦截 → 连接超时；行为拦截 → 卡死/操作失败 |
| 3 | `SecurityCenter2` 的能力与局限（能列产品，不能判它拦了什么） |
| 4 | 处置建议排序：加白名单 > 临时禁用 > 卸载 |
| 5 | 企业管控环境的特殊性：策略下发的安全软件用户无权改 |

> § 4 的排序来自 aha_doctor 官方文档：「将飞书添加至安全类软件的白名单，或者退出/卸载相关软件」。

### 5.4 `network-layered-probe.md` — 网络分层排查

| § | 内容 |
|---|---|
| 1 | 分层排查序列（本篇主干）：本机 IP → DNS 配置 → hosts → 代理 → LSP/命名空间提供者 → 域名可达性 → 延迟/丢包 → 下载测速 |
| 2 | 每层的判据与典型异常形态 |
| 3 | hosts 篡改识别 |
| 4 | 代理检测：系统代理、PAC、per-app 代理的差异 |
| 5 | LSP/命名空间提供者异常 |
| 6 | 错误码 → 处置建议映射表（.NET 侧：`SocketError` / `WebExceptionStatus` / WinHTTP 错误码） |
| 7 | 域名可达性与"能上网"的区别 |

> § 1 的序列直接继承自 aha_doctor 的网络检测分区顺序——从本机配置向外逐层排除，是正确的排查方向。

> § 6 对应 aha_doctor 的 80+ 条 Chromium net error code 映射表。C# 实现须换成 .NET 的错误码体系，映射关系需自建。

### 5.5 `system-environment-hijack.md` — 环境劫持

**这四项排查成本极低但极易被误判成程序 bug**，优先级应高于其表面复杂度。

| § | 内容 |
|---|---|
| 1 | IFEO Debugger 劫持：注册表位置、判定、正常与异常形态 |
| 2 | GlobalFlag：堆调试标志被开启导致的性能塌陷 |
| 3 | AppCompatFlags\Layers：兼容模式标志的副作用 |
| 4 | URL 协议注册：协议处理器缺失或被抢占 |
| 5 | 其他启动期劫持点：AppInit_DLLs、ShellExecute Hooks |

### 5.6 `hardware-thresholds.md` — 硬件资源判据

| § | 内容 |
|---|---|
| 1 | 阈值的性质：可调参数而非硬判据，须记录定值依据 |
| 2 | CPU：使用率 + 持续时长的联合判据 |
| 3 | 内存：物理内存可用量、提交量、虚拟内存配置 |
| 4 | 磁盘：使用率、剩余容量、队列长度、SSD/HDD 判定 |
| 5 | GPU：使用率、硬件加速开关、渲染层级 |
| 6 | CPU 型号兼容性（指令集要求） |

> § 1 是必须先立的：aha_doctor 的阈值内置于二进制、无法读取，本知识库的阈值须自定。把它们标为可调参数并记录依据，避免变成不可解释的魔数。

### 5.7 `vdi-environment.md` — 虚拟桌面环境

| § | 内容 |
|---|---|
| 1 | VDI 环境识别 |
| 2 | 磁盘读取速度判据（VDI 常见瓶颈） |
| 3 | 传输协议与图形性能 |
| 4 | VDI 下哪些常规判据失效 |

> 若目标用户无虚拟桌面场景，本篇可延后。

### 5.8 `dotnet-probing-techniques.md` — C# 取证手段（实现约束）

**单列一篇的理由**：前七篇是诊断理论（稳定），本篇是实现约束（随 .NET 版本变）。混在一起会让理论条目跟着实现细节反复改版。

| § | 内容 |
|---|---|
| 1 | 取证手段总表：检测项 → C# 可行路径 → 是否需 P/Invoke |
| 2 | WMI 的权衡：最顺手但故障机器上可能挂住；主用 + 超时保护 + P/Invoke 兜底 |
| 3 | 必须 P/Invoke 的项：`wintrust`/`crypt32` 验签、`fwpuclnt` WFP、`WSCEnumProtocols` LSP、`WinHttpGetIEProxyConfigForCurrentUser` 代理 |
| 4 | 托管封装够用的项：`Ping`、`NetworkInterface`、`Registry`、`Process.Modules` |
| 5 | 性能计数：`PerformanceCounter` 在 .NET Core+ 的行为差异 |
| 6 | ETW：`TraceEvent` 库的适用性与 GC 压力权衡；何时改调 `wpr.exe` |
| 7 | 外部工具编排：`wpr.exe`（Win10+ 内置，免分发）vs `xperf.exe`（需分发） |
| 8 | 发布形态约束：自包含 + 单文件（故障机器不能假设有运行时）、AOT 与 P/Invoke/反射的兼容性 |

> § 7 继承 aha_doctor 的取巧：它自己也没自研 ETW 录制，直接调微软的 `xperf.exe`。C# 侧更应如此。优先 `wpr.exe` 因其 Win10+ 内置，省去分发与签名问题。

### 5.9 `aha-doctor-teardown.md` — 外部工具分析（迁入）

**来源**：`docs/aha-doctor-analysis.md` 迁入本领域。原文件的删除**推迟到收口阶段**——该文件未提交过 git（`??` 未跟踪），删除不可逆，须等全领域验证通过后再删。详见实施计划附录 A。

**为什么收录**：它是本领域全部判据的**依据出处**。§ 5.1-5.7 的检测项清单、网络分层序列、环境劫持四点均继承自它。没有这篇，其余条目的"为什么这么定"就断线了——这正是 knowledge-base README § source 所说的「规则到理由的连接」。

**为什么放 `reference/` 而非留在 `docs/`**：按 AGENTS.md 的划分标准——「这份内容是否需要被某个 skill 按条检索引用作为判断依据？」本文档会被 `rules/` 与其他 `reference/` 以 `source` 字段引用，属被检索的依据，因此归 `knowledge-base/`。

#### 收录时须做的四处调整

| # | 调整 | 原因 |
|---|---|---|
| 1 | 保留三级来源标记（【官方】/【实测】/【推断】） | 本领域独有的溯源结构，是它作为依据出处的价值所在，不得压平 |
| 2 | 补「快照日期与失效条件」小节 | 分析对象是会更新的商业软件；须声明本文基于 2026-09-06 快照，厂商更新后结论可能失效 |
| 3 | 「能否改配置诊断其他软件」一节**移除** | 该节讨论修改第三方商业软件配置，与本领域「诊断自有宿主」的定位无关；保留会给出误导性操作指引 |
| 4 | 补「本文档不可作为判据直接引用的部分」 | 【推断】标记的内容不得被 `source` 引用为依据（对应 § 10 的实施警惕项） |

#### 索引形态

按 `mcp` 领域的既有做法——外部来源材料以**整篇为单位**登记（`anchor: ""`），不拆条：

```json
{"id": "host-diagnostics.ref.aha-doctor-teardown", "kind": "reference",
 "file": "reference/aha-doctor-teardown.md", "anchor": "",
 "title": "AHA 电脑医生静态分析：作用范围、检测项与实现机制",
 "tags": ["aha-doctor", "teardown", "prior-art", "detection-scope", "etw", "brand-config", "reverse-reference"],
 "summary": "飞书内置诊断工具的只读静态分析：六类检测子模块、取数机制（绕开 WMI 的原因）、双进程提权架构与品牌配置驱动模型；本领域判据的依据出处。",
 "applies_to": ["Windows"]}
```

**不拆条的理由**：它是一份完整的分析报告，内部小节（作用范围/实现方法/能力观察）互为上下文，单独检索出"3.2 取数机制"而不看分析边界声明会误读。这符合 README § 索引粒度规范的「描述性文档以整篇为单位登记是被认可的做法」。

#### `catalog.json` 中须声明来源性质

参照 `data-structures-algorithms` 声明许可证隔离、`mcp` 声明内容取自官方文档版本的做法，在 `notes` 中写明：

> ⚠️ `reference/aha-doctor-teardown.md` 为第三方商业软件（字节跳动 AHA 电脑医生）的只读静态分析，基于 2026-09-06 本机快照；仅含公开可读配置与文件元数据层面的观察，未反编译二进制、未解密受保护规则包。其中【推断】标记内容不得作为判据依据引用。

---

## 6. 索引规范

### 6.1 ID 命名

遵循 `<domain>.<两位文件编号或 ref>.<slug>`：

- rule：`host-diagnostics.01.readonly-first`、`host-diagnostics.02.raw-output-required`
- reference：`host-diagnostics.ref.ifeo-hijack`、`host-diagnostics.ref.network-probe-sequence`

### 6.2 rule 条目必填字段

按 README § 「新增 `rule` 条目时须一并填写」的约定，五个字段必填：

```json
{"id": "host-diagnostics.01.readonly-first", "kind": "rule", "level": "MUST",
 "file": "rules/01-diagnostic-safety.md", "anchor": "1. 只读优先",
 "title": "诊断阶段禁止系统写操作",
 "tags": ["safety", "readonly", "diagnosis", "write-operation"],
 "summary": "诊断与修复须分离，诊断阶段只采集不修改；修复动作由用户显式触发。",
 "enforcement": "review", "status": "active",
 "applies_to": ["Windows", ".NET 8+", ".NET Framework 4.6.2+"],
 "reviewed_at": "<实际审阅日>", "owner": "desktop client team"}
```

**`applies_to` 统一取值**：`["Windows", ".NET 8+", ".NET Framework 4.6.2+"]`。

- `"Windows"` 恒含——本领域全部内容 Windows 专有
- 两个框架版本反映工具的多目标要求；**仅 `dotnet-probing-techniques.md` 的条目需要按框架分化**（部分 API 在 Framework 与 Core 上行为不同，见 § 5.8），其余领域内容与框架无关，但仍保留完整取值以便消费者按框架过滤

### 6.3 enforcement 取值判断

按 README 的操作性检验「工具判的是该小节的实质，还是只是它的外壳」：

本领域**几乎全部条目应为 `review`**。理由：诊断安全、取证质量、结论强度都是需人工判断意图与内容的规则，无法由静态分析无歧义判定。

**不要为了让 `enforcement` 分布好看而强标 `ci`**——本领域没有对应的 CI 检查机制。仅 `01 § 4 采集数据的密级` 中"诊断产物须进 .gitignore"这一具体要求可标 `ci`，若单独成节。

### 6.4 粒度

- rules：**按小节登记**，每条可独立用于判断
- reference：**按独立主题登记**，不按整篇——本领域每篇 reference 内部都有多个会被独立检索的主题（如 `system-environment-hijack.md` 的四个劫持点各自可查）

预估条目数：rule 约 14 条，reference 约 46-56 条（含 teardown 整篇 1 条），合计 **61-71 条**（与 `dotnet-debugging` 的 74 条同量级）。

### 6.5 source 字段

`rules/` 条目的 `source` 指向对应 `reference/`：

- `01 § 5 禁止进程内注入` → `["reference/dotnet-probing-techniques.md#6. ETW 与 hook 的取舍"]`
- `02 § 3 故障机器上的降级` → `["reference/dotnet-probing-techniques.md#2. WMI 的权衡"]`

⚠️ **写入时机受校验器约束**：`check_index.py` 会校验 `source` 的目标文件与锚点**真实存在**（`check_source_refs`），指向不存在的文件或标题会直接报错。

上述两条的目标文件 `dotnet-probing-techniques.md` 在 P6 才产出，因此：

- **P4 建 rules 时**，这两条先指向已存在的 `["reference/aha-doctor-teardown.md"]`（整篇，无锚点）
- **P6 完成后**回填为上述精确锚点

同理，任何 `source` 都不得指向尚未写出的章节——**先有目标，再有引用**。

外部依据（微软文档 URL）在 reference 正文内以链接形式给出，不强行塞进 `source`。URL 不做离线校验。

---

## 7. 分阶段实施

按价值密度排序，每阶段可独立交付、独立校验。

| 阶段 | 内容 | 交付物 | 为什么这个顺序 |
|---|---|---|---|
| **P0** | 领域骨架 + teardown 迁入 | README、CHANGELOG（0.1.0）、index.jsonl（1 条）、`catalog.json` 登记、`reference/aha-doctor-teardown.md`（含四处调整） | 先让 `check_index.py` 跑通；teardown 是后续判据的依据出处，须先到位才能被 `source` 引用 |
| **P1** | 环境劫持 + 现象反查 | `system-environment-hijack.md`、`symptom-routing.md` | 排查成本最低、误判率最高、立即可用 |
| **P2** | 模块注入 | `module-injection.md` | 官方认定的头号故障源，价值最高 |
| **P3** | 网络分层 | `network-layered-probe.md` | 故障占比大，序列可直接继承 |
| **P4** | rules 三篇 | `01`/`02`/`03` | 前面有了实体内容，安全与质量约束才有落点 |
| **P5** | 安全软件 + 硬件 | `security-software.md`、`hardware-thresholds.md` | 阈值需自定，依赖实际场景 |
| **P6** | C# 实现约束 | `dotnet-probing-techniques.md` | 工具开发启动前完成即可；须按 .NET 8+ / Framework 4.6.2+ 双目标分化 |
| **P7** | VDI（可选） | `vdi-environment.md` | 仅当目标用户有该场景 |

**P4 放在 P1-P3 之后是刻意的**：rules 是对内容的约束，先有内容才知道该约束什么。反过来先写 rules 容易写成空泛的原则。

**P0 含 teardown 迁入是刻意的**：它不是普通 reference，是其余条目 `source` 字段的指向目标。若延后，P1-P3 的条目将无依据可引，事后回填 `source` 又是一轮返工。

---

## 8. 验收标准

### 8.1 每阶段验收

| 检查项 | 命令 / 方式 |
|---|---|
| 索引一致性 | `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" host-diagnostics` 无错误 |
| 覆盖率健康 | `check_index.py --audit` 输出的 `indexed / eligible_headings` 合理（不追求 100%，见 README § 覆盖率不追求 100%） |
| 版本一致 | 领域 README 版本行与 CHANGELOG 最新条目一致（脚本校验） |
| catalog 双向一致 | 脚本全局检查自动覆盖 |

### 8.2 领域整体验收

- [ ] 每条 reference 判据可对应到**具体可采集的证据**，不是概念介绍
- [ ] 每条判据标注了**结论强度**（能得出确认还是仅供推测）
- [ ] 明确记录了**超出覆盖的边界**——哪些现象本知识库判不了
- [ ] 硬件阈值全部标为**可调参数**并记录定值依据
- [ ] 无任何条目内嵌**具体产品黑名单**（符合 § 1.3 约束）
- [ ] 与 `dotnet-debugging` **零重复**：抽查 5 条，确认无同一事实两处登记
- [ ] `docs/aha-doctor-analysis.md` 已在收口阶段删除，仓库内无第二份副本（`grep -r "aha-doctor-analysis"` 无残留引用）
- [ ] teardown 中【推断】标记的内容**未被任何 `source` 字段引用**

### 8.3 判据质量的检验标准

每条判据须能填满这个模板，填不满说明还不够具体：

```
现象/输入：<可观测的具体数据>
判据：<看到什么算命中>
结论：<命中说明什么>
强度：<已确认 | 推测 | 需进一步取证>
下一步：<还要查什么>
```

---

## 9. 待确认事项

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| 1 | 领域名 `host-diagnostics` | 目录名、全部 ID 前缀 | ✅ **已确认采纳** |
| 2 | `applies_to` 中 .NET 版本 | 索引字段取值 | ✅ **已确认**：`.NET 8+` / `.NET Framework 4.6.2+` |
| 3 | aha_doctor 分析文档归属 | 目录结构、迁移动作 | ✅ **已确认**：迁入 `reference/aha-doctor-teardown.md`，见 § 5.9 |
| 4 | 是否需要 VDI 领域（P7） | 一篇 reference 的工作量 | ⏳ 按目标用户场景定，可延后 |
| 5 | 硬件阈值的定值依据从哪来 | 影响 `hardware-thresholds.md` 可信度 | ⏳ 建议先用行业通用值 + 标注"待实测校准" |
| 6 | 是否同步建配套 skill | 知识库是"传感器"，反查表是"引导器" | ⏳ 建议知识库先行，工具开发时再评估 |

> 第 6 项对应 AGENTS.md 的自检要求：「这个 skill 是引导器还是传感器？有没有配对的另一半？」本 spec 只建知识库，尚无配对 skill——这是有意的，因为工具形态未定。

### 9.1 版本影响

按 AGENTS.md 触发矩阵，本 spec 的实施：

| 改动 | 版本动作 |
|---|---|
| 新建 `knowledge-base/host-diagnostics/` | 该领域独立起 `0.1.0`（分领域版本化，无全局版本号） |
| 更新 `knowledge-base/catalog.json` | 随领域新增同步，无独立版本号 |
| 删除 `docs/aha-doctor-analysis.md` | `docs/` 下改动**不升任何版本号** |
| 本 spec 自身（`docs/superpowers/specs/`） | 不升任何版本号 |

**不涉及任何插件 `plugin.json`** ——本次改动全部落在 `knowledge-base/` 与 `docs/`，两者都不随插件分发。

---

## 10. 本 spec 的边界

**本 spec 不涉及**：诊断工具本身的架构、UI、技术选型、开发计划。这些应在工具开发启动时另开 spec。

**本 spec 的知识来源**：对 aha_doctor 的只读静态分析（现为 `knowledge-base/host-diagnostics/reference/aha-doctor-teardown.md`）。该分析已明确标注了三类来源（官方/实测/推断）与四个未能覆盖的问题——本 spec 继承其边界，**不把推断当作已证实的判据写入知识库**。

**一处须在实施时警惕**：aha_doctor 的检测项清单可以继承，但它**为什么这么定阈值、为什么把某类模块判为可疑**，静态分析给不出答案。实施时若发现某条判据只能追溯到"aha_doctor 这么做"而无法说明理由，应标为待验证，不直接登记为判据。
