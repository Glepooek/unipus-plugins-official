# AHA 电脑医生静态分析（外部工具参考）

> **本文档在知识库中的角色**：本领域判据的**依据出处**。检测项清单、网络分层序列、环境劫持检测点均继承自这份分析。
>
> **原始分析日期**：2026-09-06 ｜ **分析对象**：`D:\Feishu\app\aha_doctor`（飞书 Windows 客户端内置）

---

## 0. 阅读须知

### 0.1 三级来源标记

全文每项结论都标注来源，**引用时必须区分**：

| 标记 | 含义 | 可否作为判据依据 |
|---|---|---|
| **【官方】** | 来自飞书帮助中心公开文档 | ✅ 可 |
| **【实测】** | 对本机安装目录的只读静态分析（配置文件、资源文件、PE 元数据、导入表） | ✅ 可 |
| **【推断】** | 基于上述证据的判断，**未经运行验证** | ❌ **不可** |

### 0.2 本文档不可作为判据直接引用的部分

以下内容**不得**被 `index.jsonl` 的 `source` 字段引用为依据，也不得作为知识库判据的出处：

1. **全部【推断】标记的内容**——包括 `task_host.exe` 的角色定位、部分实现机制的推测
2. **§ 6.3 未能覆盖的问题**——这一节记录的是「答不了什么」，不是结论
3. **任何关于加密规则包内容的描述**——4 个 `.dat` 规则包未解密，其内容完全未知

引用时的正确做法：指向【官方】或【实测】标记的具体小节；若某判据只能追溯到【推断】，应标为待验证，不登记为判据。

### 0.3 快照日期与失效条件

⚠️ **本文基于 2026-09-06 的本机快照，分析对象是持续更新的商业软件。**

以下情形会使本文结论部分或全部失效：

| 失效来源 | 影响范围 |
|---|---|
| 厂商发布新版本 | 检测项清单、UI 结构、配置文件字段、二进制依赖均可能变化 |
| 官方帮助文档更新 | 【官方】标记的全部内容 |
| 本机安装的是定制/私有化版本 | `BrandDetect.dat` 的品牌配置与域名清单 |

**因此**：本文的价值在于**故障源分类与检测思路**（这部分相对稳定），而非具体的字段名、文件大小、版本号（这些会变）。引用时优先引用前者。

复核方式：重新对照安装目录检查本文【实测】部分的可观察事实。

### 0.4 分析边界

`aha_doctor.exe` 是字节跳动的已编译商业软件。本次分析**仅限公开可读的配置与资源文件、以及文件元数据层面的观察**。

**未做**：反编译或反汇编二进制、解密受保护的规则包、运行任何 exe、修改任何文件。

