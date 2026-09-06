# 进程与系统命令行取证手册

> `cli-probe-toolbox.md` 覆盖**网络层**，本篇覆盖其余四类故障源：模块注入、安全软件、硬件资源、环境劫持。
>
> 两篇口径一致：**判据在各自的 reference 篇，本篇只给「敲什么命令、看输出的哪个字段」**，cmd 与 PowerShell 双栏，全部 Windows 内置零安装。

⚠️ **本篇与网络篇的关键差异：权限。**

网络层的探测绝大多数普通用户即可执行，本篇则不然——枚举他进程模块、读 `HKLM`、查安全产品、采性能计数，多数需要管理员。**每节的命令表都标注了权限要求，不得默认以管理员运行全部命令**（理由见 `dotnet-probing-techniques.md § 7.3`）。

## 1. 本篇的结论强度基线

⚠️ **本篇多数判据只能给「推测」，这与网络篇相反。**

网络篇的分层定位是「已确认」（`network-layered-probe.md § 11` 称其为"本篇最强的产出"），因为网络故障有明确的层次归属。本篇四类故障源没有这个性质：

| 领域 | 存在性 | 因果性 | 依据 |
|---|---|---|---|
| 模块注入 | 已确认 | **推测**——除非停用复现 | `module-injection.md` 结论强度基线 |
| 安全软件 | 已确认（有覆盖缺口） | **推测**——查不到"它拦了什么" | `security-software.md § 3.1` |
| 硬件资源 | 已确认（测量事实） | **推测**——因果方向常相反 | `hardware-thresholds.md § 2.3` |
| 环境劫持 | **已确认** | 推测 | `system-environment-hijack.md` |

**环境劫持是唯一例外**——注册表键值存在与否是客观事实且语义明确，故 § 6 是本篇唯一能大量给出「已确认」的一节。

⚠️ **这意味着本篇的命令产出的是「候选项」，不是「结论」。** 把「检出 3 个无签名模块」写成「发现 3 个问题」，正是 `rules/03-conclusion-strength.md § 4 风险计数不是故障计数` 所禁止的形态。

## 2. 三条执行纪律

网络篇 § 2 的三条纪律同样适用（留原始输出、多次采样、只读不改），此处只列**本篇特有**的三条。

### 2.1 采集时机决定结果有效性

⚠️ **模块是动态加载的。** `module-injection.md § 1` 要求「排查白屏/崩溃类现象时，应在现象复现后立即枚举」。

| 采集时机 | 后果 |
|---|---|
| 启动瞬间 | 漏掉延迟加载与运行时注入的模块 |
| **现象复现后立即** | **正确时机** |
| 现象恢复后 | 干扰模块可能已卸载 |

这同时是 `rules/02-evidence-standards.md § 4 时间窗口对齐` 的要求：多源证据须记录各自采集时刻，跨源比对前确认窗口重叠。

### 2.2 权限不足必须显式记录，不得当作「未发现」

⚠️ **本篇多数命令在权限不足时会「成功返回但结果不全」**，而非报错——这是最危险的失效形态。

| 命令 | 权限不足时 |
|---|---|
| `tasklist /m` | 只返回本用户进程，**不报错** |
| `Get-Process -Module` | 部分进程抛错，其余正常返回 |
| `Get-NetFirewallRule` | 可读，但 WFP 层枚举需管理员 |
| `Get-Counter` | 部分计数器类别不可见 |

**必须**按 `rules/02 § 3` 记录「因权限未采集」，**不得**据此判定「不存在」。这与 `dotnet-probing-techniques.md § 3.2` 对 WFP 枚举的降级要求是同一条。

### 2.3 只读，不改配置

同网络篇 § 2.3。本篇涉及的修改类命令风险更高：

| 修改类命令 | 为什么不在诊断阶段 |
|---|---|
| `reg add` / `reg delete` | 直接改劫持点配置，销毁证据且可能致系统不可启动 |
| `taskkill` | 终止进程会使模块列表证据消失 |
| `sc stop` / `Stop-Service` | 停用安全服务属高风险，且企业环境多无权限 |
| `sfc /scannow` / `DISM` | 会修改系统文件，耗时且掩盖原始状态 |

⚠️ **`module-injection.md § 5.1` 与 `security-software.md § 4.3` 都指出「停用后复现」是唯一能确认因果的手段——但两篇同时声明它属系统修改，须由用户决策执行，不在诊断阶段。** 本篇给出的全部命令均为只读，不含停用动作。

---

## 3. 模块注入：枚举与分类

对应 `module-injection.md § 1`（检测框架四步：枚举 → 验签 → 分类 → 判定）。本节覆盖第 1、3 步，验签见 § 4。

### 3.1 命令

| 目的 | cmd | PowerShell | 权限 |
|---|---|---|---|
| **列出指定进程的模块** | `tasklist /m /fi "imagename eq <exe>"` | `Get-Process <名> \| Select-Object -ExpandProperty Modules` | 管理员（他用户进程） |
| 含模块路径 | 无（`tasklist` 只给模块名） | `(Get-Process <名>).Modules \| Select-Object ModuleName, FileName` | 同上 |
| 反查某 DLL 被谁加载 | `tasklist /m <dll名>` | — | 同上 |
| 进程基本信息 | `tasklist /v /fi "imagename eq <exe>"` | `Get-Process <名> \| Format-List *` | 部分需管理员 |
| **进程的位数** | 无直接等价 | 见 § 3.3 | — |

⚠️ **`tasklist /m` 只给模块名，不给路径。** 而 `module-injection.md § 2` 的五个可疑维度中，**文件路径是权重「高」的维度**（临时目录/用户目录/含随机串）。因此 `tasklist /m` **不足以完成判定**——必须用 PowerShell 取 `FileName`：

```powershell
Get-Process <名> -ErrorAction Stop |
  Select-Object -ExpandProperty Modules |
  Select-Object ModuleName, FileName, @{n='Size';e={$_.ModuleMemorySize}} |
  Sort-Object FileName
```

### 3.2 分类：把上百个模块缩到个位数

`module-injection.md § 1` 强调「判定只在第三方子集上进行」——一个正常 WPF 进程加载 100+ 模块，不分类直接看数量毫无意义。

按路径三分：

```powershell
$p = Get-Process <名> -ErrorAction Stop
$sys = "$env:SystemRoot\"
$self = (Split-Path $p.Path -Parent) + '\'
$p.Modules | ForEach-Object {
    $f = $_.FileName
    $cls = if ($f -like "$sys*") { 'System' }
           elseif ($f -like "$self*") { 'Self' }
           else { 'ThirdParty' }
    [PSCustomObject]@{ Class = $cls; Name = $_.ModuleName; Path = $f }
} | Group-Object Class | Select-Object Name, Count
```

列出第三方子集（后续判定只在这个集合上做）：

