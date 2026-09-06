# C# 取证手段

> 前八篇是**诊断理论**（判什么、凭什么判），本篇是**实现约束**（在 C# 里能不能拿到、拿的代价是什么）。两者分开是因为理论稳定，而实现手段随 .NET 版本演进。

⚠️ **本篇是全领域唯一按框架分化的一篇。** 目标运行时为 **.NET 8+** 与 **.NET Framework 4.6.2+**，两者能力不对等。索引中只适用于单一框架的条目，`applies_to` 必须如实收窄，**不得**统一标全集。

## 1. 取证手段总表

下表按检测项列出 C# 侧路径。「需 P/Invoke」为「是」的项，托管 API 无对应能力或能力不足（理由见 § 3）。

| 检测项 | C# 路径 | 需 P/Invoke | 框架差异 |
|---|---|---|---|
| 进程已加载模块 | `Process.Modules` | 否 | 无 |
| 模块数字签名 | `wintrust!WinVerifyTrust` | **是** | 无（两者均须 P/Invoke） |
| 已安装安全软件 | WMI `ROOT\SecurityCenter2` | 否 | **有**（见 § 2） |
| 防火墙 profile 状态 | `HNetCfg.FwPolicy2` COM | 否 | 有（COM 互操作在 .NET 8+ 需显式配置） |
| WFP 过滤器枚举 | `fwpuclnt!FwpmFilterEnum0` | **是** | 无 |
| LSP / 协议链 | `ws2_32!WSCEnumProtocols` | **是** | 无 |
| 系统代理配置 | `winhttp!WinHttpGetIEProxyConfigForCurrentUser` | **是** | 无 |
| DNS 解析 | `Dns.GetHostEntryAsync` | 否 | 无 |
| ICMP 连通性 | `System.Net.NetworkInformation.Ping` | 否 | 无 |
| TCP 可达性 | `TcpClient.ConnectAsync` | 否 | 无 |
| TLS 握手与证书链 | `SslStream` + `X509Chain` | 否 | **有**（默认 TLS 版本、证书校验回调签名不同） |
| 网卡与路由 | `NetworkInterface.GetAllNetworkInterfaces` | 否 | 无 |
| 性能计数（CPU/磁盘/内存） | `PerformanceCounter` | 否 | **有**（见 § 5） |
| 物理内存总量与可用量 | `kernel32!GlobalMemoryStatusEx` | **是** | 无（托管无对应 API） |
| 磁盘容量与类型 | `DriveInfo` + `IOCTL_STORAGE_QUERY_PROPERTY` | 部分 | 无 |
| CPU 指令集支持 | `System.Runtime.Intrinsics.X86.*.IsSupported` | 否 | **有**（Framework 无 `Intrinsics`，须 `IsProcessorFeaturePresent`） |
| GPU 与显示适配器 | WMI `Win32_VideoController` | 否 | 有（同 WMI 差异） |
| 系统事件日志 | `EventLogReader`（`System.Diagnostics.Eventing.Reader`） | 否 | **有**（.NET 8+ 需 NuGet 包） |
| ETW 采集 | `TraceEvent` 库，或外部 `wpr.exe` | 否 | 有（见 § 6、§ 7） |

**表的用法**：这不是"应该全都实现"的清单。按 `reference/symptom-routing.md` 的现象分流结果，只采集本次路由指向的项。全量采集在故障机器上代价过高，且会稀释证据。

## 2. WMI 的权衡

WMI 是最顺手的取证入口——一句 WQL 拿到结构化结果，覆盖安全软件、显卡、磁盘、操作系统版本等大量检测项。但它在**故障机器上恰恰是最不可靠的一环**。

### 2.1 风险

| 风险 | 后果 |
|---|---|
| `Winmgmt` 服务异常或 WMI 仓库损坏 | 查询长时间挂起，**不抛异常也不返回** |
| 某些 provider（尤其第三方安装的）本身有 bug | 单条查询拖垮整个诊断流程 |
| 安全软件拦截 WMI 调用 | 查询失败或超时——而这正是我们要诊断的场景 |

⚠️ **诊断工具跑在故障机器上**。把「WMI 一定可用」当作前提，等于假设被诊断的环境是健康的——这与工具存在的理由矛盾。

