# 网络层命令行取证手册

> `network-layered-probe.md` 回答**判什么、凭什么判**，本篇回答**敲什么命令、看输出的哪个字段**。两者一一对应：本篇的节号与该篇的层号对齐（本篇 § 3 ↔ 该篇第 1 层，依此类推）。
>
> 本篇是 `rules/02-evidence-standards.md § 1 原始输出优先` 的落地路径。该节要求证据形态为「具体域名、错误码、解析结果、耗时」——这四项正是本篇各命令的输出字段。

⚠️ **本篇服务两类读者，用途不同：**

| 读者 | 怎么用 |
|---|---|
| **支持 / 运维人员** | 直接照着敲，按判读列得出结论 |
| **诊断工具开发者** | 作为「该采集哪个字段」的规格说明；实现路径查 `dotnet-probing-techniques.md` |

## 1. 本篇的取舍：为什么收录命令行工具

`dotnet-probing-techniques.md § 4` 的立场是「托管 API 覆盖完整的项不要 P/Invoke」，并以 `NetworkInterface` 覆盖 `ipconfig /all` 为例。**该立场只对「正在写诊断 exe」成立**，本篇覆盖它不管的场景：

| 场景 | 为什么命令行是唯一可行路径 |
|---|---|
| 诊断工具还没做出来 | 本领域的配套工具形态未定（见 `README.md § 配套 skill 评估`），此期间排查只能靠命令行 |
| 诊断工具装不上或跑不起来 | 正是 `dotnet-probing-techniques.md § 8` 警告的情形——网络不通的机器下载不了运行时 |
| 需要现场交互式验证 | 排查是循环过程，改一项试一次；重编译工具不现实 |
| 需要用户自己配合取证 | 让用户敲一条命令截图，成本远低于让其安装未签名 exe |

### 1.1 选型口径

本篇命令**全部为 Windows 内置、零安装**，与 `dotnet-probing-techniques.md § 7.1`「免分发是决定性的」同一原则。

每项给 **cmd 工具**与 **PowerShell cmdlet** 两种写法：

| 写法 | 何时用 |
|---|---|
| cmd 工具（`ping`、`nslookup`…） | 全版本可用；让用户复制粘贴时更稳（无执行策略限制） |
| PowerShell cmdlet（`Test-Connection`、`Resolve-DnsName`…） | 输出为**对象**，可直接筛选字段、可脚本化批量探测；部分能力 cmd 侧没有 |

⚠️ **两者不是等价替换。** cmdlet 的可用性受 Windows 版本与模块约束，差异在各节的「可用性」列如实标注。选 cmd 还是 cmdlet 取决于**目标机器版本**与**是否需要批量**，不是风格偏好。

### 1.2 未收录的工具及理由

| 未收录 | 理由 |
|---|---|
| `psping`（Sysinternals） | 需下载。TCP 探测能力由 `Test-NetConnection` 覆盖（见 § 9.1），不值得引入分发成本 |
| `mtr` / `tcping` 等第三方 | 非内置，且触发安全软件告警的风险与 `dotnet-probing-techniques.md § 7.1` 的顾虑相同 |
| Wireshark 等抓包工具 | 需安装且需驱动；抓包判读属独立技能，超出本领域「按判据表定位到层」的目标 |
| `netsh trace`（抓包功能） | 内置但产出 `.etl` 需离线解析，属 `dotnet-probing-techniques.md § 6` 的 ETW 范畴，不在本篇 |

## 2. 三条执行纪律

在敲任何命令前，以下三条**必须**先成立。它们是 `rules/` 的直接落地，违反会使取得的输出不可用。

### 2.1 必须记录完整原始输出，不得转述

**必须**保留命令的完整输出（含命令行本身与执行时刻），不得只记结论。

**理由**：`rules/02 § 1`。「ping 不通」这一转述丢失了关键区分——是解析失败、是超时、还是 TTL 耗尽？三者指向完全不同的层。

### 2.2 波动型指标必须多次采样

`ping`、测速类命令的单次结果**禁止**直接定值，须按 `rules/02 § 2` 采样并记录次数与间隔。

各节已在命令中带上相应参数（如 `ping -n 20`），**不要**删减为默认值。

### 2.3 只读，不改配置

本篇全部命令为**只读**。`rules/01-diagnostic-safety.md § 1 只读优先` 要求诊断阶段不修改系统状态。

⚠️ 以下命令**属于修改操作，不在本篇**，即便它们常与排查一同出现：

| 修改类命令 | 为什么不在诊断阶段 |
|---|---|
| `ipconfig /flushdns` | 清空 DNS 缓存会**销毁证据**——缓存内容本身是判据（见 § 4.3） |
| `netsh winsock reset` | 重置 LSP 链需重启，且会掩盖 `network-layered-probe.md § 6` 要判的损坏 LSP |
| `netsh int ip reset` | 同上，且影响面更大 |
| `arp -d` | 清 ARP 缓存同样销毁证据 |

**这些命令可能是最终的修复动作，但必须在证据采集完成、结论成立之后，并按 `rules/01 § 2` 确认与记录回滚路径。**

---

## 3. 第 1 层：本机 IP 与网卡状态

对应 `network-layered-probe.md § 2`。

### 3.1 命令

| 目的 | cmd | PowerShell | 可用性 |
|---|---|---|---|
| 全部网卡与 IP 配置 | `ipconfig /all` | `Get-NetIPConfiguration -Detailed` | cmdlet 需 Win8/2012+ |
| 网卡链路状态 | `netsh interface show interface` | `Get-NetAdapter` | 同上 |
| **路由表** | `route print` | `Get-NetRoute` | 同上 |
| 链路速率与丢弃计数 | 无直接等价 | `Get-NetAdapterStatistics` | 同上 |

