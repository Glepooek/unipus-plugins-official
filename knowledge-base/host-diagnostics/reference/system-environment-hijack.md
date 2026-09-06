# 系统环境劫持检测

> 本篇收录**启动期环境劫持**的五个检测点。这类问题的共同特征：故障发生在程序自身代码运行之前，现象却表现为「程序有 bug」。

## 为什么这五项优先级最高

三个原因叠加，使这类检查的投入产出比高于其余全部检测项：

1. **取证成本极低**——全部是读注册表，无需提权、无需枚举进程、无需网络
2. **误判率极高**——现象是启动失败或莫名卡顿，开发者第一反应是查自己的代码，可能耗掉数天
3. **判据确定性强**——多数情形下键值存在即可判定，是本领域少数能给「已确认」强度结论的检测项

因此在任何排查流程中，这五项都应排在最前面。见 `reference/symptom-routing.md`。

## 判据强度总览

| 检测点 | 典型强度 | 说明 |
|---|---|---|
| IFEO Debugger | 已确认 | 键存在即劫持，但需排除合法调试配置 |
| GlobalFlag | 已确认 | 标志位可精确判读 |
| AppCompatFlags | 已确认 | 值可精确判读，但影响程度需结合现象 |
| URL 协议注册 | 已确认 / 推测 | 缺失可确认；被抢占需判断是否合理 |
| AppInit_DLLs | 已确认 | 键值存在且非空即生效 |

## 通用取证前提

**读取位置的两个作用域**：本篇多数检测点在 `HKLM`（machine 级）与 `HKCU`（user 级）都可能存在，**必须两处都查**。只查一处是本类检测最常见的漏检原因。

**WOW64 重定向**：32 位进程读取 `HKLM\SOFTWARE` 会被重定向到 `Wow6432Node`。诊断 64 位宿主时，工具本身应为 64 位，或显式使用 `KEY_WOW64_64KEY`。见 `reference/dotnet-probing-techniques.md`。

---

## 1. IFEO Debugger 劫持

### 机制

Image File Execution Options（IFEO）是 Windows 的调试器附加机制：为某个 exe 名注册 `Debugger` 值后，**系统在启动该 exe 时改为启动 Debugger 指定的程序**，并把原 exe 路径作为参数传入。

关键点：**匹配的是 exe 文件名，不是完整路径**。任何位置的同名 exe 都会被劫持。

### 取证位置

```
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>
  值名：Debugger        类型：REG_SZ
```

64 位系统上 32 位视图另有：

```
HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>
```

### 判据

| 观察 | 判定 | 强度 |
|---|---|---|
| 子键不存在 | 无 IFEO 劫持 | 已确认 |
| 子键存在但无 `Debugger` 值 | 无劫持（可能只配了其他 IFEO 选项，如 GlobalFlag） | 已确认 |
| `Debugger` 值存在且非空 | **启动被重定向** | 已确认 |

### 正常与异常形态

**合法用途**（不应判为故障）：

- 开发者主动配置的调试器附加（值指向 `vsjitdebugger.exe`、`windbg.exe` 等）
- 部分安全软件的合法沙箱机制

**异常形态**：

- 值指向不存在的路径 → 目标程序**完全无法启动**，且报错信息通常与真实原因无关
- 值指向非调试器的第三方程序 → 启动被中转，可能表现为启动慢、闪退、或启动了别的东西

### 判据模板

```
现象/输入：目标 exe 双击无反应 / 闪退 / 报错信息与代码逻辑无关
判据：IFEO\<exe名> 下 Debugger 值存在且非空
结论：启动流程被重定向至该值指向的程序
强度：已确认（劫持存在）；该劫持是否为故障主因 → 推测，需结合值的内容判断
下一步：检查 Debugger 指向的路径是否存在、是否为已知调试器
```

### 边界

- **不能仅凭键存在就判定为恶意**——须区分合法调试配置与异常劫持
- IFEO 还有其他值（`GlobalFlag`、`MitigationOptions` 等），本节只覆盖 `Debugger`；`GlobalFlag` 见 § 2