### 2.2 处置：主用 + 超时保护 + 兜底

**必须**满足三条：

1. **每次 WMI 查询设置独立超时**（建议 3–5 秒，可配置）。`ManagementObjectSearcher` 的 `EnumerationOptions.Timeout` 只作用于枚举，**不覆盖连接阶段**——须在外层再包一层 `Task` 超时。
2. **超时后放弃该项并记录"未采集"**，不得阻塞后续项，也不得把超时当作"未安装"。这是 `rules/02 § 4 缺失证据不等于反证` 的直接落地。
3. **对关键项准备 P/Invoke 或注册表兜底路径**。例：显卡信息可退到 `EnumDisplayDevices`；磁盘容量可退到 `DriveInfo`。

### 2.3 框架差异

| | .NET Framework 4.6.2+ | .NET 8+ |
|---|---|---|
| `System.Management` | BCL 内置，直接引用 | 须 NuGet 引 `System.Management`，且**仅 Windows** |
| 异步 API | 有 `ManagementObjectSearcher.Get()` 同步为主 | 同左；包本身是对 Framework API 的移植，无新增异步面 |
| AOT 兼容性 | 不适用 | **不兼容**——依赖 COM 与反射，见 § 8 |

## 3. 必须 P/Invoke 的项

以下四项在两个框架下**均无托管等价 API**，只能 P/Invoke。它们不是"为了性能才这么写"，而是托管面根本没有这个能力。

### 3.1 模块数字签名验证

| 项 | 内容 |
|---|---|
| API | `wintrust!WinVerifyTrust`（信任状态）+ `crypt32!CryptQueryObject`（取签名者信息） |
| 为什么必须 | `X509Certificate.CreateFromSignedFile` 只能读出证书，**不做信任链与吊销校验**，也不识别 catalog 签名 |
| 关键参数 | `WINTRUST_ACTION_GENERIC_VERIFY_V2`；`dwUIChoice = WTD_UI_NONE`（诊断工具**不得**弹 UI） |
| 陷阱 | 吊销检查会发起网络请求。故障场景常伴随网络不通，须设 `WTD_REVOKE_NONE` 或接受超时 |

⚠️ **验签结果只能得出「签名有效 / 无效 / 无签名」，不能得出「安全 / 恶意」。** 见 `reference/module-injection.md` 对签名证据强度的界定。

### 3.2 WFP 过滤器枚举

| 项 | 内容 |
|---|---|
| API | `fwpuclnt!FwpmEngineOpen0` → `FwpmFilterCreateEnumHandle0` → `FwpmFilterEnum0` |
| 为什么必须 | 无任何托管封装 |
| 权限 | **需管理员**。非管理员下 `FwpmEngineOpen0` 返回 `ERROR_ACCESS_DENIED` |
| 编组难点 | 返回嵌套非托管结构体数组，须手工 `Marshal.PtrToStructure` 并配对 `FwpmFreeMemory0` |

**降级路径**：非管理员时跳过本项，记录「因权限未采集」——不得据此判定"无过滤器"。

### 3.3 LSP / 协议链枚举

| 项 | 内容 |
|---|---|
| API | `ws2_32!WSCEnumProtocols`（32 位）/ `WSCEnumProtocols32`（64 位进程查 32 位链） |
| 为什么必须 | 无托管封装 |
| 陷阱 | **64 位进程默认只看到 64 位协议链**。32 位宿主进程的问题须另调 `WSCEnumProtocols32` 才能看全 |

### 3.4 系统代理配置

| 项 | 内容 |
|---|---|
| API | `winhttp!WinHttpGetIEProxyConfigForCurrentUser` |
| 为什么必须 | `WebRequest.DefaultWebProxy` 反映的是**当前进程的托管配置**，不等于系统实际生效的 WinHTTP 代理 |
| 补充 | PAC 脚本场景须再调 `WinHttpGetProxyForUrl` 才知道目标 URL 实际走哪个代理 |
| 陷阱 | 返回的三个字符串指针须逐个 `GlobalFree`，否则泄漏 |