⚠️ **`route print` 不可省。** `network-layered-probe.md § 2` 明确要求「判定路由走向须看路由表，不能只看网卡列表」——多网卡环境下网卡列表看不出流量走哪个出口。

### 3.2 判读

按 `ipconfig /all` 的输出字段：

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 无任一网卡处于 `Media State: Connected` | 无网络连接 | 已确认 |
| `IPv4 Address` 为 `169.254.x.x` | **DHCP 获取失败**（APIPA 自动地址） | 已确认 |
| 有 IP 但 `Default Gateway` 为空 | 仅限本地网络，无法访问外部 | 已确认 |
| `DNS Servers` 为空 | 域名解析必然失败，直接进 § 4 | 已确认 |
| 多个网卡同时有 IP 与网关 | 出口可能非预期，**须看路由表判定** | 需进一步取证 |

按 `route print` 的输出字段：

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 存在多条 `0.0.0.0/0` 默认路由 | 出口由 `Metric` 最小者决定；须核对是否为预期网卡 | 已确认（配置事实） |
| 默认路由指向 VPN 虚拟网卡 | 全部流量走 VPN | 已确认 |
| 目标服务网段有更具体的路由条目 | **该服务流量走特殊出口**，与默认路由不同 | 已确认 |

### 3.3 VPN 残留：本层最高频的误判源

`network-layered-probe.md § 2` 指出「VPN 客户端常改写路由表与 DNS，断开后可能残留」。取证方式：

```
route print
ipconfig /all
```

**判据**：VPN 客户端已退出（进程不在），但路由表仍有指向其虚拟网卡的条目，或 `ipconfig /all` 中 VPN 网卡的 DNS 仍在生效。

⚠️ **须区分两种形态**，处置方向不同：

| 形态 | 表现 | 后果 |
|---|---|---|
| 路由残留 | 路由条目指向已不存在的接口 | 流量黑洞——发出即丢，表现为**超时** |
| DNS 残留 | 仍向 VPN 内网 DNS 查询 | 解析失败或返回内网地址，表现为 § 4 的现象 |

### 3.4 本层的边界

| 判不了 | 原因 |
|---|---|
| 网关本身是否正常 | 网关配置存在 ≠ 网关可达；须到 § 8 探测验证 |
| 路由条目由谁写入 | 同 `system-environment-hijack.md § 6`——从配置内容无法判断写入者 |
| 无线信号质量 | `Get-NetAdapter` 只给链路速率，不给信号强度与重传率 |

---

## 4. 第 2 层：DNS 配置与解析

对应 `network-layered-probe.md § 3`。

### 4.1 命令

| 目的 | cmd | PowerShell | 可用性 |
|---|---|---|---|
| 解析指定域名 | `nslookup <域名>` | `Resolve-DnsName <域名>` | cmdlet 需 Win8/2012+ |
| **指定 DNS 服务器解析**（对照） | `nslookup <域名> 8.8.8.8` | `Resolve-DnsName <域名> -Server 8.8.8.8` | 同上 |
| 绕过本机缓存解析 | 无（`nslookup` 本身不走缓存） | `Resolve-DnsName <域名> -DnsOnly -NoHostsFile` | 同上 |
| **查看本机 DNS 缓存** | `ipconfig /displaydns` | `Get-DnsClientCache` | 同上 |
| 当前 DNS 服务器 | `ipconfig /all` | `Get-DnsClientServerAddress` | 同上 |

### 4.2 `nslookup` 的两个易错点

⚠️ **① `nslookup` 不走本机 DNS 缓存与 hosts 文件。** 它直接向 DNS 服务器查询。

这意味着：**`nslookup` 解析正常，但应用仍解析失败，是完全可能的**——差异恰好来自缓存或 hosts。此时应改用：

```powershell
Resolve-DnsName <域名>              # 走完整解析链（含 hosts 与缓存）
Resolve-DnsName <域名> -DnsOnly     # 仅 DNS，用于对比
```

两者结果不同即定位到缓存或 hosts 层，转 § 4.3 与 § 5。

⚠️ **② `nslookup` 开头的 "Non-authoritative answer" 与 `*** can't find` 语义**：

| 输出 | 含义 | 不是什么 |
|---|---|---|
| `Non-authoritative answer` | 来自缓存或递归服务器的正常应答 | **不是错误**，这是绝大多数查询的正常形态 |
| `*** <server> can't find <域名>: Non-existent domain` | NXDOMAIN——DNS 明确答"无此域名" | 不代表网络不通 |
| `*** Request to <server> timed-out` | **DNS 服务器本身不可达** | 不代表该域名不存在 |
| `DNS request timed out` 后仍给出结果 | 首个 DNS 服务器超时，由备用服务器应答 | 须记录：主 DNS 已异常 |

**最后一行常被忽略**——它是 DNS 服务器部分失效的证据，但因为最终拿到了结果，容易被判为"正常"。

### 4.3 DNS 缓存是判据，不是障碍

`network-layered-probe.md § 3` 指出缓存可能持有过期记录。取证：

```
ipconfig /displaydns | findstr /i "<域名>"
```