`config\` 下有 4 个规则包是加密的（统一 `06e0` 魔数头）：`3partyAppDetect.dat`、`SoftwareDetect.dat`、`ModuleDetect.dat`、`BrowserPlugin.dat`。这是厂商刻意的规则保护。

**这个边界决定了本文的形态**：能讲清楚**检测机制怎么搭的**，讲不了**具体检测规则内容是什么**（哪些模块被判为有害、哪些软件在名单里）。这不是分析做得不够，是静态检查在这里的天花板。

**这也是本领域「知识库给方法，不给名单」这条核心约束的由来**——见领域 README。

---

## 1. 这是什么

**【官方】** AHA 电脑医生是飞书提供的专业故障诊断工具，核心能力包括：

- 自动诊断飞书应用的常见异常（启动失败、卡顿、崩溃、白屏等）
- 系统环境与资源占用检测（CPU、GPU、内存、磁盘、进程状态等）

**【实测】** 它不是飞书独有的组件，而是**字节系客户端通用的诊断框架**——通过配置文件适配不同宿主应用（详见 § 4）。社区亦有用户发现豆包安装目录下附带同一程序。

### 1.1 启动方式与权限

**【官方】** 在安装目录中找到 `aha_doctor.exe`，**选择「以管理员身份运行」**。官方明确提示：不以管理员身份运行，可能导致部分诊断功能无法运行。

**【实测】** 这条要求与 PE 清单一致——`aha_doctor.exe` 与 `task_host.exe` 的清单均为 `asInvoker`，**不会自动弹 UAC**。因此提权必须由用户在启动时手动完成，或由程序在运行时按需发起（主程序持有 `CreateProcessWithTokenW` + `runas` 相关能力）。

> **对本领域的启示**：诊断工具的提权模型是一个必须显式设计的决策点，不能默认「反正要管理员权限」。见 `rules/01-diagnostic-safety.md § 3 提权最小化`（待产出）。

### 1.2 界面语言

**【官方】** 左下角「设置」→「通用设置」可切换界面语言，支持中、英、日三种。

**【实测】** 与资源目录一致：`resources\lang\` 下有 `zh_CN` / `en_US` / `ja_JP` 三套 `gdstrings.ini`。UI 中所有文本通过 `textid` 引用字符串表，不硬编码。

---

## 2. 功能模块

### 2.1 官方文档列出的四类用途

**【官方】**

| 模块 | 什么时候用 | 怎么用 |
|---|---|---|
| **异常诊断** | 启动失败、卡顿、崩溃等异常 | 首页右上角点「开始诊断」→ 查看故障信息 → 按需处理。检出不兼容三方模块时，可逐一「屏蔽」或「全部屏蔽并重启」。问题未解决可点「重新诊断」 |
| **系统信息 / 资源占用** | 网络连接异常、访问卡顿、资源占用过高 | 查看系统环境；「资源占用」标签页可看设备整体 CPU/GPU/内存/磁盘占用，以及各进程的资源占用 |
| **网络诊断** | 消息发送失败、文件上传下载异常、音视频通话卡顿 | 「基础网络环境」/「链路连通性检测」/「自定义域名检测」三个标签页，点「开始检测」 |
| **模块屏蔽** | 白屏、卡顿、卡死、崩溃 | 检测异常模块 → 将飞书加入安全软件白名单，或退出/卸载相关软件 |

> **【官方】关键根因判断**：白屏/卡顿类现象**通常是第三方软件引起飞书功能异常**。
>
> 这是官方给出的根因排序依据，也解释了为什么「三方模块检测」是整个工具里唯一带干预动作的模块。**本领域的现象反查表据此排序**——见 `reference/symptom-routing.md`（待产出）。

### 2.2 实测的完整功能面

**【实测】** 静态分析看到的功能面比官方文档列出的更宽。官方文档面向普通用户，只讲了最常用的四类；资源与字符串表里还包含：

- **高级诊断**：本地应用/更新列表、蓝屏记录、启动耗时分析、自启动项一键屏蔽、最近运行/崩溃记录、电源电池信息
- **工具箱**：Trace 录制、Dump 抓取（支持按 CPU/内存/IO/卡死阈值**自动抓取**）、内核转储、证书一键导入、禁用硬件加速/沙箱、清理缓存、进程退出监控、剪贴板监控、文件句柄监控、键鼠监控、DNS 解析监控、浏览器插件检测
- **显卡检测**、**模块屏蔽**独立页

> ⚠️ **一处需要说明的差异**：`resources\themes\doctor\` 下的目录结构（如 `ui_page_advanced_diagnostics`、`ui_tools`）与官方文档描述的标签页划分不完全对应。可能原因：版本差异、部分功能未对普通用户暴露、或主题目录保留了未启用的界面。**以实际运行界面为准**——本文档未运行程序验证。

### 2.3 异常诊断的六个子模块（本领域故障源分类的来源）

**【实测】** 「异常诊断」不是笼统扫描，是 6 个独立子模块（来自 `ui_exception_diagnosis\` 的目录构成与字符串表）：

| 子模块 | 查什么 | 本领域对应 reference |
|---|---|---|
| **三方模块检测** | 被注入宿主进程的第三方 DLL。列出模块名/软件厂商/检测类型/来源，带「详情」「屏蔽」按钮 | `module-injection.md` |
| **安全软件检测** | 已安装安全软件；防火墙状态（域/专用/公用三种配置文件分别判） | `security-software.md` |
| **网络检测** | 6 个可折叠分区：防火墙检测、网络硬件信息、网络协议栈、网络配置数据（本机 IP/DNS/公网 IP/hosts 异常）、网络访问情况（链路/延迟/IP/城市/LSP/分析/结果 七列）、代理检测 | `network-layered-probe.md` |
| **硬件检测** | CPU/内存/虚拟内存/磁盘使用率/磁盘容量/是否 SSD/GPU，各带阈值；硬件加速开关；CPU 型号兼容性 | `hardware-thresholds.md` |
| **VDI 环境检测** | 磁盘读取速度、传输协议 —— 专为虚拟桌面场景 | `vdi-environment.md`（可选） |
| **系统环境检测** | IFEO 调试器劫持、GlobalFlag、AppCompat 兼容模式、URL 协议注册是否正常 | `system-environment-hijack.md` |

**结果模型**：走**风险计数**而非通过/失败——`共发现 {:d} 项风险信息` / `暂未发现问题`，并记录上次诊断时间。结果可通过「发送给{宿主}」回传给宿主应用。

> **对本领域的启示**：风险计数模型对用户友好，但容易让人把「检出 47 个第三方模块」读成「有 47 个问题」。见 `rules/03-conclusion-strength.md § 4 风险计数不是故障计数`（待产出）。

---

## 3. 实现方法

### 3.1 架构：规则与引擎分离

**【实测】** 这个工具架构上最值得说的一点是**检测逻辑与检测规则分离**：

- 二进制里是**执行引擎**（怎么枚举模块、怎么发探测请求、怎么读注册表）
- 规则在**外部数据文件**里（哪些模块可疑、哪些域名要探、适配哪个宿主）

好处是加品牌、改域名清单、更新恶意模块特征都不用重发二进制。代价是规则包必须加密——否则等于公开黑名单。这正是那 4 个 `.dat` 加密的原因。

**整体形态**：原生 C++ 插件化架构，以 **Chromium `base` 库**为骨架。六个 UI 模块对应 `plugins\` 下独立探测器（`net_detector`、`module_block`、`system_info_querier`、`vdi_environment_querier` 等），统一经 `DoctorIpcHelper` IPC 分发到 `task_server`——符号如 `RunDiagnosis`/`GetThirdModule`/`GetSecureSoftware`/`AutoDumpStart`/`FlushDNS` 均可见。

### 3.2 取数机制

**【实测】** 以下基于 PE 导入表实测解析（本机无 `pefile`，用手写解析器逐个解出 DLL + 函数名），非字符串近似。

| 能力 | 实现 |
|---|---|
| **ETW** | 自建 session：`StartTraceW`/`ProcessTrace`/`EnableTraceEx2` + `tdh.dll` 解析事件。源码路径 `proc_net_traffic_etw.cc`（按进程统计网络流量） |
| **性能计数器** | `pdh.dll` 传统 API + `advapi32` PerfLib v2（`PerfOpenQueryHandle`/`PerfAddCounters`）双路 |
| **事件日志** | `wevtapi`（`EvtQuery`/`EvtRender`），查 `Diagnostics-Performance/Operational` 与 `ProcessExitMonitor` |
| **进程/模块枚举** | Toolhelp（`CreateToolhelp32Snapshot`/`Module32FirstW` → 三方模块检测的数据源）+ `ntdll` 的 `NtQuerySystemInformation`。**未导入 psapi** |
| **硬件信息** | `setupapi`/`cfgmgr32` 枚举设备、`GetSystemFirmwareTable`（SMBIOS）、`GlobalMemoryStatusEx`、`DeviceIoControl`（SSD 判定）、`dxgi`（GPU）、`powrprof`（电池） |
| **网络** | `iphlpapi` 含**原生 `IcmpSendEcho`**；`ws2_32` 45 项含 `WSCEnumProtocols`/`WSCGetProviderPath`（→ LSP 列与「网络协议栈」分区）；`winhttp` 的 `WinHttpGetIEProxyConfigForCurrentUser`（→ 代理检测）；**`fwpuclnt` 枚举 WFP 防火墙过滤器** |
| **签名验证** | `wintrust` 目录签名 + `crypt32` → 三方模块列表的「软件厂商」列 |
| **注册表** | `advapi32` 完整 Reg* 族，含 `RegNotifyChangeKeyValue`（变更监听）。目标：IFEO、`AppCompatFlags\Layers`、`Tcpip\Parameters`、`Dnscache\Parameters` |
| **服务控制** | 仅 `EnumServicesStatusExW`/`QueryServiceConfigW` 等**只读** API，**无** `StartService`/`ControlService`/`ChangeServiceConfig` |
| **崩溃/转储** | `dbghelp` 的 `MiniDumpWriteDump` + `Sym*` 符号解析 |

#### 一个关键设计选择：几乎完全绕开 WMI

**【实测】** 导入表里**没有任何 wbem DLL**。WMI 仅在一处使用——通过 `ole32` 运行时绑定 `ROOT\SecurityCenter2`，只查 `AntiVirusProduct` 和 `FirewallProduct` 两张表。**没有任何 `Win32_*` 硬件类查询**。

**为什么这么做**：WMI 慢、依赖 WMI 服务自身健康、在故障机器上本身就可能查不动——而这工具面对的恰恰是故障机器。

> **对本领域的启示（本文最重要的一条实现经验）**：诊断工具的取证手段必须在故障机器上仍能工作。C# 侧 WMI 是最顺手的路径，但也最容易挂住，须有超时与兜底。见 `rules/02-evidence-standards.md § 3 故障机器上的降级` 与 `reference/dotnet-probing-techniques.md § 2 WMI 的权衡`（均待产出）。

### 3.3 三个具体实现细节

**① 网络诊断的结论文案，是 Chromium 错误码翻译表。**

**【实测】** 字符串表里有 80+ 条 `IDS_NETWORK_NET_ERROR_-xxx`，把 Chromium net error code 映射成中文处置建议。例如 `-202`（证书错误）→「可尝试使用左侧【工具箱】->【证书一键导入】」。说明网络探测走 Chromium 网络栈（合理，宿主是 Electron 类应用），且**诊断结论直接挂接修复动作**。

> **对本领域的启示**：错误码 → 处置建议的映射表是网络诊断的核心产物。但 C# 实现须换成 .NET 错误码体系（`SocketError`/`WebExceptionStatus`/WinHTTP），**映射关系需自建，不可直接抄**。

**② 证书问题的修复手段是自带根证书。**

**【实测】** `config\certs\` 放了 14 个 `.der` + 3 个 `.crt`，全是公共根 CA（DigiCert G2/G3/TLS ECC P384 G5/TLS RSA4096 G5、GlobalSign R3/R6/R46/E46/ECC R5、Sectigo E46/R46、vTrus、Certum）。「证书一键导入」就是把这些装进系统信任存储——针对企业环境根证书缺失导致 TLS 握手失败。

**③ Trace 录制复用微软官方工具链，不是自研。**

**【实测】**

| 项 | `xperf.exe` | `perfctrl.dll` |
|---|---|---|
| CompanyName | **Microsoft Corporation** | **Microsoft Corporation** |
| ProductName | Microsoft® Windows® Performance Analyzer | 同左 |
| 版本 | 6.3.9600.17298 (winblue.141024-1500) | 同左 |
| Authenticode | **Valid, CN=Microsoft Corporation** | **Valid, CN=Microsoft Corporation** |

两者版本与构建分支完全一致，`xperf.exe` 从 `perfctrl.dll` 导入 60 个函数——成套搬运的 Windows Performance Toolkit（Win8.1 时代）原件。主程序只做命令编排（`StartXperf`/`CancelXperf`/`action.command.xperf.start`，源码 `plugins\tools_kit\xperf.cc`）。

三个 Feishu 件签名为 `CN="Beijing Feishu Technology Co."`，全部有效，来源界线清晰。

> **对本领域的启示**：重活外包给微软官方工具是合理策略。C# 侧更应如此——优先 `wpr.exe`（Win10+ 内置，免分发签名问题）。

### 3.4 进程结构

**【实测】** 确证部分：

- 主程序里存在 `task_host.exe`、`LaunchProcess(task_host) failed` 等字符串，确实由主程序拉起
- `task_host.exe`（403 KB）含 PDB 路径 `...\src\out\output\task_host.pdb`，且含 `plugins\tools_kit\xperf.cc`——与主程序共享 xperf 驱动代码
- 导入表极简（11 个 DLL，无网络、无 WMI、无 ETW、无 UI），**自己不做诊断取数**
- 含单实例互斥体 `AhaDoctorTaskHost8DC05A500F9B_%lu`
- 主程序侧存在 `plugins\task_server\proxy\task_proxy.cc` 与整套 `DoctorIpcHelper::*` 符号

**【推断】** ⚠️ **以下为推断，不可作为判据依据引用**：

> `task_host.exe` 是「特权/危险操作的隔离执行载体」——主程序保持普通权限跑 UI，把需要提权（xperf 需 `SeSystemProfilePrivilege`、内核 dump 需 `SeDebugPrivilege`）或可能崩溃的动作外包给它，IPC 回传结果。字符串 `Disable DllBlock IsElevated:` 表明「模块屏蔽」这类写操作会检查提权状态。

**【实测】** `applogrs.dll` 与诊断无关——是埋点上报 SDK（导出 `AppLog_init`/`AppLog_onEvent`/`AppLog_getDeviceId`/`AppLog_setHttpClient`）。

### 3.5 UI 框架

**【实测】** 确证是 **DirectUI/Duilib 系**直接渲染框架，非标准 Win32 控件：根元素 `<Window>`，控件标签 `VBox`/`HBox`/`Label`/`ButtonEx`/`Progress`，属性风格 `width="stretch"`/`margin="l,t,r,b"`/`bkimage`/`class`/`textid`。

结构是**数据驱动列表**：每个子模块 = 容器 XML（标题栏 + 空的 `content_list` 占位）+ 行模板 XML（`*_item.xml`），运行时按数据条数克隆填充。**界面本身不含任何诊断逻辑。**

> 本节与本领域判据无关，仅作实现参考——C#/WPF 实现时这套 XML 对应 `ItemsControl` + `DataTemplate`，属原生能力。

---

## 4. 作用范围与边界

### 4.1 它是宿主应用的定向排查器，不是通用体检工具

**【实测】** `config\BrandDetect.dat` 是**明文 UTF-8 JSON**，结构为：

```
{ "brand_list": [ 16 个品牌 ], "current": "Feishu" }
```

每个品牌两组配置：

- `args` — `exe_file_name_default`（宿主进程名）、`log_dir`、`dump_dir`、`reg_path`、`exe_dir_ini`
- `geo_config` — 按地域的 `domain_list`、`domain_white_list`、`download_test`

飞书的配置：进程 `Feishu.exe`，日志 `sdk_storage\log`，dump `sdk_storage\log\monitor`，注册表 `SOFTWARE\Feishu`；覆盖 6 个地域（CN 25 域名 / JP 7 / SG 12 / VA 10 / MY 9 / US 8），另有 32 条 `domain_white_list`，`download_test` 限 10 MB、超时 10 s。

16 个品牌均为字节系产品线，域名数从 5 到 146 不等。

> **对本领域的启示**：**「宿主进程名 + 服务域名清单」是诊断工具必须外置为配置的两项**。硬编进二进制会让工具只能服务一个产品。这是可直接继承的架构决策。

### 4.2 三条硬边界

1. **仅 Windows**——资源、PE 结构、IFEO/注册表检测项都是 Windows 专有（Mac 版是另一套程序）
2. **仅配置中登记的宿主应用**——换个应用它不知道该查哪个进程、探哪些域名
3. **「网络能不能通」是按宿主服务域名判的**，不是判「你能不能上网」

> 第 3 条是重要判据：**域名可达性 ≠ 能上网**。见 `reference/network-layered-probe.md`（待产出）。

### 4.3 它明确不做的事

**【实测】** 不修复系统故障、不查杀病毒、不做性能优化。**它只出具证据**——修复动作要么给建议文案，要么引导到「工具箱」里的独立功能（证书一键导入、模块屏蔽、禁用硬件加速），与诊断是分开的页面。

唯一例外是三方模块的「屏蔽」，见 § 6.2。

> **对本领域的启示**：**诊断与修复分离**是正确的产品边界。见 `rules/01-diagnostic-safety.md § 1 只读优先`（待产出）。

---

## 5. 值得注意的能力观察

**【实测】** 以下两项均为确证。它们与工具的诊断用途是自洽的，但能力边界值得知悉。

### 5.1 进程内 API Hook 能力

PE 里存在 **`.detourc` / `.detourd` 节**——Microsoft Detours 的特征节。

佐证：`dnsapi.dll` 出现在字符串里但**不在导入表中**，配合源码路径 `monitor_dns_imp.cc` / `monitor_clipboard_imp.cc` / `monitor_raw_input_imp.cc`，说明 DNS 解析监控、剪贴板监控、键鼠监控走的是**运行时 API hook**，而非静态导入。

> **对本领域的启示（明确不继承）**：本知识库**不收录 hook 手法**。理由：托管环境做进程内 hook 不稳、杀软误报率高，且 ETW 可替代（DNS 走 `Microsoft-Windows-DNS-Client` provider，剪贴板走 `AddClipboardFormatListener`，键鼠走 `SetWindowsHookEx`）。见 `rules/01-diagnostic-safety.md § 5 禁止进程内注入`（待产出）。

### 5.2 唯一的系统写操作

三方模块检测的「屏蔽 / 解除屏蔽 / 全部屏蔽并重启」，配合 `CreateProcessWithTokenW` 提权路径，字符串 `Disable DllBlock IsElevated:` 印证会检查提权状态。

**这是整套诊断里唯一具备系统修改能力的项**——其余全部为只读采集，连服务控制都只有查询 API（无 `StartService`/`ControlService`/`ChangeServiceConfig`）。

> **对本领域的启示**：对一个诊断工具来说这个边界守得算干净，可作为设计参照——**只读为默认，写操作是显式例外且需单独设计确认与回滚**。

### 5.3 未能覆盖的问题

⚠️ **本节记录的是「答不了什么」，不是结论，不可作为判据引用。**

以下问题静态分析无法回答，如需结论须另行验证：

| 问题 | 为什么答不了 |
|---|---|
| 具体检测哪些模块/软件算异常 | 规则在加密包内 |
| 阈值具体定在多少 | 内置于二进制 |
| 诊断结果上报了什么、传给谁 | 需运行时抓包；`applogrs.dll` 是埋点 SDK，但上报内容未知 |
| 数据保留策略、隐私边界 | 官方文档未涉及，静态不可见 |
| 实际运行时的标签页划分 | 主题目录与官方描述不完全对应，需运行确认 |

> **这张表直接决定了本领域的两条约束**：① 不内置产品黑名单（规则内容未知）；② 硬件阈值须自定并标注依据（原阈值未知）。见领域 README 与 `reference/hardware-thresholds.md`（待产出）。

---

## 6. 本篇覆盖边界

**本篇能提供**：

- 故障源的分类框架（六个子模块 → 本领域六篇 reference 的划分依据）
- 网络分层排查的序列
- 环境劫持的四个检测点
- 取证机制的选型经验（绕开 WMI、外包 ETW 录制、双进程提权）
- 产品边界的设计参照（诊断与修复分离、只读为默认）

**本篇不能提供**：

- 任何具体的检测规则内容（加密包未解密）
- 任何阈值的具体数值（内置于二进制）
- 运行时行为的验证（未运行程序）
- 上报与隐私的事实（静态不可见）

**引用本篇时**：优先引用【官方】与【实测】标记的小节；【推断】内容与 § 5.3 不得作为判据依据。详见 § 0.2。

---

## 参考来源

**官方文档**

- [使用 Windows 版 AHA 电脑医生](https://www.feishu.cn/hc/zh-CN/articles/294755026335-%E4%BD%BF%E7%94%A8-windows-%E7%89%88-aha-%E7%94%B5%E8%84%91%E5%8C%BB%E7%94%9F)
- [在 Windows 中使用飞书时出现白屏或卡顿等现象怎么办？](https://www.feishu.cn/hc/zh-CN/articles/413916844794-%E5%9C%A8-windows-%E4%B8%AD%E4%BD%BF%E7%94%A8%E9%A3%9E%E4%B9%A6%E6%97%B6%E5%87%BA%E7%8E%B0%E7%99%BD%E5%B1%8F%E6%88%96%E5%8D%A1%E9%A1%BF%E7%AD%89%E7%8E%B0%E8%B1%A1%E6%80%8E%E4%B9%88%E5%8A%9E)
- [使用 Mac 版 AHA 电脑医生](https://www.feishu.cn/hc/zh-CN/articles/150689469947-%E4%BD%BF%E7%94%A8-mac-%E7%89%88-aha-%E7%94%B5%E8%84%91%E5%8C%BB%E7%94%9F)

> ⚠️ 官方帮助中心正文为客户端渲染，直接抓取仅得标题。本文【官方】部分内容经搜索引擎中转获取，措辞可能与原文有出入，事实点已交叉核对。

**社区**

- [Windows 豆包安装目录下有一个 Aha 电脑医生程序是干什么的?](https://www.v2ex.com/t/1175965) — 印证该工具为字节系客户端通用组件

**静态分析对象**

- `D:\Feishu\app\aha_doctor\`（2026-09-06 本机快照）