⚠️ **代理配置分三层**：WinHTTP 机器级（`netsh winhttp`）、WinINET 用户级（IE 设置）、进程内托管配置。三者可以互不一致，取证时须说明取的是哪一层。

## 4. 托管封装够用的项

以下项**不要**P/Invoke——托管 API 覆盖完整，手写互操作只会增加出错面。

| 项 | API | 说明 |
|---|---|---|
| ICMP 探测 | `Ping.SendPingAsync` | 支持超时与 TTL；注意 ICMP 常被防火墙丢弃，不通**不代表**主机不可达 |
| 网卡 / 路由 / DNS 服务器 | `NetworkInterface`、`IPGlobalProperties` | 覆盖 `ipconfig /all` 的绝大部分信息 |
| 注册表读取 | `Microsoft.Win32.Registry` | 注意 `RegistryView.Registry64` / `Registry32` 的显式指定，见 § 4.1 |
| 进程模块列表 | `Process.Modules` | 见 § 4.2 的两处限制 |
| 磁盘容量 | `DriveInfo` | 类型判定（SSD/HDD）仍须 IOCTL |
| 服务状态 | `ServiceController` | 可判 `Winmgmt`、`Dnscache` 等关键服务是否在跑 |

### 4.1 注册表视图必须显式指定

32 位进程读 `HKLM\SOFTWARE\...` 默认被重定向到 `Wow6432Node`。**必须**用 `RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)` 显式指定视图，否则在 32 位宿主上会读到不同的分支，得出与实际不符的结论。

诊断 AppInit_DLLs 一类的注入点时（见 `reference/system-environment-hijack.md`），**两个视图都要读**——它们是两份独立的值。

### 4.2 `Process.Modules` 的两处限制

| 限制 | 后果 |
|---|---|
| **位数必须匹配** | 32 位诊断进程枚举 64 位目标进程的模块会失败。诊断工具应发布为 64 位，或按目标位数分发两个版本 |
| **只能看到已加载的** | 延迟加载、已卸载、或以 `MEM_PRIVATE` 手工映射的代码不在列表内。见 `reference/module-injection.md` 对该盲区的说明 |

**权限**：枚举其他进程模块需 `PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`。诊断自身进程无此问题，但本领域的场景是「诊断宿主进程」，通常是**另一个进程**——须考虑管理员权限与保护进程（PPL）两种失败情形。

## 5. 性能计数

`reference/hardware-thresholds.md` 要求全部资源判据基于**多次采样**而非瞬时值。这一节说明在 C# 里怎么采、以及两个框架的差异。

### 5.1 `PerformanceCounter` 的框架差异

| | .NET Framework 4.6.2+ | .NET 8+ |
|---|---|---|
| 可用性 | BCL 内置 | 须 NuGet 引 `System.Diagnostics.PerformanceCounter`，**仅 Windows** |
| 类别枚举（`PerformanceCounterCategory.GetCategories`） | 支持 | 支持，但在计数器损坏的机器上更易抛异常 |
| 首次读取延迟 | 数百毫秒级 | 同左 |
| AOT | 不适用 | **不兼容** |

### 5.2 两个必须遵守的采样约束

1. **第一次 `NextValue()` 恒为 0 或无意义**——增量型计数器需要两个采样点。**必须**丢弃首次读数，间隔 ≥ 1 秒后再读。写成"读一次就用"是新手最常见的错误，会稳定产出错误结论。
2. **计数器名受系统语言影响**。中文系统上英文类别名可能不匹配。**优先用 PDH 的语言无关索引**（`pdh!PdhLookupPerfNameByIndex`）或改用其他数据源，不要硬编中文名——硬编会让工具在英文系统上静默失效。

### 5.3 计数器损坏的可能

性能计数器本身可能损坏（表现为类别缺失或全 0）。这是**故障机器上的常见状态**，不是异常情况。

**处置**：捕获异常并记录「计数器不可用」，走 § 1 表中的兜底路径（如 `GlobalMemoryStatusEx` 取内存）。不得让单个计数器失败中断整个采集。

### 5.4 进程级 vs 系统级

采集**必须**同时覆盖两个层级：