```powershell
Get-DnsClientCache | Where-Object Entry -like "*<域名>*"
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 缓存中该域名的 `Data` 与实时解析结果不同 | **缓存持有过期记录**，应用可能仍用旧值 | 已确认 |
| 缓存中该域名指向 `127.0.0.1` / `0.0.0.0` | 来源可能是 hosts（hosts 条目会进缓存），转 § 5 | 已确认 |
| 缓存中 `Status` 为负缓存（无 `Data`） | **失败结果被缓存**，短期内重试仍失败 | 已确认 |

⚠️ 第三行值得注意：**负缓存会让「问题其实已修复」表现为「仍然故障」**。判定时须考虑，但清缓存属修改操作（见 § 2.3），须在采集后进行。

### 4.4 对照解析：区分污染与 CDN 差异

`network-layered-probe.md § 3` 的判据「解析结果与对照环境显著不同」需要对照数据。用指定 DNS 服务器构造对照：

```powershell
Resolve-DnsName <域名>                      # 本机 DNS
Resolve-DnsName <域名> -Server 8.8.8.8      # 公共 DNS 对照
Resolve-DnsName <域名> -Server 223.5.5.5    # 第二个对照（境内）
```

| 结果关系 | 判定 | 强度 |
|---|---|---|
| 三者一致 | 解析层无干预 | 已确认 |
| 本机与两个对照均不同，但两对照互相一致 | **本机 DNS 返回了异常结果** | 推测（仍可能是内部策略） |
| 本机指向内网/回环，对照指向公网 | 内部 DNS 策略或劫持 | 已确认（结果差异）｜ 推测（成因） |
| 三者互不相同但均为公网地址 | **很可能是 CDN 地理调度，非污染** | 推测 |

⚠️ **这里必须复述 `network-layered-probe.md § 3` 的警告：解析结果不同 ≠ 被污染。** 上表第四行是 CDN 的正常行为。判定污染需要「指向明显无关的地址」这类更强证据，本篇的对照法**不足以单独定性污染**。

⚠️ **企业环境下对照法可能不成立**：内部域名在公共 DNS 上本就无记录，`8.8.8.8` 返回 NXDOMAIN 是预期结果，不构成异常证据。

### 4.5 本层的边界

| 判不了 | 原因 |
|---|---|
| 解析结果是否被污染 | 同上，与 CDN 差异难以静态区分（`network-layered-probe.md § 11`） |
| DNS 服务器为何返回该结果 | 服务器侧策略对客户端不可见 |
| 解析成功后能否连接 | 解析与连接是两层，须到 § 8 |

---

## 5. 第 3 层：hosts 文件

对应 `network-layered-probe.md § 4`。该层是全篇少数能给「已确认」的层——文件内容明文且语义明确。

### 5.1 命令

| 目的 | cmd | PowerShell |
|---|---|---|
| 读取全文 | `type %SystemRoot%\System32\drivers\etc\hosts` | `Get-Content $env:SystemRoot\System32\drivers\etc\hosts` |
| 过滤非注释行 | `findstr /v "^#" %SystemRoot%\System32\drivers\etc\hosts` | `Get-Content ... \| Where-Object { $_ -notmatch '^\s*#' -and $_.Trim() }` |
| 查特定域名 | `findstr /i "<域名>" %SystemRoot%\System32\drivers\etc\hosts` | `Select-String -Path ... -Pattern '<域名>'` |
| **最后修改时间** | `dir %SystemRoot%\System32\drivers\etc\hosts` | `(Get-Item ...).LastWriteTime` |

⚠️ **必须读全文，不能只 `findstr` 目标域名。** 两个原因：

1. 通配形态的条目（如注掉整段又漏掉一行）需看上下文才能判断生效范围
2. 文件末尾无换行、或含大量空行填充的条目，是"藏"条目的常见手法

### 5.2 判读

沿用 `network-layered-probe.md § 4` 的判据，补充输出层面的细节：

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 无宿主服务域名 | hosts 未干预 | 已确认 |
| 域名指向 `127.0.0.1` 或 `0.0.0.0` | **域名被本地屏蔽** | 已确认 |
| 域名指向其他 IP | **解析被重定向** | 已确认 |
| 文件不存在或为空 | hosts 未干预（系统会正常工作） | 已确认 |
| `LastWriteTime` 与故障起始时间接近 | 时间相关性——**不是因果**（`rules/03 § 2`） | 推测 |

### 5.3 两个易被忽略的形态

⚠️ **① `hosts` 之外还有 `hosts.ics`。** 同目录下的 `hosts.ics` 由「Internet 连接共享」生成，也参与解析。排查时应一并查看：

```
dir %SystemRoot%\System32\drivers\etc\
```

⚠️ **② 文件可能被安全软件保护为只读或重定向。** 表现为读到的内容与实际生效内容不一致。若 hosts 显示无条目但 § 4.3 的缓存中出现回环地址，二者矛盾即指向此形态——转 `security-software.md`。

### 5.4 本层的边界

| 判不了 | 原因 |
|---|---|
| **条目由谁写入** | `network-layered-probe.md § 4` 已明确：开发遗留、企业策略、第三方工具、恶意软件从内容无法区分 |
| 修改时间是否可信 | 文件时间戳可被改写，不能作为强证据 |

---

## 6. 第 4 层：代理配置

对应 `network-layered-probe.md § 5`。该层是「部分功能不可用」的头号成因。

### 6.1 命令：三层代理必须分别取证

`dotnet-probing-techniques.md § 3.4` 指出代理分三层且可互不一致。命令按层对应：

| 层 | 作用范围 | cmd | PowerShell |
|---|---|---|---|
| **WinHTTP 机器级** | 服务、部分系统组件 | `netsh winhttp show proxy` | 同左（无 cmdlet） |
| **WinINET 用户级** | 使用系统设置的应用（含多数桌面应用） | `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"` | `Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'` |
| 环境变量级 | 遵循 `HTTP_PROXY` 约定的程序（含 `curl`） | `set http_proxy` | `$env:HTTP_PROXY` |

⚠️ **`netsh winhttp show proxy` 返回「直接访问(没有代理服务器)」不等于无代理。** 它只反映机器级 WinHTTP，用户级 WinINET 代理仍可能生效——这正是 `dotnet-probing-techniques.md § 3.4` 警告的分层混淆。**三条命令必须全跑。**

### 6.2 WinINET 关键值判读

`reg query` 输出中需关注的值名：