---

## 2. GlobalFlag 堆调试标志

### 机制

GlobalFlag（GFlags）是 Windows 的全局调试标志集。其中若干标志会启用**堆调试**功能——每次堆分配都做额外的校验、填充与记录。

这些标志的设计用途是排查堆破坏，代价是**性能大幅下降**。在生产环境误开会导致程序运行极慢，但功能完全正常——这个组合极易被误判为「程序性能有问题」。

### 取证位置

两处作用域，语义不同：

```
# 系统全局（影响所有进程）
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager
  值名：GlobalFlag      类型：REG_DWORD

# 单个 exe（影响指定程序，位于 IFEO 下）
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe名>
  值名：GlobalFlag      类型：REG_DWORD 或 REG_SZ
```

### 判据

关注的是**堆调试相关位**是否被置位。典型影响性能的标志：

| 标志 | 位值 | 作用 | 性能影响 |
|---|---|---|---|
| `hpa`（Enable page heap） | `0x02000000` | 全页堆校验 | **极大**——每次分配占用整页 |
| `htc`（Enable heap tail checking） | `0x00000010` | 堆尾校验 | 大 |
| `hfc`（Enable heap free checking） | `0x00000020` | 释放校验 | 大 |
| `hpc`（Enable heap parameter checking） | `0x00000040` | 参数校验 | 中 |
| `ust`（Create user mode stack trace DB） | `0x00001000` | 分配栈回溯 | 大——每次分配记栈 |

> ⚠️ 页堆另有独立开关位置（`PageHeapFlags`），且 `gflags.exe -p` 设置的是这一处。检测时两处都应查。

| 观察 | 判定 | 强度 |
|---|---|---|
| 两处 GlobalFlag 均不存在或为 0 | 无堆调试开启 | 已确认 |
| 任一处置有上表标志位 | **堆调试已开启，性能受影响** | 已确认 |

### 判据模板

```
现象/输入：程序运行极慢但功能正常；CPU 未打满；无明显阻塞点
判据：Session Manager 或 IFEO\<exe名> 的 GlobalFlag 含堆调试位
结论：堆调试标志导致性能塌陷
强度：已确认
下一步：确认该标志是谁设置的（开发调试遗留 / 安全软件 / 手工误设）
```

### 边界

- GlobalFlag 有数十个标志位，本节只覆盖**影响性能的堆调试类**
- 其余标志（如内核调试相关）不在本节判据内
- 标志被设置的**原因**无法从注册表判断

---

## 3. AppCompatFlags 兼容模式

### 机制

Windows 应用兼容性数据库允许为特定 exe 设置兼容性层（Compatibility Layer），如以旧版 Windows 模式运行、禁用视觉主题、以管理员身份运行等。

对现代应用（尤其是 WPF/DirectX 程序），**误设的兼容性标志会导致渲染异常、DPI 错乱、功能失效**。

### 取证位置

两处作用域，**都要查**：

```
# 当前用户（更常见，普通用户即可设置）
HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers
  值名：<exe完整路径>   类型：REG_SZ   值内容：空格分隔的标志串

# 本机所有用户
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers
```

### 判据

值内容是空格分隔的标志串，常见且**对现代应用有害**的：

| 标志 | 含义 | 对 WPF/现代应用的影响 |
|---|---|---|
| `WIN7RTM` / `WINXPSP3` / `VISTARTM` 等 | 以旧版 Windows 模式运行 | API 行为回退，可能导致 DPI、渲染、字体异常 |
| `DISABLEDWM` | 禁用桌面窗口管理器 | **WPF 硬件渲染失效**，可能白屏或严重卡顿 |
| `HIGHDPIAWARE` / `DPIUNAWARE` | 强制 DPI 感知模式 | 界面模糊或尺寸错乱 |
| `RUNASADMIN` | 始终以管理员运行 | 权限异常、拖放失效（UIPI 隔离） |
| `DISABLETHEMES` | 禁用视觉样式 | 控件外观异常 |