| 层级 | 用途 |
|---|---|
| 系统级（`Processor` / `Memory` 类别） | 判断是否整机资源紧张 |
| 进程级（`Process` 类别，或 `Process` 类的 `TotalProcessorTime` / `WorkingSet64`） | 判断压力是否来自宿主进程本身 |

**只采一层无法完成 `hardware-thresholds.md § 2.3` 要求的分流**——分不清"机器慢"和"这个程序慢"。

## 6. ETW 与 hook 的取舍

### 6.1 为什么不用 hook

⚠️ **本知识库禁止诊断工具向目标进程注入代码或安装 hook**（`rules/01 § 5`）。这一节给出该禁令的技术理由。

| 理由 | 说明 |
|---|---|
| **改变了被观测对象** | 注入本身就是本领域正在排查的故障源之一（见 `reference/module-injection.md`）。用注入去诊断注入，无法区分症状与工具自身 |
| **触发安全软件** | 远程线程创建、模块注入是杀软的高优先级行为特征。诊断工具会被拦截甚至隔离——而"安全软件拦截"同样是待排查项 |
| **可能加剧故障** | 在已经不稳定的进程里执行注入，崩溃风险显著上升。诊断不得让被诊断对象更糟 |
| **不可解释** | 注入后得到的调用序列，无法向用户说明其来源与可信度 |

**ETW 是替代方案**：它是操作系统提供的**旁路观测**通道，不修改目标进程。

### 6.2 `TraceEvent` 库

`Microsoft.Diagnostics.Tracing.TraceEvent` 是唯一成熟的托管 ETW 封装，两个框架均可用。

| 项 | 说明 |
|---|---|
| 权限 | 开启内核会话需**管理员**。用户态 provider 会话在部分场景下不需要 |
| 会话类型 | 实时会话（低延迟、需持续消费）/ 文件会话（写 `.etl` 后离线解析）。**诊断场景优先文件会话**——实时会话要求消费速度跟得上事件产生速度，跟不上就丢事件 |
| **GC 压力** | 高频 provider（如上下文切换、文件 IO）每秒可产生数万事件，托管解析会造成显著分配。**必须**限定 provider 与关键字，并设采集时长上限 |
| API 面差异 | 两个框架均支持，但 Framework 上部分较新的 provider 解析路径未同步更新 |

### 6.3 何时改调外部工具

出现以下任一情况时，**放弃进程内 ETW，改用 § 7 的外部工具**：

| 情况 | 理由 |
|---|---|
| 需要采集**启动阶段** | 诊断工具还没起来，事件已经发生。须提前起会话，外部工具更合适 |
| 需要**内核级**采集（磁盘 IO、上下文切换全量） | 事件量级超出托管解析的承受范围 |
| 需要**跨重启**采集 | boot trace 只有外部工具支持 |
| 诊断工具自身可能被拖慢 | 外部进程采集不占用宿主诊断进程的资源 |

### 6.4 ETW 的固有边界

ETW 能看到**发生了什么**，看不到**为什么**。它给出的是事件序列，不是因果链。把 ETW 输出直接当作结论违反 `rules/03 § 2 相关性不等于因果`。

## 7. 外部工具编排

| 工具 | 来源 | 分发 | 适用 |
|---|---|---|---|
| `wpr.exe` | **Windows 10+ 系统内置** | **免分发** | 首选。ETW 采集、启动追踪 |
| `xperf.exe` | Windows Performance Toolkit（ADK 组件） | **须随工具分发** | `wpr` 不可用或需要旧版特性时 |
| `netsh.exe` | 系统内置 | 免分发 | WinHTTP 代理、WFP 日志、trace 采集 |
| `powercfg.exe` | 系统内置 | 免分发 | 电源策略（影响 CPU 降频，见 `hardware-thresholds.md`） |

### 7.1 优先 `wpr.exe` 的理由

**免分发**是决定性的：随工具分发 `xperf.exe` 意味着分发体积增大、须处理第三方许可、且带签名的外部 exe 更易触发安全软件告警——而"安全软件拦截"正是本领域待排查项之一。

⚠️ Windows 8.1 及更早无内置 `wpr.exe`。若目标环境包含这些系统，须准备 `xperf` 路径或放弃 ETW 采集。