| 值名 | 含义 | 判读 |
|---|---|---|
| `ProxyEnable` | `0x1` 启用手动代理，`0x0` 未启用 | 为 1 则 `ProxyServer` 生效 |
| `ProxyServer` | 代理地址，可按协议分别指定 | 记录原文；须验证该地址可达（见 § 6.3） |
| `ProxyOverride` | 绕过代理的例外列表 | **宿主域名在此列表内 = 该域名直连** |
| `AutoConfigURL` | PAC 脚本 URL | 存在则**规则由脚本决定**，见 § 6.4 |

| 组合 | 判定 | 强度 |
|---|---|---|
| `ProxyEnable=0` 且无 `AutoConfigURL` | 直连 | 已确认 |
| `ProxyEnable=1` 且代理不可达 | **全部经代理的流量失败** | 已确认 |
| `ProxyEnable=1` 且宿主域名在 `ProxyOverride` | 该域名直连，代理故障不解释其现象 | 已确认 |
| 有 `AutoConfigURL` 且该 URL 不可达 | 解析规则失败，**行为不确定** | 已确认 |

### 6.3 验证代理本身可达

代理配置存在但不可达，是「配置看起来正常却全部不通」的典型。取证：

```powershell
Test-NetConnection -ComputerName <代理主机> -Port <代理端口> -InformationLevel Detailed
```

⚠️ **必须验证，不能只读配置。** `network-layered-probe.md § 5` 的判据「有代理且代理不可达 → 全部流量失败」要求的就是这一步；只读到配置就下结论属于跳过取证。

### 6.4 PAC 脚本：读到 URL 只是开始

有 `AutoConfigURL` 时，代理规则**不在注册表里**，须取回脚本判读：

```powershell
Invoke-WebRequest -Uri <AutoConfigURL> -UseBasicParsing | Select-Object -ExpandProperty Content
```

| 输出情况 | 判定 | 强度 |
|---|---|---|
| 取不回（超时/404） | **PAC 失效，代理行为不确定** | 已确认 |
| 取回脚本，宿主域名匹配到 `DIRECT` | 该域名直连 | 已确认 |
| 取回脚本，宿主域名匹配到某代理 | 须再验证该代理可达（回 § 6.3） | 已确认（规则）｜ 推测（是否为主因） |

⚠️ **PAC 是 JavaScript，人工判读易错。** 脚本含多重条件、正则、`dnsResolve` 调用时，静态阅读得出的匹配结果**不可作为强证据**。此时应改为行为验证：用 § 8 的 TCP 探测直接测目标域名，观察实际结果。

⚠️ **`Invoke-WebRequest` 自身会走系统代理**，可能出现"因为代理坏了所以取不到 PAC，而 PAC 本来是要说这个域名直连"的循环。必要时加 `-NoProxy`（PowerShell 6+）对照。

### 6.5 本层的边界

| 判不了 | 原因 |
|---|---|
| 代理服务器的转发策略 | 服务端规则对客户端不可见（`network-layered-probe.md § 11`） |
| 应用是否真的遵循系统代理 | 应用可自带代理设置或硬编直连；须看应用自身配置 |
| 代理配置由谁设置 | 同 hosts，从内容无法判断来源 |

---

## 7. 第 5 层：LSP / 命名空间提供者

对应 `network-layered-probe.md § 6`。**残留的损坏 LSP 是「突然完全无法联网」的经典成因。**

### 7.1 命令

| 目的 | cmd | PowerShell |
|---|---|---|
| **枚举 Winsock 协议链** | `netsh winsock show catalog` | 无 cmdlet（须调 `netsh`） |
| 命名空间提供者 | 含在上述输出中 | 同上 |

**这一层没有 PowerShell 原生 cmdlet。** `dotnet-probing-techniques.md § 3.3` 说明托管侧亦无封装（须 P/Invoke `WSCEnumProtocols`）——`netsh winsock show catalog` 是唯一的零成本取证路径。

### 7.2 判读

输出中每个条目的关键字段是 **`Path`**（提供者 DLL 路径）与 **`Provider`**（描述）：

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 全部条目的 `Path` 指向 `%SystemRoot%\system32\` 下的系统 DLL（`mswsock.dll`、`winrnr.dll`、`nlaapi.dll` 等） | 无第三方干预 | 已确认 |
| 存在 `Path` 指向第三方目录的条目 | **网络调用经第三方组件** | 已确认（存在）｜ 推测（是否为主因） |
| **`Path` 指向的文件不存在** | **链已损坏**，网络功能可能异常 | 已确认 |

⚠️ **第三行必须实际验证文件是否存在，`netsh` 不会替你检查。** 取出 `Path` 后逐个测：

```powershell
netsh winsock show catalog |
  Select-String 'Path' |
  ForEach-Object { ($_ -split ':\s*',2)[1].Trim() } |
  Sort-Object -Unique |
  ForEach-Object { [PSCustomObject]@{ Path=$_; Exists=(Test-Path ([Environment]::ExpandEnvironmentVariables($_))) } }