```powershell
$p.Modules | Where-Object { $_.FileName -notlike "$sys*" -and $_.FileName -notlike "$self*" } |
  Select-Object ModuleName, FileName
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| `ThirdParty` 计数为 0 | 无第三方模块注入 | 已确认 |
| `ThirdParty` 子集非空 | 候选项，**须按 § 4 逐维度评估** | 已确认（存在）｜ 推测（是否为主因） |
| 第三方模块路径在**临时目录 / 用户目录 / 含随机串** | 高可疑（`module-injection.md § 2` 权重「高」） | 推测 |

⚠️ **「第三方模块存在」本身不是结论。** `module-injection.md` 篇首明确：一台正常机器上通常也有若干第三方模块。这一步的产出是**候选集**，不是问题清单。

### 3.3 位数必须匹配，否则枚举静默失败

⚠️ **这是本节最危险的陷阱。** `module-injection.md § 1` 与 `dotnet-probing-techniques.md § 4.2` 都指出：32 位进程枚举 64 位目标会失败或**只得到部分结果**——静默的错误来源。

先确认目标进程位数：

```powershell
Get-Process <名> | ForEach-Object {
    [PSCustomObject]@{
        Name  = $_.Name
        Path  = $_.Path
        Bits  = if ([Environment]::Is64BitOperatingSystem) {
                    # 查询进程是否运行在 WOW64（即 32 位进程运行于 64 位系统）
                    $w = [bool]0
                    if ([Wow]::IsWow64Process($_.Handle, [ref]$w)) { if ($w) {'32-bit'} else {'64-bit'} } else {'unknown'}
                } else {'32-bit'}
    }
}
```

需先注册 P/Invoke（一次性）：

```powershell
Add-Type -Namespace Wow -Name Wow -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError=true)]
public static extern bool IsWow64Process(System.IntPtr h, out bool w);
'@ -PassThru | Out-Null
```

**更简单的替代判据**（不需 P/Invoke）：看模块列表里是否含 `SysWOW64` 路径的系统 DLL——含即为 32 位进程。

```powershell
if ((Get-Process <名>).Modules.FileName -match 'SysWOW64') { '32-bit 进程' } else { '64-bit 进程' }
```

⚠️ **PowerShell 自身的位数决定能枚举什么。** 64 位系统上默认 `powershell.exe` 为 64 位，可枚举 64 位目标；要枚举 32 位目标的完整模块列表，须用 `%SystemRoot%\SysWOW64\WindowsPowerShell\v1.0\powershell.exe`。

### 3.4 本节的边界

| 判不了 | 原因 |
|---|---|
| **加载方式（静态导入 vs 运行时注入）** | ⚠️ `module-injection.md § 2.2` 称这是**权重最高**的维度，但命令行拿不到——须解析 PE 导入表并与已加载列表比对。见 § 3.5 |
| 模块是否为现象主因 | `module-injection.md` 结论强度基线；须经停用复现（属修改操作） |
| 枚举时机之外的模块 | 动态加载可能在枚举后才发生，见 § 2.1 |

### 3.5 ⚠️ 命令行的能力缺口：拿不到加载方式

**这是本篇最重要的一处坦白。**

`module-injection.md § 2` 的五个维度中，**权重「最高」的「加载方式」（非导入却已加载 → 运行时注入）在命令行侧无法取得**。原因：判定需要解析每个已加载模块的 PE 导入表，构建导入链，再找出不在链上的模块——没有任何内置命令提供这个能力。

| 维度 | 权重 | 命令行可得 |
|---|---|---|
| 签名状态 | 高 | ✅ § 4 |
| 签名主体 | 中 | ✅ § 4 |
| 文件路径 | 高 | ✅ § 3.1 |
| **加载方式** | **最高** | ❌ **不可得** |
| 模块功能与宿主关系 | 中 | 部分（靠签名主体与文件描述推断） |

**后果**：命令行侧的模块判定**天然弱于**完整实现。可用的四个维度能给出可疑度排序，但拿不到最强的那个信号。

**替代路径**：

| 路径 | 说明 |
|---|---|
| 交叉验证注册表注入点 | § 6 的 AppInit_DLLs / IFEO / ShellExecuteHooks 有静态痕迹，两侧命中即强证据链（`module-injection.md § 3.1`） |
| DLL 劫持判定 | § 4.3 可从路径直接判定，不需导入表 |
| 完整实现 | 须按 `dotnet-probing-techniques.md` 走托管/P-Invoke 路径 |

⚠️ **`CreateRemoteThread` 与 `SetWindowsHookEx` 两种手法无静态痕迹**（`module-injection.md § 3` / § 7），命令行与完整实现都只能观察结果，无法反推注入源头。这不是命令行的局限，是手法本身的性质。

---

## 4. 模块注入：验签与路径判定

对应 `module-injection.md § 1` 第 2 步与 § 2.1 的三个陷阱。

### 4.1 命令

| 目的 | cmd | PowerShell | 权限 |
|---|---|---|---|
| **验证单个文件签名** | 无内置 | `Get-AuthenticodeSignature <路径>` | 普通用户 |
| 批量验证模块签名 | — | 见 § 4.2 | 管理员（枚举他进程） |
| 查看文件版本与厂商 | — | `(Get-Item <路径>).VersionInfo` | 普通用户 |

⚠️ **cmd 侧无验签工具。** Sysinternals `sigcheck` 需下载，按网络篇 § 1.2 同一理由不收录。`Get-AuthenticodeSignature` 是唯一的零安装路径。

### 4.2 批量验签：第三方子集

```powershell
$sys = "$env:SystemRoot\"
$p = Get-Process <名> -ErrorAction Stop
$self = (Split-Path $p.Path -Parent) + '\'
$p.Modules |
  Where-Object { $_.FileName -notlike "$sys*" -and $_.FileName -notlike "$self*" } |
  ForEach-Object {
      $sig = Get-AuthenticodeSignature $_.FileName
      [PSCustomObject]@{
          Name    = $_.ModuleName
          Status  = $sig.Status            # Valid / NotSigned / UnknownError / HashMismatch ...
          Signer  = $sig.SignerCertificate.Subject
          Company = (Get-Item $_.FileName).VersionInfo.CompanyName
          Path    = $_.FileName
      }
  } | Format-List