| 观察 | 判定 | 强度 |
|---|---|---|
| 两处均无该 exe 路径的值 | 无兼容性标志 | 已确认 |
| 存在值且含上表标志 | **兼容性层已生效** | 已确认（标志存在）｜ 推测（是否为现象主因） |

### 判据模板

```
现象/输入：界面模糊 / 尺寸错乱 / 白屏 / 控件外观异常 / 拖放失效
判据：AppCompatFlags\Layers 下存在该 exe 路径的值，且含 DISABLEDWM、DPIUNAWARE 等标志
结论：兼容性层改变了程序运行环境
强度：已确认（标志生效）；与具体现象的因果 → 推测
下一步：按标志含义比对现象；临时移除标志后复现验证
```

### 边界

- **值名是 exe 的完整路径**——程序移动位置后旧值失效但仍残留，须比对路径是否为当前实例
- 兼容性标志还可能来自系统兼容性数据库（`.sdb` 文件），本节**不覆盖**——那需要解析 shim 数据库，成本远高于注册表检查
- 标志与现象的因果关系需实验验证，注册表只能证明标志存在

---

## 4. URL 协议注册

### 机制

应用通过注册自定义 URL 协议（如 `myapp://`）接收外部唤起。协议处理器注册在注册表中，指向处理该协议的可执行文件。

两类故障：**缺失**（注册被清除，外部唤起无响应）与**被抢占**（另一程序注册了同名协议，唤起打开了错误的程序）。

### 取证位置

```
# 系统级（传统位置）
HKLM\SOFTWARE\Classes\<协议名>
HKCR\<协议名>                      # HKCR 是 HKLM\Classes 与 HKCU\Classes 的合并视图

# 用户级（优先级更高）
HKCU\SOFTWARE\Classes\<协议名>

必需结构：
  <协议名>\
    (默认值)              = "URL:<描述>"
    "URL Protocol"        = ""            ← 此值必须存在（内容可为空）
    shell\open\command\
      (默认值)            = "<exe路径>" "%1"
```

### 判据

| 观察 | 判定 | 强度 |
|---|---|---|
| 协议键不存在 | **未注册**，外部唤起无响应 | 已确认 |
| 键存在但缺 `URL Protocol` 值 | **注册不完整**，系统不识别为 URL 协议 | 已确认 |
| `shell\open\command` 缺失或路径不存在 | **注册损坏** | 已确认 |
| command 指向的 exe 非目标程序 | **协议被抢占** | 已确认（指向他处）｜ 推测（是否恶意） |
| HKCU 与 HKLM 同时注册且指向不同程序 | **用户级覆盖系统级** | 已确认 |

⚠️ **优先级**：`HKCU\SOFTWARE\Classes` 优先于 `HKLM\SOFTWARE\Classes`。只查 HKLM 会漏掉用户级抢占——这是本节最易漏检的形态。

### 判据模板

```
现象/输入：点击外部链接无法唤起程序 / 唤起了错误的程序
判据：协议键缺失、缺 URL Protocol 值、command 路径无效、或 HKCU 覆盖指向他处
结论：协议注册异常导致唤起失败
强度：已确认
下一步：比对 command 路径与目标程序实际路径；检查 HKCU/HKLM 两级是否冲突
```

### 边界

- **不判断协议被抢占是否为恶意**——多程序注册同一协议可能是合理竞争（如多个浏览器注册 `http`）
- 现代 Windows 的默认应用关联还受「默认应用设置」影响（`UserChoice` 键带哈希保护），本节不覆盖该机制

---

## 5. 其他启动期劫持点

### 5.1 AppInit_DLLs

#### 机制

**所有**加载 `user32.dll` 的进程都会自动加载 `AppInit_DLLs` 中列出的 DLL。这是系统级的全局注入机制，一次配置影响全机器。

#### 取证位置