```

`Exists` 为 `False` 的条目即损坏项——这是本层最强的判据，且**在软件卸载后尤其常见**。

### 7.3 与模块注入交叉验证

`network-layered-probe.md § 6` 指出 LSP 的 DLL 会被加载进使用网络的进程，两处可交叉验证：

```
tasklist /m /fi "imagename eq <宿主进程名>"
```

若 `netsh winsock show catalog` 中的第三方 DLL 同时出现在宿主进程的模块列表中，两处证据互证。判断该模块是否可疑转 `module-injection.md`。

### 7.4 本层的边界

| 判不了 | 原因 |
|---|---|
| 第三方提供者是否为故障主因 | 存在 ≠ 有害；正常用途包括 VPN、加速器、安全软件（`network-layered-probe.md § 6`） |
| 提供者的实际行为 | 静态枚举看不到它对调用做了什么；观测行为须 ETW，见 `dotnet-probing-techniques.md § 6` |
| 32 位链是否也有问题 | ⚠️ 见 `dotnet-probing-techniques.md § 3.3`——64 位环境默认只看到 64 位链；`netsh` 输出已含两者，但须留意条目的位数标注 |

---

## 8. 第 6 层：域名可达性

对应 `network-layered-probe.md § 7`。**本层是全篇价值最高的一层**——它要求区分三种「不可达」，而这个区分只能靠 TCP 层探测完成。

### 8.1 为什么 `ping` 不能用于本层

⚠️ **`ping` 无法验证服务可达性。** `network-layered-probe.md § 8` 已警告「ICMP 结果不完全代表业务流量」，在本层这个警告更强：

| `ping` 的问题 | 后果 |
|---|---|
| ICMP 与 TCP 是不同协议 | 防火墙可放通 ICMP 而阻断 TCP 端口，反之亦然 |
| 不涉及端口 | 服务端口未监听时 `ping` 依然通 |
| 常被策略性屏蔽 | 大量公网主机默认丢弃 ICMP，`ping` 不通是**正常配置**，不是故障 |

**结论**：`ping` 只用于 § 9 的延迟测量，**不得**作为本层「服务可达」的判据。本层必须用 TCP 探测。

### 8.2 命令：TCP 探测（即「tcp ping」）

| 目的 | PowerShell | cmd | 可用性 |
|---|---|---|---|
| **单目标 TCP 探测** | `Test-NetConnection <域名> -Port 443` | 无内置等价 | Win8/2012+ |
| 含详细信息 | `Test-NetConnection <域名> -Port 443 -InformationLevel Detailed` | — | 同上 |
| 仅返回布尔 | `Test-NetConnection <域名> -Port 443 -InformationLevel Quiet` | — | 同上 |
| **按清单批量** | 见 § 8.5 | — | 同上 |

⚠️ **cmd 侧无 TCP 探测工具。** 这是本篇唯一一处 cmd 侧完全缺位的能力——Windows 未内置 `tcping`。若目标机器无法用 PowerShell（如 Win7 无 `Test-NetConnection`），退路是：

```
curl.exe -v --connect-timeout 5 https://<域名>/    (Win10 1803+ 内置)
```

或用 `telnet <域名> 443`（需先启用 Telnet 客户端可选功能，属**安装操作**，不推荐）。

### 8.3 `Test-NetConnection` 输出判读：三种不可达的区分

**这是本篇最关键的一张表。** `network-layered-probe.md § 7` 要求区分三种不可达，其判定依据就是以下字段组合：

| `NameResolutionSucceeded` | `TcpTestSucceeded` | 耗时 | 判定 | 转向 |
|---|---|---|---|---|
| `True` | `True` | 快 | 本层通过 | 进 § 9 |
| **`False`** | `False` | — | **解析失败** | 回 § 4 / § 5 |
| `True` | **`False`** | **接近超时值（数秒）** | **被静默丢弃** → 防火墙/网络策略 | `security-software.md` |
| `True` | **`False`** | **极快（<1s）** | **连接被主动拒绝** → 服务端或中间设备拒绝 | 服务方确认 |

⚠️ **耗时是区分后两行的唯一依据，必须记录。** `network-layered-probe.md § 7` 说「报『不可达』而不区分类型的诊断结论是低价值的」——而区分的操作方法就是看**失败得快还是慢**：

- **慢失败（超时）**= 数据包被丢弃，没有任何回应。典型为防火墙 `DROP` 规则
- **快失败（拒绝）**= 收到了 `RST`，对方明确拒绝。典型为端口未监听或防火墙 `REJECT`

`Test-NetConnection` 不直接给耗时，须自行计时：

```powershell
Measure-Command { Test-NetConnection <域名> -Port 443 -InformationLevel Quiet } |
  Select-Object -ExpandProperty TotalSeconds