```

### 4.3 判读：`Status` 的语义与三个陷阱

`module-injection.md § 2.1` 列了三个陷阱，全部在 `Status` 字段上体现：

| `Status` 取值 | 含义 | ⚠️ 陷阱 |
|---|---|---|
| `Valid` | 签名有效且信任链完整 | **陷阱②：有效签名 ≠ 无害**。大量兼容性问题恰恰来自签名有效的正规软件 |
| `NotSigned` | 确认无签名 | 高可疑（`module-injection.md § 2` 权重「高」） |
| `UnknownError` | **无法验证**（常因吊销检查需联网而失败） | **陷阱①：验签失败 ≠ 无签名**。须区分记录，报成 `NotSigned` 是常见误判 |
| `HashMismatch` | 文件被篡改 | 强信号 |
| `NotTrusted` | 签名者不在受信任根 | 须结合企业环境判断（内部 CA 属正常） |

⚠️ **陷阱① 在命令行侧尤其容易踩**：`Get-AuthenticodeSignature` 在网络不通时对需要 OCSP 校验的文件返回 `UnknownError`——而**网络不通恰恰可能是当前正在排查的故障**（见 `dotnet-probing-techniques.md § 3.1` 的同一警告）。

**处置**：`UnknownError` 必须单独归类，**不得**并入 `NotSigned` 统计。

⚠️ **陷阱③：过期签名 ≠ 失效。** 若签名带可信时间戳，证书过期后签名仍有效。`Get-AuthenticodeSignature` 的 `Status` 已考虑时间戳，故直接看 `Status` 即可，**不要**自行比对 `SignerCertificate.NotAfter` 与当前时间——那样会把有效签名误判为失效。

### 4.4 DLL 劫持：命令行能给「已确认」的一项

`module-injection.md § 3.2` 指出这是少数能给「已确认」的注入判定——系统 DLL 的预期路径是确定的。

```powershell
$sysDirs = @("$env:SystemRoot\System32\", "$env:SystemRoot\SysWOW64\")
(Get-Process <名>).Modules | ForEach-Object {
    $name   = $_.ModuleName
    $loaded = $_.FileName
    $fromSys = $false
    foreach ($d in $sysDirs) { if ($loaded -like "$d*") { $fromSys = $true } }
    $alsoInSys = @()
    foreach ($d in $sysDirs) { if (Test-Path (Join-Path $d $name)) { $alsoInSys += (Join-Path $d $name) } }
    if (-not $fromSys -and $alsoInSys.Count -gt 0) {
        [PSCustomObject]@{ Module = $name; LoadedFrom = $loaded; AlsoInSystem = ($alsoInSys -join '; ') }
    }
} | Format-List
```

**判读**：输出非空即表示存在「同名 DLL 在系统目录也有，但进程加载的是别处那个」。

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 系统 DLL 从非系统目录加载 | **搜索顺序劫持** | 已确认 |
| 同名 DLL 在程序目录且系统目录也有 | 须比对签名判断哪个是预期的（用 § 4.2） | 推测 |

⚠️ **须排除已知的合法同名情形**：部分运行时组件（如 VC++ 运行库、.NET 的 `System.*.dll`）在应用目录与系统目录同时存在属正常发布形态。判定前先看签名主体是否与宿主一致。

### 4.5 时间线比对：成本最低的排除手段

`module-injection.md § 5` 把时间线比对列为**成本极低**且能直接排除的手段——安装在现象之后 → 可排除。

```powershell
(Get-Process <名>).Modules |
  Where-Object { $_.FileName -notlike "$env:SystemRoot\*" } |
  ForEach-Object { Get-Item $_.FileName } |
  Select-Object Name, CreationTime, LastWriteTime, DirectoryName |
  Sort-Object LastWriteTime -Descending
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 模块文件时间**晚于**现象首次出现时间 | **可排除**（`module-injection.md § 5`） | 已确认（排除方向） |
| 模块文件时间与现象出现时间接近 | 时间相关性——**不是因果**（`rules/03 § 2`） | 推测 |

⚠️ **文件时间戳可被改写**，且软件更新会刷新时间。与 hosts 的 `LastWriteTime` 同理（网络篇 § 5.2），**不能作为强证据**，只能用于**排除**方向——这个不对称性是有意的：证明"晚于故障"能排除，证明"早于故障"不能定罪。

---

## 5. 安全软件

对应 `security-software.md`。⚠️ **本节的结构性限制先行**：`security-software.md § 3.1` 明确「能查到装了什么，查不到它拦了什么」——**本节全部命令都受这条约束**，没有任何命令能给出「某次失败是否被拦截」。

### 5.1 命令

| 目的 | cmd | PowerShell | 权限 |
|---|---|---|---|
| **已注册安全产品** | `wmic /namespace:\\root\SecurityCenter2 path AntiVirusProduct get *` | `Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct` | 普通用户 |
| 防火墙产品 | 同上，类改 `FirewallProduct` | 同上，`-ClassName FirewallProduct` | 普通用户 |
| **防火墙三配置文件状态** | `netsh advfirewall show allprofiles` | `Get-NetFirewallProfile` | 普通用户 |
| 防火墙规则 | `netsh advfirewall firewall show rule name=all` | `Get-NetFirewallRule` | 普通用户 |
| 查特定程序的规则 | — | 见 § 5.4 | 普通用户 |
| Defender 状态 | — | `Get-MpComputerStatus` | 普通用户 |
| **Defender 检测历史** | — | `Get-MpThreatDetection` | **管理员** |
| 已安装安全类服务 | `sc query type=service state=all` | `Get-Service` | 普通用户 |

⚠️ **`wmic` 在 Win11 与较新 Win10 上已弃用**（可能未安装）。PowerShell 的 `Get-CimInstance` 是替代路径，且 `dotnet-probing-techniques.md § 2.1` 警告的 **WMI 在故障机器上可能挂起**同样适用于这两条命令——须设超时：

```powershell
$job = Start-Job { Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct }
if (Wait-Job $job -Timeout 5) { Receive-Job $job } else { '未采集：WMI 查询超时'; Stop-Job $job }
Remove-Job $job -Force
```

### 5.2 已注册产品判读

`security-software.md § 1.1` 的判据，对应到 `productState` 字段：

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 查询返回空 | 无第三方 AV（可能仅系统自带） | 已确认**（有覆盖缺口，见下）** |
| 有条目，`displayName` 为产品名 | 该产品已注册 | 已确认 |
| `productState` 表明已过期/已禁用 | 可能仍驻留但不更新规则 | 推测 |

⚠️ **`security-software.md § 1.1` 的两个覆盖缺口在命令行侧无法弥补**：

| 缺口 | 后果 |
|---|---|
| 企业级 EDR **不一定注册**到安全中心 | 查询为空**不等于**没有安全软件 |
| 已卸载产品可能残留驱动或注册项 | 清单显示不准 |

**因此这条命令的空结果不构成排除依据**，必须结合 § 5.3 的模块交叉验证。

⚠️ `productState` 是位编码的 DWORD，各厂商填写不完全一致。**不要**试图精确解码其全部位含义——按 `rules/03` 的强度纪律，只取「已注册」这一确定事实，状态解读降为推测。

### 5.3 模块交叉验证：比清单更可靠

`security-software.md § 4.1` 指出这比安全中心清单更可靠——「清单可能漏掉 EDR，但注入的模块骗不了人」。

复用 § 3.2 的第三方子集，看其签名主体是否为安全厂商：

```powershell
# 承接 § 4.2 的批量验签输出，按签名主体归组
$third | Group-Object Signer | Sort-Object Count -Descending | Select-Object Count, Name
```

| 观察 | 判定 | 强度 |
|---|---|---|
| 安全中心有清单 + 模块列表有其组件 | 该产品正在干预本进程 | 已确认 |
| 安全中心无清单 + 模块列表有安全类组件 | **存在未注册的安全软件** | 推测 |
| 安全中心有清单 + 模块列表无其组件 | 该产品未注入本进程（但仍可能在内核层拦截） | 推测 |

⚠️ **第三行是本节新增的判读**，`security-software.md § 4.1` 只列了前两行。补充理由：安全软件的拦截可发生在内核（文件过滤驱动、WFP），此时**不注入用户态进程也能拦截**——因此"模块列表干净"不能排除安全软件干扰。这与 § 5.1 表中「Defender 不注入目标进程」的实际形态一致。

⚠️ **本领域不点名具体产品**（`README.md` 核心约束）。判断某签名主体是否为安全厂商，属使用方按 `module-injection.md § 6` 外置名单积累的内容，**不在本篇**。

### 5.4 防火墙：三配置文件必须分别看

`security-software.md § 1.2` 强调「只查一个配置文件是常见漏检」——用户切换网络会改变活动配置文件。

```powershell
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction
Get-NetConnectionProfile | Select-Object InterfaceAlias, NetworkCategory   # 当前活动的是哪个
```

**两条都要跑**——第一条给三个配置文件的状态，第二条给「当前生效的是哪一个」。只有二者结合才能判定。

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 当前活动配置文件 `Enabled=False` | 该配置下防火墙不拦截 | 已确认 |
| 当前活动配置文件 `Enabled=True` | 可能拦截，需看规则 | 已确认（开启）｜ 推测（是否拦截） |
| `DefaultOutboundAction=Block` | **出站默认阻断**，未显式放行的连接全部失败 | 已确认 |

⚠️ **`DefaultOutboundAction=Block` 值得单独关注**：Windows 默认出站是放行，改为阻断多为企业策略。此时宿主须有显式放行规则才能联网——这直接解释网络篇 § 8.3 的「慢失败（超时）」形态。

查宿主程序的放行规则：

```powershell
Get-NetFirewallApplicationFilter -Program "<exe完整路径>" -ErrorAction SilentlyContinue |
  Get-NetFirewallRule |
  Select-Object DisplayName, Direction, Action, Enabled, Profile
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 无任何规则且出站默认 Block | **该程序出站被阻断** | 已确认 |
| 存在 `Action=Block` 的规则 | **存在显式阻断规则** | 已确认 |
| 存在 `Action=Allow` 且 `Enabled=True` | 已放行（须核对 `Profile` 含当前活动配置文件） | 已确认 |

⚠️ **`Profile` 列必须核对。** 一条只在「专用」生效的放行规则，在公用网络下不起作用——这正是 § 5.4 开头「切换网络才出现故障」的机制。

### 5.5 拦截事件：能查到的极少数

`security-software.md § 3.1` 的表格里「某次连接失败是否被防火墙拦截」标为 ❌ 不能。**这在默认配置下成立**，但有两个例外可查：

**① Defender 的检测历史**（需管理员）：

```powershell
Get-MpThreatDetection | Select-Object InitialDetectionTime, ThreatID, Resources | Sort-Object InitialDetectionTime -Descending
Get-MpThreat | Select-Object ThreatName, SeverityID, IsActive
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 有涉及宿主文件路径的检测记录 | **文件被 Defender 处置过** | 已确认 |
| 无记录 | Defender 未处置（**不排除其他产品**） | 已确认（仅限 Defender） |

**② 防火墙审计日志**（须已启用，默认关闭）：

```powershell
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=5157} -MaxEvents 50 -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, Message
```

事件 ID `5157` 为「筛选平台阻止连接」，`5152` 为「筛选平台阻止数据包」。

⚠️ **默认不记录**——须已开启「筛选平台连接」审计策略。查不到事件**不等于**没有拦截，这是 `rules/02 § 4 缺失证据不等于反证` 的直接体现。

⚠️ **不得据此推广。** 这两个例外只覆盖 Windows 自带组件。第三方安全产品的拦截日志**仍然只在其自己的界面里**（`security-software.md § 3.2`），命令行无法获取——本节不改变 `security-software.md § 3.1` 的结论。

### 5.6 本节的边界

| 判不了 | 原因 |
|---|---|
| **第三方产品拦截了什么** | `security-software.md § 3.1` 的结构性限制，命令行不改变 |
| 哪条规则命中 | 规则逻辑在产品内部 |
| 文件是否被第三方产品隔离 | 需查各产品自己的隔离区 |
| 未注册到安全中心的产品 | § 5.2 的覆盖缺口；须靠 § 5.3 间接发现 |
| 规则库何时更新过 | 不对外暴露，但会改变行为（`security-software.md § 4.2`） |
| **WFP 过滤器枚举** | ⚠️ 无内置命令。`security-software.md § 1.3` 的这一检测面在命令行侧**不可得**——须按 `dotnet-probing-techniques.md § 3.2` 走 P/Invoke |

---

## 6. 系统环境劫持

对应 `system-environment-hijack.md` 的五个检测点。**本节是全篇最有价值的一节**，三个原因（该篇篇首）：取证成本极低（纯读注册表、无需枚举进程）、误判率极高（开发者会先查自己的代码，可能耗掉数天）、**判据确定性强（多数键值存在即可判定，可给「已确认」）**。

### 6.0 两条通用前提

⚠️ **① 双作用域必查。** `system-environment-hijack.md § 通用取证前提`：多数检测点在 `HKLM` 与 `HKCU` 都可能存在，**只查一处是本类检测最常见的漏检原因**。

⚠️ **② WOW64 重定向。** 32 位进程读 `HKLM\SOFTWARE` 会被重定向到 `Wow6432Node`。命令行侧的对应做法：

| 写法 | 效果 |
|---|---|
| `reg query "HKLM\SOFTWARE\..." /reg:64` | 强制 64 位视图 |
| `reg query "HKLM\SOFTWARE\..." /reg:32` | 强制 32 位视图（等价于读 `Wow6432Node`） |
| PowerShell `Get-ItemProperty 'HKLM:\SOFTWARE\...'` | 跟随当前 PowerShell 的位数 |

**`reg` 的 `/reg:64` 与 `/reg:32` 是命令行侧比 PowerShell 更方便的一处**——PowerShell 侧要显式指定视图须用 `OpenBaseKey`（见 `dotnet-probing-techniques.md § 4.1`）。**两个视图都要读**。

### 6.1 IFEO Debugger 劫持

对应 `system-environment-hijack.md § 1`。

```
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>" /v Debugger /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>" /v Debugger /reg:32
```

```powershell
'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>',
'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>' |
  ForEach-Object { Get-ItemProperty $_ -Name Debugger -ErrorAction SilentlyContinue }
```

**列出全部已配置 Debugger 的 exe**（不知道该查哪个名字时）：

```powershell
Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options' |
  ForEach-Object {
      $d = (Get-ItemProperty $_.PSPath -Name Debugger -ErrorAction SilentlyContinue).Debugger
      if ($d) { [PSCustomObject]@{ Exe = $_.PSChildName; Debugger = $d } }
  }
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 子键不存在 / 查询报错「找不到」 | 无 IFEO 劫持 | 已确认 |
| 子键存在但无 `Debugger` 值 | 无劫持（可能只配了 GlobalFlag，见 § 6.2） | 已确认 |
| `Debugger` 值存在且非空 | **启动被重定向** | 已确认 |

⚠️ **匹配的是 exe 文件名，不是完整路径**（`system-environment-hijack.md § 1`）——任何位置的同名 exe 都被劫持。

**必须再验证一步**：`Debugger` 指向的路径是否存在。

```powershell
Test-Path '<Debugger 值中的 exe 路径>'
```

| 结果 | 判定 |
|---|---|
| 路径不存在 | **目标程序完全无法启动**，且报错与真实原因无关 |
| 路径存在且为已知调试器（`vsjitdebugger.exe` / `windbg.exe`） | 可能是开发者主动配置，**不应判为故障** |
| 路径存在但为其他第三方程序 | 启动被中转——可能表现为启动慢、闪退、或启动了别的东西 |

⚠️ **不能仅凭键存在就判定为恶意**（`system-environment-hijack.md § 1 边界`）——合法用途包括调试器附加与部分安全软件的沙箱机制。

### 6.2 GlobalFlag 堆调试标志

对应 `system-environment-hijack.md § 2`。这一项解释「运行极慢但功能完全正常」这一极易误判的组合。

```
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager" /v GlobalFlag
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>" /v GlobalFlag /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>" /v PageHeapFlags /reg:64
```

**三处都要查**——`system-environment-hijack.md § 2` 指出 `gflags.exe -p` 设置的是 `PageHeapFlags` 这一独立位置。

判读堆调试位（值为 DWORD，须按位与）：

```powershell
$v = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' -Name GlobalFlag -ErrorAction SilentlyContinue).GlobalFlag
if ($null -eq $v) { '未设置' } else {
  $flags = [ordered]@{
    'hpa  页堆(极大影响)'   = 0x02000000
    'htc  堆尾校验'         = 0x00000010
    'hfc  释放校验'         = 0x00000020
    'hpc  参数校验'         = 0x00000040
    'ust  分配栈回溯'       = 0x00001000
  }
  $flags.GetEnumerator() | ForEach-Object {
      [PSCustomObject]@{ Flag = $_.Key; Set = [bool]($v -band $_.Value) }
  }
}
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 三处均不存在或为 0 | 无堆调试开启 | 已确认 |
| 任一处置有上表标志位 | **堆调试已开启，性能受影响** | 已确认 |

⚠️ **`GlobalFlag` 在 IFEO 下可能是 `REG_SZ` 而非 `REG_DWORD`**（`system-environment-hijack.md § 2` 取证位置已注明两种类型）。读到字符串时须先转数值再按位与，否则 `-band` 会静默给出错误结果。

### 6.3 AppCompatFlags 兼容模式

对应 `system-environment-hijack.md § 3`。⚠️ **值名是 exe 的完整路径**，不是文件名。

```
reg query "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
```

```powershell
'HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers',
'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers' |
  ForEach-Object {
      $k = $_
      if (Test-Path $k) {
          (Get-Item $k).Property | ForEach-Object {
              [PSCustomObject]@{ Scope = $k.Split(':')[0]; Exe = $_; Flags = (Get-ItemProperty $k -Name $_).$_ }
          }
      }
  } | Format-List
```

**HKCU 更常见**——普通用户即可设置（右键属性→兼容性）。

| 值内容含 | 对 WPF / 现代应用的影响 | 强度 |
|---|---|---|
| `DISABLEDWM` | **WPF 硬件渲染失效**，可能白屏或严重卡顿 | 已确认（标志生效） |
| `WIN7RTM` / `WINXPSP3` / `VISTARTM` | API 行为回退——DPI、渲染、字体异常 | 已确认 |
| `HIGHDPIAWARE` / `DPIUNAWARE` | 界面模糊或尺寸错乱 | 已确认 |
| `RUNASADMIN` | 权限异常、**拖放失效**（UIPI 隔离） | 已确认 |
| `DISABLETHEMES` | 控件外观异常 | 已确认 |
| 两处均无该 exe 路径的值 | 无兼容性标志 | 已确认 |

⚠️ **必须比对路径是否为当前实例**（`system-environment-hijack.md § 3 边界`）：程序移动位置后旧值失效但仍残留。用 `(Get-Process <名>).Path` 取实际路径比对。

⚠️ **与现象的因果仍是「推测」**——标志存在是已确认，标志导致了这个现象需移除后复现验证。

### 6.4 URL 协议注册

对应 `system-environment-hijack.md § 4`。

```
reg query "HKCU\SOFTWARE\Classes\<协议名>" /s
reg query "HKLM\SOFTWARE\Classes\<协议名>" /s
```

```powershell
'HKCU:\SOFTWARE\Classes\<协议名>','HKLM:\SOFTWARE\Classes\<协议名>' | ForEach-Object {
    if (Test-Path $_) {
        [PSCustomObject]@{
            Scope       = $_
            UrlProtocol = (Get-Item $_).Property -contains 'URL Protocol'
            Command     = (Get-ItemProperty "$_\shell\open\command" -Name '(default)' -ErrorAction SilentlyContinue).'(default)'
        }
    } else { [PSCustomObject]@{ Scope = $_; UrlProtocol = '键不存在'; Command = $null } }
}
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 两处协议键均不存在 | **未注册**，外部唤起无响应 | 已确认 |
| 键存在但 `UrlProtocol` 为 `False` | **注册不完整**，系统不识别为 URL 协议 | 已确认 |
| `Command` 为空或其路径不存在 | **注册损坏** | 已确认 |
| `Command` 指向的 exe 非目标程序 | **协议被抢占** | 已确认（指向他处）｜ 推测（是否恶意） |
| HKCU 与 HKLM 同时存在且指向不同 | **用户级覆盖系统级** | 已确认 |

⚠️ **`HKCU\SOFTWARE\Classes` 优先于 `HKLM\SOFTWARE\Classes`**——`system-environment-hijack.md § 4` 称「只查 HKLM 会漏掉用户级抢占，是本节最易漏检的形态」。**HKCU 必须先查。**

### 6.5 AppInit_DLLs 与 ShellExecute Hooks

对应 `system-environment-hijack.md § 5`。这两项与 § 3 的模块列表**可交叉验证**。

**AppInit_DLLs**：

```
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v AppInit_DLLs /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v LoadAppInit_DLLs /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v AppInit_DLLs /reg:32
```

⚠️ **判定顺序：必须先看 `LoadAppInit_DLLs`。** `system-environment-hijack.md § 5.1` 明确「只看 `AppInit_DLLs` 非空就报警会产生误报——残留配置在开关关闭时不生效」。

| 输出组合 | 判定 | 强度 |
|---|---|---|
| `LoadAppInit_DLLs` = 0 或不存在 | 机制未启用，内容不生效 | 已确认 |
| `LoadAppInit_DLLs` = 1 且 `AppInit_DLLs` 非空 | **列出的 DLL 注入所有 GUI 进程** | 已确认 |

⚠️ **Secure Boot 启用时该机制被系统禁用**，检出非空值也不生效。核对：

```powershell
Confirm-SecureBootUEFI   # 需 UEFI 环境，传统 BIOS 会报错
```

**ShellExecute Hooks**（两步，缺一不可）：

```powershell
Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ShellExecuteHooks' -ErrorAction SilentlyContinue |
  ForEach-Object {
      $clsid = $_.PSChildName
      $dll = (Get-ItemProperty "HKLM:\SOFTWARE\Classes\CLSID\$clsid\InprocServer32" -Name '(default)' -ErrorAction SilentlyContinue).'(default)'
      [PSCustomObject]@{ CLSID = $clsid; DLL = $dll }
  }
```

⚠️ **必须做 CLSID 反查这第二步**（`system-environment-hijack.md § 5.2 边界`）——只列 CLSID 无法判断。

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 无非系统 CLSID 条目 | 无第三方 shell hook | 已确认 |
| 存在第三方 CLSID 且反查到 DLL | **该 DLL 会加载进调用 ShellExecute 的进程** | 已确认（存在）｜ 推测（是否为主因） |

### 6.6 交叉验证：注册表侧 × 模块侧

`module-injection.md § 3.1` 指出三种手法（AppInit_DLLs、IFEO、ShellExecute Hooks）**两侧都有证据**，两侧都命中即强证据链。

| 情形 | 判读 | 强度 |
|---|---|---|
| **注册表有配置 + 模块列表有对应 DLL** | **强证据链** | 已确认（该 DLL 确经此机制进入） |
| 注册表有配置，模块列表无对应 DLL | 配置未生效（开关关闭、Secure Boot、加载失败） | 已确认 |
| 模块列表有可疑 DLL，注册表无配置 | 用了无静态痕迹的手法（`CreateRemoteThread` / `SetWindowsHookEx`） | 推测 |

**这是 § 3.5 能力缺口的主要补偿路径**——命令行拿不到"加载方式"，但注册表侧的痕迹能对三种全局注入手法给出等价强度的证据。

### 6.7 本节的边界

| 判不了 | 原因 |
|---|---|
| **配置是谁设置的** | 注册表不记录写入者（`system-environment-hijack.md § 6`） |
| 配置是否为现象主因 | 存在劫持 ≠ 导致此现象；须移除后复现验证 |
| 列出的 DLL / 程序是否有害 | 本领域不内置产品名单 |
| 企业 GPO 下发的合法配置 | 域环境中部分配置属预期行为，工具应提示而非判定为异常 |
| **兼容性 shim 数据库（`.sdb`）** | 需解析二进制，`system-environment-hijack.md § 3 边界`已声明不覆盖 |
| **默认应用关联的 `UserChoice`** | 带哈希保护，非协议注册检查所能覆盖 |

---

## 7. 硬件资源

对应 `hardware-thresholds.md`。⚠️ **两条前提先行：**

**① 本节不给任何阈值数值。** `hardware-thresholds.md § 1` 要求阈值必须是可配置参数、须记录定值依据与校准状态，且**该篇全部阈值当前状态均为 `待实测校准`**。本节给采集手段与判读方向，数值须查该篇并按 § 7 校准——这与网络篇 § 9.2 / § 10.3 的处理一致。

**② 必须多次采样。** `rules/02 § 2` 与 `hardware-thresholds.md § 2.1`：判据是「使用率 + 持续时长」，单点定值被明确禁止。本节各命令均已带采样参数，**不要**删减。

### 7.1 命令

| 目的 | cmd | PowerShell | 权限 |
|---|---|---|---|
| **CPU 采样** | `typeperf "\Processor(_Total)\% Processor Time" -si 1 -sc 30` | `Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 30` | 普通用户 |
| **进程级 CPU** | `typeperf "\Process(<名>)\% Processor Time" -si 1 -sc 30` | `Get-Counter '\Process(<名>)\% Processor Time' -SampleInterval 1 -MaxSamples 30` | 普通用户 |
| 内存总量与可用 | `systeminfo \| findstr /i "Memory"` | `Get-CimInstance Win32_OperatingSystem \| Select-Object TotalVisibleMemorySize, FreePhysicalMemory` | 普通用户 |
| **提交量与限制** | `typeperf "\Memory\Committed Bytes" "\Memory\Commit Limit" -sc 1` | `Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit'` | 普通用户 |
| 分页文件配置 | `wmic pagefileset list /format:list` | `Get-CimInstance Win32_PageFileSetting` | 普通用户 |
| 磁盘容量 | `wmic logicaldisk get caption,freespace,size` | `Get-PSDrive -PSProvider FileSystem` | 普通用户 |
| **磁盘介质类型（SSD/HDD）** | 无 | `Get-PhysicalDisk \| Select-Object FriendlyName, MediaType, HealthStatus` | 普通用户（Win8+） |
| 磁盘活动时间 | `typeperf "\PhysicalDisk(_Total)\% Disk Time" -si 1 -sc 30` | `Get-Counter '\PhysicalDisk(_Total)\% Disk Time' -SampleInterval 1 -MaxSamples 30` | 普通用户 |
| GPU 与驱动 | `wmic path Win32_VideoController get name,driverversion,driverdate` | `Get-CimInstance Win32_VideoController \| Select-Object Name, DriverVersion, DriverDate` | 普通用户 |
| CPU 型号 | `wmic cpu get name,numberofcores` | `Get-CimInstance Win32_Processor \| Select-Object Name, NumberOfCores, NumberOfLogicalProcessors` | 普通用户 |
| 电源策略 | `powercfg /getactivescheme` | 同左 | 普通用户 |

⚠️ **`typeperf` / `Get-Counter` 的计数器名受系统语言影响。** `dotnet-probing-techniques.md § 5.2` 警告「不要硬编中文名——硬编会让工具在英文系统上静默失效」。命令行侧同理，**反向也成立**：上表的英文计数器名在中文系统上可能不匹配。

**排障**：先列出本机实际的类别名：

```powershell
Get-Counter -ListSet * | Select-Object -ExpandProperty CounterSetName | Sort-Object
```

### 7.2 CPU：必须同时采系统级与进程级

`dotnet-probing-techniques.md § 5.4` 明确「只采一层无法完成分流——分不清『机器慢』和『这个程序慢』」。

```powershell
Get-Counter -Counter @(
    '\Processor(_Total)\% Processor Time',
    "\Process(<进程名>)\% Processor Time"
) -SampleInterval 1 -MaxSamples 30 |
  ForEach-Object { $_.CounterSamples | Select-Object Path, CookedValue } 
```

⚠️ **进程级计数器须按核心数归一化。** `hardware-thresholds.md § 2.2`：`\Process(*)\% Processor Time` 的口径是**「单核 100% 为满」**——32 核机器上显示 100% 只是一个核心跑满（约总量 3%）。

```powershell
$cores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
# 归一化：进程读数 / 逻辑核心数 = 占全机比例
```

**因果方向判读**（`hardware-thresholds.md § 2.3`，本节最重要的判据）：

| 观察 | 更可能的因果 | 转向 |
|---|---|---|
| 目标进程 CPU **单核跑满** + 无响应 | **进程内部**死循环 | `dotnet-debugging` |
| 系统整体 CPU 高 + 目标进程占比低 | 外部进程抢占 | 本篇（找抢占者，见下） |
| CPU 不高但无响应 | **不是 CPU 问题** | 死锁 / 阻塞排查 |

找抢占者：

```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, Id, CPU, WorkingSet64
```

⚠️ **`Get-Process` 的 `CPU` 属性是进程启动至今的累计 CPU 秒数，不是当前使用率。** 长期运行的进程累计值必然大——**不能**据此判断"谁在占用 CPU"。要看当前使用率须用 `Get-Counter` 的进程级计数器，或对 `CPU` 属性做两次采样求差：

```powershell
$a = Get-Process | Select-Object Id, Name, CPU
Start-Sleep -Seconds 5
$b = Get-Process | Select-Object Id, Name, CPU
$b | ForEach-Object {
    $prev = $a | Where-Object Id -eq $_.Id
    if ($prev) { [PSCustomObject]@{ Name = $_.Name; Id = $_.Id; DeltaCpuSec = [math]::Round($_.CPU - $prev.CPU, 2) } }
} | Sort-Object DeltaCpuSec -Descending | Select-Object -First 10
```

⚠️ **这是本节最容易出错的一处。** 直接 `Sort-Object CPU` 得到的排行榜几乎总是把开机就启动的系统进程排在前面，与"当前谁在占 CPU"无关。

### 7.3 内存：三个指标不可混用

`hardware-thresholds.md § 3.1` 要求区分三个指标，它们回答不同问题：

```powershell
$os = Get-CimInstance Win32_OperatingSystem
$c  = Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit'
[PSCustomObject]@{
    '物理总量GB'   = [math]::Round($os.TotalVisibleMemorySize/1MB, 2)
    '物理可用GB'   = [math]::Round($os.FreePhysicalMemory/1MB, 2)
    '提交量GB'     = [math]::Round(($c.CounterSamples | Where-Object Path -like '*committed bytes').CookedValue/1GB, 2)
    '提交限制GB'   = [math]::Round(($c.CounterSamples | Where-Object Path -like '*commit limit').CookedValue/1GB, 2)
}
```

⚠️ **提交量耗尽比物理内存耗尽更严重**（`hardware-thresholds.md § 3.1`）——前者导致**分配失败（崩溃）**，后者只是换页变慢。

| 排查目标 | 该看哪个指标 |
|---|---|
| 「内存不足导致**崩溃**」 | **提交量 / 提交限制** |
| 「内存不足导致**变慢**」 | 物理可用量 |
| 「这个程序占多少」 | 进程工作集（`(Get-Process <名>).WorkingSet64`） |

**分页文件配置**（影响提交限制上限）：

```powershell
Get-CimInstance Win32_PageFileSetting | Select-Object Name, InitialSize, MaximumSize
Get-CimInstance Win32_ComputerSystem | Select-Object AutomaticManagedPagefile
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 查询返回空且 `AutomaticManagedPagefile=False` | **分页文件已禁用**，提交限制受限于物理内存 | 已确认 |
| `InitialSize` / `MaximumSize` 固定且较小 | 提交限制无法动态扩展 | 已确认 |

⚠️ **与托管内存的边界**（`hardware-thresholds.md § 3.3`）：本节只判**系统级**内存压力。单一进程内存**单调增长**属进程内部问题——转 `dotnet-debugging`。区分点：系统整体紧张（多进程共同导致）→ 本节；单进程单调增长 → 进程内部。

### 7.4 磁盘：先定介质类型再判阈值

⚠️ **`hardware-thresholds.md § 4.3`：判定阈值前必须先确定介质类型，否则 HDD 机器会持续产生误报。**

```powershell
Get-PhysicalDisk | Select-Object DeviceId, FriendlyName, MediaType, Size, HealthStatus
Get-Partition | Select-Object DriveLetter, DiskNumber, Size   # 映射盘符到物理盘
```

| `MediaType` | 判读 |
|---|---|
| `SSD` | 响应时间高属**异常信号**——可能是驱动、固件或健康度问题 |
| `HDD` | 启动慢、加载慢属**预期**，阈值应放宽 |
| `Unspecified` | 虚拟磁盘或驱动未报告；无法据此调整阈值，须降低结论强度 |

容量：

```powershell
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{n='FreeGB';e={[math]::Round($_.Free/1GB,2)}}, @{n='TotalGB';e={[math]::Round(($_.Used+$_.Free)/1GB,2)}}
```

⚠️ **系统盘须用更保守的阈值**（`hardware-thresholds.md § 4.2`）：系统盘空间不足会导致分页文件无法扩展、临时文件写入失败、更新失败——影响远超数据盘。

⚠️ **磁盘压力的因果方向与 CPU 同理**（`hardware-thresholds.md § 4.4`）：磁盘饱和可能是**其他进程**导致的，目标进程只是受害者。须看是谁在读写：

```powershell
Get-Counter '\Process(*)\IO Data Bytes/sec' -MaxSamples 1 |
  ForEach-Object { $_.CounterSamples } |
  Where-Object { $_.CookedValue -gt 0 -and $_.InstanceName -notin '_total','idle' } |
  Sort-Object CookedValue -Descending | Select-Object -First 10 InstanceName, CookedValue
```

### 7.5 GPU 与渲染：硬件加速状态比使用率重要

`hardware-thresholds.md § 5.1`：对 WPF 宿主，**渲染层级比 GPU 使用率更重要**，「软件渲染回退是 WPF 卡顿的高频成因，且容易被误判为程序性能问题」。

⚠️ **渲染层级（`RenderCapability.Tier`）是进程内的 WPF API，命令行拿不到。** 命令行侧只能采集其**成因**：

```powershell
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, DriverDate, VideoProcessor, AdapterRAM, Status
```

按 `hardware-thresholds.md § 5.2` 的五个回退原因，命令行可查其中四个：

| 回退原因 | 命令行判据 |
|---|---|
| 驱动过旧或不支持 | 上述 `DriverVersion` / `DriverDate` |
| 远程桌面 / VDI 会话 | `qwinsta` 或 `$env:SESSIONNAME`（`RDP-Tcp#N` 即远程会话） |
| **注册表或组策略禁用** | § 6.3 的 `DISABLEDWM` 标志 |
| 第三方软件干扰渲染链 | § 3 的模块列表（`module-injection.md § 4.1`） |
| 虚拟机无 GPU 直通 | `Get-CimInstance Win32_ComputerSystem \| Select-Object Manufacturer, Model` |

检测远程会话：

```powershell
[PSCustomObject]@{
  SessionName = $env:SESSIONNAME                      # RDP-Tcp#N = 远程会话
  IsRemote    = $env:SESSIONNAME -like 'RDP*'
}
```

⚠️ **`hardware-thresholds.md § 5.3`：GPU 使用率的采集在不同显卡与驱动上差异较大，多适配器（集显+独显）环境下需明确采哪一个，可靠性低于 CPU/内存指标，判定时权重应相应降低。** 命令行侧同样受此限制。

### 7.6 CPU 指令集兼容性

`hardware-thresholds.md § 6` 单列此项，因为它有三个难排查特征：确定性失败（易误判为程序 bug）、错误信息无关、换机器就好。

```powershell
Get-CimInstance Win32_Processor | Select-Object Name, Description, Caption, NumberOfCores
```

⚠️ **命令行无法直接枚举 CPU 支持的指令集。** `wmic` / `Get-CimInstance` 只给型号名与家族，不给 AVX/AVX2/SSE4 等特性位。判定路径有二：

| 路径 | 说明 |
|---|---|
| 按型号查厂商规格 | 从 `Name` 取型号，查厂商公开规格表——**离线不可行**，且属外部信息 |
| 完整实现 | `System.Runtime.Intrinsics.X86.*.IsSupported`（.NET 8+），见 `dotnet-probing-techniques.md § 1` |

**命令行侧能给的**：型号与核心数这一事实。**判不了**：是否支持某指令集。老旧机器或虚拟机（可能屏蔽部分指令集）上出现"这台机器就是打不开"时，须走完整实现路径。

### 7.7 电源策略：容易被忽略的降频源

`dotnet-probing-techniques.md § 7` 把 `powercfg` 列为系统内置工具，用于「电源策略（影响 CPU 降频）」。

```
powercfg /getactivescheme
powercfg /list
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 活动方案为「节能」/ `Power saver` | **CPU 可能被限频**，表现为整体变慢 | 已确认（配置）｜ 推测（是否为主因） |
| 活动方案为「平衡」/「高性能」 | 无策略性降频 | 已确认 |

⚠️ **笔记本电池模式下策略会自动切换**——采集时须记录当时是否接电源，否则结论不可复现（`rules/02 § 4`）。

### 7.8 本节的边界

| 判不了 | 原因 |
|---|---|
| **阈值是否适合本环境** | 未校准前只是建议值（`hardware-thresholds.md § 1`）；本节有意不给数值 |
| **因果方向** | CPU / 磁盘高可能是结果而非原因（§ 7.2、§ 7.4） |
| **WPF 渲染层级** | 进程内 API，命令行不可得；只能采集回退成因（§ 7.5） |
| **CPU 指令集支持** | 无内置命令枚举特性位（§ 7.6） |
| 托管堆内部的内存问题 | 属进程内部，转 `dotnet-debugging` |
| GPU 指标的跨设备可比性 | 采集实现差异大，可靠性低于 CPU/内存 |
| **间歇性资源峰值** | 采样窗口外的峰值不可见；须延长 `-MaxSamples` |

---

## 8. 现象直达速查

接 `symptom-routing.md` 的现象分流结果，给出第一条命令。⚠️ **`system-environment-hijack.md` 篇首要求这五项排在最前**——取证成本极低而误判率极高，故下表凡涉及启动/性能异常者均先查 § 6。

| 用户描述 | 起查节 | 第一条命令 |
|---|---|---|
| 双击无反应 / 闪退 / 报错与代码无关 | § 6.1 | `reg query "HKLM\...\Image File Execution Options\<exe>" /v Debugger /reg:64` |
| **运行极慢但功能完全正常** | § 6.2 | `reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager" /v GlobalFlag` |
| 白屏 / 界面模糊 / 尺寸错乱 / 拖放失效 | § 6.3 | `reg query "HKCU\SOFTWARE\...\AppCompatFlags\Layers"` |
| 点击外部链接无法唤起 / 唤起错误程序 | § 6.4 | `reg query "HKCU\SOFTWARE\Classes\<协议>" /s` |
| **白屏 / 卡顿 / 崩溃**（环境劫持已排除） | § 3 | `Get-Process <名> \| Select -Expand Modules` |
| 特定操作必然失败、重装无效、其他机器正常 | § 5 | `Get-NetFirewallProfile` + § 5.2 安全产品清单 |
| 自动更新失败 | § 5 | 同上（`security-software.md § 2.2`：优先级高于网络排查） |
| 整机卡顿 / CPU 高 | § 7.2 | `Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 30` |
| 内存不足导致**崩溃** | § 7.3 | `Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit'` |
| 这台机器就是打不开（换机器就好） | § 7.6 | `Get-CimInstance Win32_Processor \| Select Name` |

### 8.1 最小取证集

`system-environment-hijack.md` 的五项**成本极低且确定性强**，作为任何排查的第一步：

```
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>" /s /reg:64
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager" /v GlobalFlag
reg query "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows" /v LoadAppInit_DLLs /reg:64
```

⚠️ **这四条只覆盖 § 6，不覆盖 § 3 / § 5 / § 7。** 与网络篇 § 11.1 同一告诫：**筛查无果不构成「环境正常」的结论**（`rules/02 § 3`）。

---

## 9. 本篇覆盖边界

### 9.1 本篇能给的

| 能给 | 强度 |
|---|---|
| 五个环境劫持检测点的存在性与配置内容（§ 6） | **已确认**——本篇最强产出 |
| 注册表侧 × 模块侧的交叉验证证据链（§ 6.6） | 已确认 |
| 进程已加载模块的清单、路径、签名状态（§ 3、§ 4） | 已确认（须区分 `NotSigned` 与 `UnknownError`） |
| DLL 搜索顺序劫持（§ 4.4） | 已确认 |
| 已注册安全产品与防火墙三配置文件状态（§ 5） | 已确认（有覆盖缺口） |
| 各项资源的测量值与采样序列（§ 7） | 已确认（测量事实） |
| 上述任一项是否为现象**主因** | **推测**——见 § 1 强度基线 |

### 9.2 命令行侧的四处能力缺口

**这是本篇与网络篇最大的不同**——网络层几乎全部检测面都有内置命令，本篇则有四项确实不可得：

| 缺口 | 影响 | 完整实现路径 |
|---|---|---|
| **模块加载方式**（静态导入 vs 运行时注入） | `module-injection.md § 2.2` 权重**最高**的维度不可得；§ 6.6 交叉验证为主要补偿 | 解析 PE 导入表 |
| **WFP 过滤器枚举** | `security-software.md § 1.3` 的一整个检测面不可得 | `dotnet-probing-techniques.md § 3.2`（P/Invoke，需管理员） |
| **WPF 渲染层级** | `hardware-thresholds.md § 5.1` 称其比 GPU 使用率更重要；只能采回退成因（§ 7.5） | 进程内 `RenderCapability.Tier` |
| **CPU 指令集特性位** | `hardware-thresholds.md § 6` 的判据不可直接执行 | `System.Runtime.Intrinsics.X86.*.IsSupported` |

⚠️ **不得因为命令行拿不到就把这四项当作「已排除」**——这正是 `rules/02 § 3` 禁止的「把『没查到』呈现为『没问题』」。**必须显式记录为「因手段限制未采集」。**

### 9.3 本篇的固有局限

⚠️ **① 权限不足时多数命令静默返回不完整结果**（§ 2.2）——这比报错危险，须显式核对是否以管理员运行。

⚠️ **② 计数器名与注册表值在中文系统上本地化。** `typeperf` 的英文计数器名在中文系统可能不匹配（§ 7.1）；`reg query` 的输出字段名同理。**批量脚本应取 PowerShell 对象属性，不匹配输出文本**——与网络篇 § 12.3 同一条。

⚠️ **③ `wmic` 已弃用。** Win11 与较新 Win10 可能未安装，本篇 `wmic` 行均给了 `Get-CimInstance` 替代。

⚠️ **④ WMI 在故障机器上可能挂起。** `dotnet-probing-techniques.md § 2.1`：WMI 仓库损坏或被安全软件拦截时**不抛异常也不返回**。§ 5.1 给了超时包装写法，§ 7 的 `Get-CimInstance` 同样适用。

⚠️ **⑤ 模块与资源采集只反映执行瞬间**（§ 2.1）——动态加载与间歇性峰值在窗口外不可见。

### 9.4 与其他篇的交接

| 情形 | 转向 |
|---|---|
| 需要判据、阈值数值与结论措辞 | 对应的 `module-injection.md` / `security-software.md` / `hardware-thresholds.md` / `system-environment-hijack.md` |
| 网络类现象 | `cli-probe-toolbox.md`（网络层命令）+ `network-layered-probe.md`（判据） |
| 确认故障在进程内部（托管堆增长、单核跑满无响应） | `symptom-routing.md § 6.1` → `dotnet-debugging` |
| 四处缺口需要完整实现 | `dotnet-probing-techniques.md` |
| 四类全部排除但现象仍在 | `symptom-routing.md` 的下一优先级 |

---