### 7.2 编排的四条约束

| 约束 | 理由 |
|---|---|
| **必须设超时并可取消** | 采集进程挂住会拖死诊断流程；用户须能中止 |
| **输出写到临时目录，不写工作目录** | 与 `rules/01 § 3` 的产物隔离要求一致 |
| **必须重定向 stdout/stderr 并记录退出码** | 外部工具失败时，退出码是唯一可靠的判据 |
| **须处理"已有会话在跑"** | ETW 会话名冲突会直接失败；须先尝试停止同名会话 |

### 7.3 权限

`wpr.exe`/`xperf.exe` 的内核采集**需管理员**。诊断工具应在**需要时按需提权**，而不是整体以管理员启动——后者会让不需要提权的检测项也承担不必要的权限，且降低用户接受度。

## 8. 发布形态约束

诊断工具的发布形态直接决定它在故障机器上能不能跑起来。**装不上的诊断工具没有价值。**

### 8.1 自包含发布

| | .NET Framework 4.6.2+ | .NET 8+ |
|---|---|---|
| 运行时依赖 | 依赖机器上已装的 Framework（4.6.2+ 在 Win10 后基本预装） | **须自包含**，否则依赖用户装运行时 |
| 单文件 | 无原生支持（须第三方打包） | `PublishSingleFile` 支持 |
| 体积 | 小（几 MB） | 自包含约 60–80 MB，裁剪后更小 |

⚠️ **不得要求用户先安装 .NET 运行时**。故障机器可能正是网络不通的那台——下载运行时这一步就走不通。

### 8.2 AOT 的兼容性代价

`PublishAot`（仅 .NET 8+）能大幅减小体积并消除运行时依赖，但与本篇多项手段**不兼容**：

| 能力 | AOT 下的状态 |
|---|---|
| `System.Management`（WMI） | **不可用**（依赖 COM 与反射） |
| `PerformanceCounter` | **不可用** |
| COM 互操作（防火墙 `FwPolicy2`） | 须显式生成互操作代码，实践上很麻烦 |
| P/Invoke（§ 3 的四项） | **可用**——`LibraryImport` 源生成器是 AOT 友好路径 |
| `TraceEvent` | **不可用**（大量反射） |

**结论**：需要 WMI 或性能计数的诊断工具**不能走 AOT**。若坚持 AOT，须把全部检测项改为 P/Invoke 与注册表路径——这是一次可观的额外实现成本，须在选型时明确权衡，而不是发布阶段才发现。

### 8.3 位数选择

| 选择 | 后果 |
|---|---|
| 仅 64 位 | 无法枚举 32 位宿主进程的模块（§ 4.2） |
| 仅 32 位 | 无法枚举 64 位宿主进程的模块；且注册表默认被重定向（§ 4.1） |
| **两个版本，按目标位数选择** | **推荐**。诊断工具须匹配被诊断进程的位数 |

### 8.4 数字签名

诊断工具**自身应签名**。理由：未签名的、会枚举其他进程模块并调用 WFP API 的可执行文件，其行为特征与恶意软件高度重合，极易被安全软件拦截——而这会让工具在最需要它的机器上跑不起来。

## 9. 本篇覆盖边界

**本篇不覆盖：**

| 不覆盖 | 应查 |
|---|---|
| 判据本身（阈值、证据强度、结论措辞） | `rules/` 三篇与其余 reference 篇 |
| 进程内部故障的取证（dump、SOS、CLR 内部状态） | `dotnet-debugging` 领域 |
| C# 语言与 BCL 的通用用法 | `csharp`、`dotnet` 领域 |
| WPF 渲染与 UI 线程问题的定位 | `wpf` 领域 |
| 具体 P/Invoke 签名的完整声明 | 本篇给 API 名与关键参数，签名细节须查 Windows SDK 文档 |
| 非 Windows 平台 | 本领域整体仅覆盖 Windows |

**本篇的时效性弱于其余各篇。** 框架差异表随 .NET 版本演进会失效，`reviewed_at` 到期后**必须**重新核对，不得沿用。这是本篇与其余八篇分开的直接原因。

---