```

⚠️ **`Test-NetConnection` 的超时不可配置**（约 1-2 秒后重试，总计数秒）。需要精确控制超时时，改用：

```powershell
$c = [System.Net.Sockets.TcpClient]::new()
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ok = $c.ConnectAsync('<域名>', 443).Wait(5000)
$sw.Stop(); $c.Dispose()
[PSCustomObject]@{ Connected = $ok; ElapsedMs = $sw.ElapsedMilliseconds }
```

### 8.4 TLS 握手与证书链：`curl` 的用途

`network-layered-probe.md § 7` 指出「连接建立成功但 TLS 握手失败，指向证书链问题」，并强调**这类问题的现象是「连不上」，但根因在证书而非网络**。

TCP 探测通过而应用仍失败时，**必须**验证 TLS 层。`curl.exe` 是 Win10 1803+ 内置：

```
curl.exe -v -o NUL --connect-timeout 5 --max-time 15 https://<域名>/
```

PowerShell 侧对照：

```powershell
Invoke-WebRequest -Uri https://<域名>/ -UseBasicParsing -TimeoutSec 15
```

`curl -v` 输出的判读要点：

| 输出行 | 判定 | 强度 |
|---|---|---|
| `Connected to <域名> (<IP>) port 443` | TCP 层通过，且**给出了实际使用的 IP**（可与 § 4 的解析结果对照） | 已确认 |
| `SSL certificate problem: unable to get local issuer certificate` | **根证书缺失**——企业环境常见 | 已确认 |
| `SSL certificate problem: self signed certificate` | **中间人代理**在替换证书 | 已确认 |
| `schannel: ... certificate revocation` | 吊销检查失败，常因网络不通导致（与 `dotnet-probing-techniques.md § 3.1` 同一陷阱） | 推测 |
| `HTTP/1.1 200` 或任何 HTTP 状态行 | **应用层完全通达**，网络侧无问题 | 已确认 |
| `Recv failure` / `Connection was reset` | 连接中途被切断，指向中间设备干预 | 推测 |

⚠️ **拿到 HTTP 状态行即可结束网络层排查。** 无论状态码是 200 还是 403，能收到 HTTP 响应就证明网络链路（含 DNS、TCP、TLS、代理）全部通达——此时现象的根因在应用层或服务端，按 `symptom-routing.md` 重新分流。

⚠️ **`curl.exe` 默认走系统代理**（读 `HTTP_PROXY` 环境变量与部分系统设置）。与 § 6 的代理配置结论交叉时，加 `--noproxy '*'` 做直连对照。

⚠️ **`curl` 是 GET 请求，属只读，但会真实访问服务。** 对生产服务的探测须选无副作用的端点（健康检查路径优于业务接口），并遵守 `rules/01 § 1` 的最小影响原则。

### 8.5 按域名清单批量探测

`network-layered-probe.md § 7` 要求「按宿主域名清单逐个探测」，且 § 域名清单必须外置 要求清单为配置数据。命令行侧的对应做法：

```powershell
$domains = Get-Content .\domains.txt      # 外置清单，不硬编
$domains | ForEach-Object {
    $r = Test-NetConnection $_ -Port 443 -InformationLevel Detailed -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Domain   = $_
        Resolved = $r.NameResolutionSucceeded
        RemoteIP = $r.RemoteAddress
        TcpOk    = $r.TcpTestSucceeded
    }
} | Format-Table -AutoSize
```

判读按 `network-layered-probe.md § 7` 的判据表：

| 结果分布 | 判定 | 强度 |
|---|---|---|
| 全部 `TcpOk=True` | 本层通过 | 已确认 |
| 全部 `False` 但公共站点可达 | **宿主服务被针对性阻断** | 推测 |
| 部分 `False` | 按不可达域名的用途判断影响面 | 推测 |
| `Resolved=False` 集中在某后缀 | 该后缀的 DNS 解析异常，回 § 4 | 已确认 |

⚠️ **必须同时探测一个公共对照站点**，否则无法区分"宿主服务被阻断"与"整机网络不通"。

### 8.6 本层的边界

| 判不了 | 原因 |
|---|---|
| **服务端是否有故障** | 本领域只在客户端取证（`network-layered-probe.md § 11`） |
| 阻断规则的具体内容 | 快/慢失败能推断 DROP 或 REJECT，但读不到规则本身 |
| 阻断由哪一环施加 | 本机防火墙、企业网关、运营商无法从客户端区分；转 `security-software.md` 查本机侧 |

---

## 9. 第 7 层：延迟、丢包与路径

对应 `network-layered-probe.md § 8`。本层**必须**按 `rules/02 § 2` 多次采样。

### 9.1 命令

| 目的 | cmd | PowerShell | 说明 |
|---|---|---|---|
| **延迟与丢包采样** | `ping -n 20 <域名>` | `Test-Connection <域名> -Count 20` | 默认仅 4 次，**必须显式加大** |
| 持续观测 | `ping -t <域名>`（Ctrl+C 停止） | `Test-Connection <域名> -Count 100` | 用于捕捉间歇性故障 |
| **逐跳路径** | `tracert <域名>` | `Test-NetConnection <域名> -TraceRoute` | 见 § 9.3 |
| **逐跳丢包统计** | `pathping <域名>` | 无等价 | 见 § 9.4，耗时约 5 分钟 |
| 指定包大小（探 MTU） | `ping -f -l 1472 <域名>` | — | 见 § 9.5 |

### 9.2 `ping` 输出判读

⚠️ **`ping` 的结论仅限「ICMP 层的链路质量」**，不代表业务流量（§ 8.1）。它在本层的合法用途是**测量链路质量**，而非判断可达性。

关注 `ping` 统计段的四个字段：

| 字段 | 判读 | 强度 |
|---|---|---|
| `Lost = 0 (0% loss)` | ICMP 层无丢包 | 已确认（测量事实） |
| `Lost > 0` | **链路不稳定**，可能表现为断续 | 已确认 |
| `Average` 显著高于阈值 | 链路质量差 | 已确认（测量）｜ 推测（是否为主因） |
| **`Minimum` 与 `Maximum` 差距大** | **抖动剧烈**——对实时功能影响大于高均值 | 已确认 |

⚠️ **第四行是本层最易被漏掉的判据。** `network-layered-probe.md § 8` 明确「波动比绝对值更重要」，但 `ping` 的默认输出把 `Minimum/Maximum/Average` 三者并列，读者习惯只看 `Average`。**判读必须同时记录极差。**

阈值须按 `hardware-thresholds.md § 1` 的可调参数原则处理——**本篇不给具体毫秒数**，因为合理阈值取决于服务端地理位置与业务类型，凭空给值即违反该原则。

### 9.3 `tracert`：定位断点位置

⚠️ **本节修正 `network-layered-probe.md § 11` 的一处过度收窄。** 该节把「中间网络设备的策略」整体列为判不了，理由是"规则对客户端不可见"。这对**规则内容**成立，但对**断点位置**不成立——`tracert` 能给出已确认的测量事实。

```
tracert -d <域名>          # -d 跳过反向 DNS，显著加快
tracert -h 15 <域名>       # 限制最大跳数，避免长时间等待
```

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 完整到达目标 | 路径连通 | 已确认 |
| **前 N 跳正常，之后全部 `* * *` 直到超出跳数** | **链路在第 N 跳之后中断** | 已确认（测量事实） |
| 中间若干跳 `* * *` 但**最终到达目标** | 中间设备不响应 ICMP，**属正常配置** | 已确认（非故障） |
| 第 1 跳即超时 | 本机到网关异常，回 § 3 | 已确认 |
| 某跳延迟骤增且后续持续高 | 该跳为质量瓶颈所在 | 推测 |

⚠️ **第三行是 `tracert` 最高频的误读。** 中途出现 `* * *` 而最终到达目标，说明只是那些跳的设备不回 ICMP——**这不是故障**。只有"之后再也没有响应且未到达目标"才构成断点证据。

⚠️ **`tracert` 走 ICMP，路径可能与 TCP 流量不同。** 运营商对 ICMP 与 TCP 可能走不同链路或不同策略，因此 `tracert` 显示的路径**不保证**就是业务流量的实际路径。这是 § 8.1 同一警告在本层的延续。

**能得出的结论形态**：「链路在第 5 跳（`x.x.x.x`）之后中断」——这是可交给网络方或运营商的具体信息，远优于「网络不通」。**判不了的仍然是**：那一跳为什么不转发。

### 9.4 `pathping`：区分「路径丢包」与「终点丢包」

`ping` 只告诉你端到端丢了多少，`pathping` 告诉你**丢在哪一跳**：

```
pathping -q 50 -h 15 <域名>
```

⚠️ **`pathping` 默认耗时约 5 分钟**（每跳采样 100 次）。`-q 50` 减少采样数可缩短，但会降低统计可靠性——须在结果中记录实际采样数（`rules/02 § 2`）。

输出的第二段（统计表）关键列：

| 列 | 含义 | 判读 |
|---|---|---|
| `This Node/Link Lost/Sent = Pct` | **该跳自身或其入链路的丢包率** | 这是定位丢包点的依据 |
| `Address` | 该跳地址 | 用于向网络方指明位置 |

| 输出特征 | 判定 | 强度 |
|---|---|---|
| 某跳起丢包率骤升且后续各跳维持 | **该跳为丢包源** | 已确认（测量事实） |
| 中间跳有丢包但**末跳为 0%** | 中间设备对 ICMP 限速，**非真实丢包** | 已确认（非故障） |
| 仅末跳有丢包 | 终点侧或最后一段链路问题 | 推测 |

⚠️ **第二行同样是高频误读**——路由器对自身产生的 ICMP 回应限速是标准行为。**只有末跳的丢包率才代表端到端质量。**

### 9.5 MTU 问题：「小请求正常、大请求失败」的成因

`network-layered-probe.md § 9` 记有判据「小文件正常但大文件失败 → 可能是超时或中间设备限制」，但未给排查手段。**MTU 不匹配是该现象的一个具体且可测的成因**：

```
ping -f -l 1472 <域名>        # 1472 + 28 字节头 = 1500，标准以太网 MTU
ping -f -l 1400 <域名>        # 逐步减小定位实际 MTU
```

`-f` 为「禁止分片」，`-l` 指定负载大小。

| 输出 | 判定 | 强度 |
|---|---|---|
| 1472 成功 | 路径 MTU ≥ 1500，无 MTU 问题 | 已确认 |
| 1472 返回 `Packet needs to be fragmented but DF set` | **路径 MTU < 1500** | 已确认 |
| 逐步减小后某值成功 | 实际路径 MTU = 该值 + 28 | 已确认 |

**典型场景**：VPN、PPPoE 隧道会降低有效 MTU。若同时存在 § 3.3 的 VPN 证据，两处互证。

⚠️ **MTU 问题的现象极具误导性**：TCP 握手（小包）成功、`ping` 默认（32 字节）成功、`Test-NetConnection` 通过，**只有传输大数据时失败**。因此它常被误判为服务端故障。

### 9.6 本层的边界

| 判不了 | 原因 |
|---|---|
| ICMP 结果是否代表业务流量 | 协议不同，见 § 8.1；须以 § 8 的 TCP 探测为准 |
| 中间设备的**规则内容** | 仍然判不了（本节只把「断点位置」从这一条里分离出来） |
| **间歇性故障** | 单次采样正常不代表持续正常（`network-layered-probe.md § 11`）；须长时间采样，见 § 9.1 的持续观测 |
| 丢包的物理成因 | 线路、无线干扰、设备过载无法从客户端区分 |

---

## 10. 第 8 层：下载测速

对应 `network-layered-probe.md § 9`。

### 10.1 命令

| 目的 | cmd | PowerShell |
|---|---|---|
| **限额下载计时** | `curl.exe -o NUL --max-time 15 --max-filesize 20000000 <URL>` | 见下 |
| 计时 | 见 `curl` 的输出统计 | `Measure-Command { Invoke-WebRequest <URL> -OutFile $env:TEMP\speedtest.tmp }` |

```
curl.exe -o NUL -w "size=%{size_download} time=%{time_total} speed=%{speed_download}\n" --max-time 15 <URL>
```

`-w` 直接输出结构化统计，无需另行计时——这是 `curl` 相对 `Invoke-WebRequest` 的实质优势。

### 10.2 三条纪律的命令级落地

`network-layered-probe.md § 9` 的三条纪律，对应到参数：

| 纪律 | 落地 |
|---|---|
| **① 必须限额** | `--max-time` + `--max-filesize`；**不得省略**——计量连接下会耗尽用户流量 |
| **② 结果受并发影响** | 采集时须记录用户是否在下载其他内容；结果不代表带宽上限 |
| **③ 应使用宿主自己的服务端点** | URL 取自 § 8.5 的外置清单，**不用第三方测速站点** |

⚠️ **`-o NUL` 是必要的**（PowerShell 侧写入 `$env:TEMP`）：不指定输出会把内容打到终端，既污染输出又拖慢速度导致测量失真。

### 10.3 判读

| 输出特征 | 判定 | 强度 |
|---|---|---|
| `speed_download` 符合预期 | 本层通过 | 已确认（相对阈值） |
| 远低于预期 | 带宽受限或链路质量差 | 已确认（测量事实） |
| 因 `--max-time` 中断且已下载量很小 | 传输极慢或中途停滞 | 已确认 |
| 小文件成功、大文件失败 | 转 § 9.5 查 MTU，或查中间设备超时 | 推测 |

阈值同 § 9.2——**本篇不给具体数值**，须按 `hardware-thresholds.md § 1` 实测校准。

### 10.4 本层的边界

| 判不了 | 原因 |
|---|---|
| 可用带宽上限 | 受并发影响，单次测速只是下限 |
| 慢的成因 | 带宽、链路质量、服务端限速无法从客户端区分 |

---

## 11. 现象直达速查

`network-layered-probe.md § 1 分层与现象的对应` 给了「现象 → 起查层」，本节接上「起查层 → 敲什么」。

⚠️ **跳层的前提不变**：该层不通时**必须**回到 § 3 按序重查（`network-layered-probe.md § 1`）。

| 用户描述 | 起查节 | 第一条命令 |
|---|---|---|
| 完全用不了、什么都加载不出 | § 3 | `ipconfig /all` |
| 有的功能能用有的不能 | § 6 | `netsh winhttp show proxy` + WinINET 注册表 |
| 消息发不出但界面正常 | § 8 | `Test-NetConnection <域名> -Port 443` |
| 能用但很慢 | § 9 | `ping -n 20 <域名>` |
| 文件传输失败但消息正常 | § 10 → § 9.5 | `curl.exe -w ...` → `ping -f -l 1472` |
| 突然完全无法联网（近期卸载过软件） | § 7 | `netsh winsock show catalog` |
| 提示证书错误 / 安全连接失败 | § 8.4 | `curl.exe -v https://<域名>/` |
| 只有某个域名不通 | § 5 → § 4 | hosts 全文 → `Resolve-DnsName` |