```
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows
  值名：AppInit_DLLs          类型：REG_SZ    （空格或逗号分隔的 DLL 列表）
  值名：LoadAppInit_DLLs      类型：REG_DWORD （1 = 启用）
  值名：RequireSignedAppInit_DLLs  类型：REG_DWORD （1 = 要求签名）

64 位系统的 32 位视图：
HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Windows
```

#### 判据

| 观察 | 判定 | 强度 |
|---|---|---|
| `LoadAppInit_DLLs` = 0 或不存在 | 机制未启用，`AppInit_DLLs` 内容不生效 | 已确认 |
| `LoadAppInit_DLLs` = 1 且 `AppInit_DLLs` 非空 | **列出的 DLL 会注入所有 GUI 进程** | 已确认 |

> ⚠️ **判定顺序**：必须先看 `LoadAppInit_DLLs`。只看 `AppInit_DLLs` 非空就报警会产生误报——残留配置在开关关闭时不生效。

> **与模块注入的关系**：本项检出的 DLL 会出现在目标进程的模块列表中。两处证据可交叉验证——见 `reference/module-injection.md`。

#### 边界

- Secure Boot 启用时该机制被系统禁用，检出非空值也不生效
- 本节只判断机制是否启用与列表内容，**不判断列出的 DLL 是否有害**（符合本领域「不给名单」约束）

### 5.2 ShellExecute Hooks

#### 机制

注册的 COM 对象会在 `ShellExecute` 调用时被加载到调用进程中，可干预或拦截 shell 启动行为。

#### 取证位置

```
HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ShellExecuteHooks
  子项：<CLSID>

对应实现位置：
HKLM\SOFTWARE\Classes\CLSID\<CLSID>\InprocServer32
  (默认值) = DLL 路径
```

#### 判据

| 观察 | 判定 | 强度 |
|---|---|---|
| 无非系统 CLSID 条目 | 无第三方 shell hook | 已确认 |
| 存在第三方 CLSID | **该 DLL 会加载进调用 ShellExecute 的进程** | 已确认（存在）｜ 推测（是否为现象主因） |

#### 边界

- 需通过 CLSID 反查 `InprocServer32` 才能得到实际 DLL 路径，**两步都要做**——只列 CLSID 无法判断
- 不判断 hook 是否有害

---

## 6. 本篇覆盖边界

### 本篇能判的

- 五个检测点各自的**存在性与配置内容**——全部可从注册表精确读出
- 多数情形可给「已确认」强度：键值存在与否是客观事实

### 本篇不能判的

| 判不了 | 原因 |
|---|---|
| **配置是谁设置的** | 注册表不记录写入者。开发调试遗留、安全软件、企业策略、恶意软件，从值本身无法区分 |
| **配置是否为当前现象的主因** | 存在劫持 ≠ 它导致了这个现象。因果需移除后复现验证——见 `rules/03-conclusion-strength.md § 2 相关性不等于因果` |
| **列出的 DLL / 程序是否有害** | 本领域不内置产品名单，见领域 README「知识库给方法，不给名单」 |
| **企业策略下发的合法配置** | 域环境中部分配置由 GPO 统一下发，属预期行为而非故障。工具应提示而非判定为异常 |
| **兼容性 shim 数据库（.sdb）** | 需解析二进制 shim 数据库，成本远高于注册表检查，本篇不覆盖 |
| **默认应用关联的 UserChoice 机制** | 带哈希保护，非本篇的协议注册检查所能覆盖 |

### 与其他篇的交接

| 情形 | 转向 |
|---|---|
| 检出 AppInit_DLLs 有内容，需判断具体模块 | `reference/module-injection.md` |
| 检出配置疑似安全软件所设 | `reference/security-software.md` |
| 需要具体的注册表读取实现 | `reference/dotnet-probing-techniques.md` |
| **需要具体敲什么命令** | `reference/cli-process-toolbox.md § 6`——五个检测点的 `reg query` 与 PowerShell 双栏命令、判定顺序，及 `§ 6.6` 与模块列表的交叉验证 |
| 五项全部正常但现象仍在 | `reference/symptom-routing.md` 的下一优先级 |