### 11.1 最小取证集

时间有限或需用户自助配合时，以下五条覆盖八层中的关键判据：

```
ipconfig /all
nslookup <域名>
netsh winhttp show proxy
ping -n 20 <域名>
curl.exe -v -o NUL --connect-timeout 5 https://<域名>/
```

⚠️ **这是筛查集，不是完整取证。** 它不覆盖 § 5（hosts）、§ 7（LSP）、§ 9.3-9.5（路径与 MTU）。**筛查无果不构成「网络正常」的结论**——这正是 `rules/02 § 3` 禁止的「把『没查到』呈现为『没问题』」。

---

## 12. 本篇覆盖边界

### 12.1 本篇能给的

| 能给 | 说明 |
|---|---|
| 八层各自的具体命令（cmd 与 PowerShell 双栏） | 零安装，故障机器上必定可用 |
| 输出的**哪个字段**对应哪条判据 | 落地 `rules/02 § 1 原始输出优先` |
| 三种不可达的**操作级区分方法** | § 8.3 的快/慢失败，原判据表未给手段 |
| 断点位置的定位（§ 9.3、§ 9.4） | 把原「中间设备判不了」中可测的部分分离出来 |
| 高频误读的防线 | `* * *`、中间跳丢包、`nslookup` 绕过 hosts 等 |

### 12.2 本篇不覆盖

| 不覆盖 | 应查 |
|---|---|
| **判据本身与结论强度规则** | `network-layered-probe.md`、`rules/03-conclusion-strength.md` |
| **具体阈值数值** | `hardware-thresholds.md § 1`；本篇有意不给数值，避免把未校准初值变成硬判据 |
| 在 C# 里如何实现这些采集 | `dotnet-probing-techniques.md` |
| 网络之外七层的命令行手段（模块、安全软件、硬件、环境劫持） | **尚未覆盖**，见 § 12.4 |
| 抓包与 ETW 分析 | `dotnet-probing-techniques.md § 6`；本篇口径为零安装轻量命令 |
| 修复动作 | 本篇全部只读（§ 2.3）；修复须按 `rules/01 § 2` 确认与记录回滚 |

### 12.3 本篇的固有局限

⚠️ **① 命令行工具的输出格式随 Windows 版本变化。** 本篇引用的字段名（如 `TcpTestSucceeded`、`Media State`）在中文系统上显示为中文。`findstr` 匹配英文字段名会在中文系统上失效——与 `dotnet-probing-techniques.md § 5.2` 的「不要硬编中文计数器名」是同一类问题的镜像。**批量脚本应按 PowerShell 对象属性取值，不按输出文本匹配。**

⚠️ **② `Test-NetConnection` 在 Win7 / Server 2008 R2 上不存在。** 这类环境退回 § 8.2 的 `curl` 或 `TcpClient` 路径。

⚠️ **③ 全部命令只反映执行瞬间的状态。** 间歇性故障须按 § 9.1 持续观测，单次采集正常不构成排除依据。

⚠️ **④ 命令行探测的是「本机当前用户上下文」。** 宿主进程若以其他用户或服务身份运行，其代理配置（§ 6 的 WinINET 为用户级）与本篇采集结果可能不同。

### 12.4 其余四类的命令行手段

本篇只覆盖**网络层**。其余四类故障源（模块注入、安全软件、硬件资源、环境劫持）的命令行手段见 **`cli-process-toolbox.md`**（1.2.0 新增），结构与本篇一致。

⚠️ **两篇有一处重要差异**：网络层几乎全部检测面都有内置命令，而 `cli-process-toolbox.md § 9.2` 登记了**四处确实不可得**的能力缺口（模块加载方式、WFP 过滤器枚举、WPF 渲染层级、CPU 指令集特性位）。跨篇排查时须注意这个不对称。

### 12.5 与其他篇的交接

| 情形 | 转向 |
|---|---|
| 已定位到层，需要判据与结论措辞 | `network-layered-probe.md` 对应层 |
| 怀疑防火墙规则或安全软件拦截（§ 8.3 慢失败） | `security-software.md` |
| LSP 的 DLL 需判断来源（§ 7.3） | `module-injection.md` |
| hosts / 代理配置疑似被劫持（§ 5、§ 6） | `system-environment-hijack.md` |
| 网络全部正常但现象仍在（§ 8.4 拿到 HTTP 状态行） | `symptom-routing.md` 重新分流 |
| 需要把这些采集写进诊断工具 | `dotnet-probing-techniques.md` |

---
