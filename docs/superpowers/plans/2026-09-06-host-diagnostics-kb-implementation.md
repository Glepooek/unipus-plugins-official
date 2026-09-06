# 实施计划：host-diagnostics 知识库

> 状态：待执行
> 日期：2026-09-06
> Spec：`docs/superpowers/specs/2026-09-06-host-diagnostics-kb-spec.md`
> 基线：执行前 `check_index.py` 全库 576 条，无问题

---

## 0. 全局约束

以下约束对**每个**任务生效，任务正文不再重复。

### 0.1 硬性规则

| 约束 | 依据 |
|---|---|
| 提交必须走 `commit-cc-plugin` skill，禁止手动 git | AGENTS.md |
| 本机无 `pytest`，Python 测试只能用 `unittest` | AGENTS.md |
| 长文档必须分段写入（Write 建骨架 + 多次 Edit 追加），禁止单次输出大段内容 | 全局规则 `output-segmentation.md` |
| 每个任务结束前跑 `check_index.py`，必须 `OK` 才算完成 | 知识库 README § 维护约定 |
| `reviewed_at` 读过正文才填，禁止批量刷新 | 知识库 README § reviewed_at |
| 不预建空目录 | 知识库 README § 目录约束 |

### 0.2 校验命令

```bash
# 单领域 + 全局检查（全局部分始终执行）
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" host-diagnostics

# 健康报告（覆盖率、kind/level 分布、孤儿文件）
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" host-diagnostics --audit
```

### 0.3 版本规则

- 领域独立版本化：`host-diagnostics/README.md` 版本行 + `CHANGELOG.md` 最新条目**必须同值**（脚本校验）
- 每个任务完成后升该领域版本；幅度按知识库 README 的判据
- **不涉及任何插件 `plugin.json`**——本计划全部改动落在 `knowledge-base/` 与 `docs/`

### 0.4 条目质量检验

每条 reference 判据须能填满此模板，填不满说明不够具体：

```
现象/输入：<可观测的具体数据>
判据：<看到什么算命中>
结论：<命中说明什么>
强度：<已确认 | 推测 | 需进一步取证>
下一步：<还要查什么>
```

### 0.5 索引字段基线

```
applies_to（统一）：["Windows", ".NET 8+", ".NET Framework 4.6.2+"]
owner（统一）：      "desktop client team"
status（rule 统一）： "active"
enforcement：        本领域几乎全部为 review，禁止为凑分布强标 ci
id 前缀：            host-diagnostics.<两位编号|ref>.<slug>
```

---

## 1. 任务总览

| # | 任务 | 阶段 | 交付 | 依赖 |
|---|---|---|---|---|
| 1 | 领域骨架 + teardown 迁入 | P0 | 骨架 4 文件 + teardown + catalog 登记 | — |
| 2 | 环境劫持 | P1 | `system-environment-hijack.md` | 1 |
| 3 | 现象反查表 | P1 | `symptom-routing.md` | 2 |
| 4 | 模块注入 | P2 | `module-injection.md` | 1 |
| 5 | 网络分层 | P3 | `network-layered-probe.md` | 1 |
| 6 | rules 三篇 | P4 | `01`/`02`/`03` | 2,4,5 |
| 7 | 安全软件 | P5 | `security-software.md` | 4 |
| 8 | 硬件阈值 | P5 | `hardware-thresholds.md` | 1 |
| 9 | C# 取证手段 | P6 | `dotnet-probing-techniques.md` | 2,4,5,7,8 |
| 10 | VDI 环境 | P7 | `vdi-environment.md` | 8 |
| 11 | 收口验收 | — | 全领域验收 + 反查表回填 | 全部 |

**关键路径**：1 → 2 → 3 → 6 → 11。任务 4、5、8 可在 1 之后并行。

**延后项处置**（对应 spec § 9 的三个 ⏳）：

| Spec 待确认项 | 本计划处置 |
|---|---|
| VDI 是否需要 | **纳入任务 10**，标为可选阶段，执行前由用户拍板 |
| 硬件阈值定值依据 | **纳入任务 8**，采用"行业通用值 + 待实测校准"标注策略 |
| 是否配套建 skill | **纳入任务 11**，作为收口时的评估项，不在本计划内实施 |

---

## 任务 1：领域骨架 + teardown 迁入（P0）

### 目标

建立可被 `check_index.py` 校验通过的领域骨架，并把 aha_doctor 分析文档迁入为依据出处。

### 为什么合并做

teardown 是任务 2-9 全部条目 `source` 字段的指向目标。若延后，后续条目无依据可引，事后回填 `source` 是一轮返工。

### 步骤

**1.1 建目录与骨架文件**

```
knowledge-base/host-diagnostics/
├── README.md
├── CHANGELOG.md
├── index.jsonl
└── reference/
    └── aha-doctor-teardown.md
```

`rules/` **本任务不建**——无内容时建空目录违反「不预建空目录」。任务 6 首次产生 rules 内容时再建。

**1.2 README.md 必含章节**（参照 `dotnet-debugging/README.md` 结构）

- 版本行 `> 版本：0.1.0`
- 领域定位：诊断宿主进程**外部**故障源
- 文档目的与目标读者
- 适用范围：Windows；.NET 8+ / .NET Framework 4.6.2+
- 收录判据（见下）
- 与既有领域的边界表（spec § 2.3 的三行）
- 规范级别（RFC 2119，与 csharp/README.md 同一套）
- 文件地图

**收录判据**（本领域专属，须写清）：

> **判据进知识库，编排进 skill。**
> 检验标准：这条内容能独立成为「查一下就照着用」的判据吗？能 → 本领域。它是否必须知道「上一步查了什么」才有意义？是 → 属 skill，不收。
> 据此：「IFEO Debugger 键存在即为劫持」**收录**；「先查环境劫持 → 无果则查注入 → 再无果则查网络」这条编排**不收**（属反查表的导航，见 `reference/symptom-routing.md`）。

**1.3 CHANGELOG.md**

```markdown
# Changelog — 宿主进程环境诊断

## [0.1.0] - <执行日>

### Added
- 建立领域骨架：README、索引、reference 目录
- 迁入 `reference/aha-doctor-teardown.md`（原 `docs/aha-doctor-analysis.md`），索引 1 条
```

**1.4 teardown 迁入与四处改造**

从 `docs/aha-doctor-analysis.md` 迁入，按 spec § 5.9 做四处调整：

| # | 改造 | 验收 |
|---|---|---|
| 1 | 保留三级来源标记【官方】/【实测】/【推断】 | 三种标记均存在 |
| 2 | 补「快照日期与失效条件」小节 | 声明基于 2026-09-06 快照 + 厂商更新后可能失效 |
| 3 | 「能否改配置诊断其他软件」一节移除 | `grep -c "改配置"` 为 0 |
| 4 | 补「不可作为判据引用的部分」小节 | 明确圈出【推断】内容 |

⚠️ 改造 3 是**删除**动作：该节讨论修改第三方商业软件配置，与本领域定位无关且构成误导性操作指引。删除前确认无其他文档引用该节。

**1.5 索引 1 条**（整篇登记，`anchor: ""`）

按 spec § 5.9 给出的 JSON 写入 `index.jsonl`。

**1.6 catalog.json 登记**

```json
{
  "domain": "host-diagnostics",
  "title": "宿主进程环境诊断",
  "categories": ["reference"],
  "owner": "desktop client team",
  "status": "active",
  "consumers": [],
  "reviewed_at": "<执行日>",
  "notes": "诊断宿主进程外部故障源：第三方模块注入、安全软件拦截、网络不通、硬件不足、系统环境劫持。与 dotnet-debugging 互补——后者负责进程内部（托管堆/线程/锁）取证，本领域负责进程外部环境。目标工具为 .NET 8+ / .NET Framework 4.6.2+ 的 Windows 桌面程序。⚠️ reference/aha-doctor-teardown.md 为第三方商业软件（字节跳动 AHA 电脑医生）的只读静态分析，基于 2026-09-06 本机快照；仅含公开可读配置与文件元数据层面的观察，未反编译二进制、未解密受保护规则包。其中【推断】标记内容不得作为判据依据引用。"
}
```

`categories` 本任务只填 `["reference"]`，任务 6 建 rules 时改为 `["rules", "reference"]`。

**1.7 原文件暂不删除**

⚠️ `docs/aha-doctor-analysis.md` **未提交过 git**（已核实为 `??` 未跟踪状态），删除不可逆。

**本任务保留原文件**，删除动作推迟到任务 11 收口——届时全领域已验证，中间任务若发现 teardown 有缺漏还能从原文件补。详见附录 A。

### 验证

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" host-diagnostics   # 须 OK
```

- [ ] `check_index.py` 输出 OK，全库总数 576 → 577
- [ ] catalog 双向一致（脚本自动校验）
- [ ] README 版本行 `0.1.0` 与 CHANGELOG 最新条目一致
- [ ] 四处改造全部完成
- [ ] teardown 内容与原文逐节比对无缺漏（除有意移除的一节）
- [ ] **原文件 `docs/aha-doctor-analysis.md` 保留**，待任务 11 删除

---

## 任务 2：环境劫持（P1）

### 目标

产出 `reference/system-environment-hijack.md` —— 五个启动期劫持点的判据。

### 为什么排第一

这四类问题排查成本极低（全是读注册表），但**极易被误判成程序 bug**——现象是启动失败或莫名卡顿，开发者第一反应是查自己的代码。投入产出比最高。

### 内容清单

| § | 标题 | 判据要点 |
|---|---|---|
| 1 | IFEO Debugger 劫持 | 注册表位置、Debugger 键存在即劫持、正常/异常形态对比、与合法调试器配置的区分 |
| 2 | GlobalFlag 堆调试标志 | 哪些位会导致性能塌陷、如何读取、正常值 |
| 3 | AppCompatFlags\Layers | 兼容模式标志的副作用、per-user 与 per-machine 两处、常见误设值 |
| 4 | URL 协议注册 | 协议处理器缺失/被抢占的判定、注册表结构 |
| 5 | 其他启动期劫持点 | AppInit_DLLs、ShellExecute Hooks |
| 6 | 本篇覆盖边界 | 判不了什么（如：策略下发的合法配置 vs 恶意劫持难以自动区分） |

### 写作要求

- 每节须给**具体注册表路径**与**判定条件**，不写"检查 IFEO 设置"这类空泛表述
- 每节须标注**结论强度**：这四项多数可给「已确认」（键存在即成立），但须说明例外
- § 6 是本领域每篇 reference 的固定收尾，明确超出覆盖的边界

### 索引

预估 6-7 条（按小节登记）。ID 形如 `host-diagnostics.ref.ifeo-hijack`。

`source` 指向 teardown 对应章节（该四项检测点继承自 aha_doctor 的系统环境检测子模块）。

### 验证

- [ ] `check_index.py` OK
- [ ] 每节可填满 § 0.4 判据模板
- [ ] 每条判据标注结论强度
- [ ] § 6 覆盖边界已写
- [ ] 领域版本升至 `0.2.0`，CHANGELOG 同步

---

## 任务 3：现象反查表（P1）

### 目标

产出 `reference/symptom-routing.md` —— 整个知识库的入口。

### 为什么依赖任务 2

反查表要指向具体判据。任务 2 完成后，"启动失败 → IFEO 劫持"这条路由才有落点。**其余路由先留占位**，在对应任务完成后回填（任务 11 收口时统一核对）。

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 如何使用本表 | 从现象出发，按命中率排序逐项排除 |
| 2 | 白屏 | 模块注入（D3D/DWM 干扰）→ 硬件加速开关 → GPU 驱动 → 渲染层降级 |
| 3 | 启动失败 | IFEO 劫持 → 安全软件隔离 → 文件完整性 → 依赖缺失 |
| 4 | 卡顿/卡死 | 模块注入 → CPU/内存/磁盘饱和 → 安全软件行为拦截 |
| 5 | 网络类现象 | 转 `network-layered-probe.md` 分层序列 |
| 6 | 崩溃 | 模块注入 → 系统崩溃记录 → **转 `dotnet-debugging`** |
| 7 | 多现象并发 | 优先级判断原则 |
| 8 | 本表覆盖边界 | 不在表内的现象如何处置 |

### 两个关键设计

**① § 2 的排序依据**：aha_doctor 官方文档明确「白屏/卡顿通常是部分第三方软件引起飞书功能异常」。模块注入是官方认定的头号故障源，排序据此。

**② § 6 是跨领域交接点**：一旦确认故障源在进程内部，本领域到此为止，转交 `dotnet-debugging`。**必须写清交接判据**——什么情况下该转、转过去查什么。这是防止两个领域重复覆盖的关键。

### 索引

预估 7-8 条。**注意**：知识库 README 规定「导航性标题不作为规则登记」，但本篇整体是判据性内容（现象→检测项的映射本身就是判断依据），按小节登记；仅 § 1「如何使用本表」是导航，**不登记**。

### 验证

- [ ] `check_index.py` OK
- [ ] § 6 交接判据明确
- [ ] 未完成任务的路由已标占位，任务 11 回填
- [ ] § 1 未登记索引
- [ ] 领域版本升至 `0.3.0`

---

## 任务 4：模块注入（P2）

### 目标

产出 `reference/module-injection.md` —— 本领域价值最高的一篇。

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 检测框架 | 枚举 → 验签 → 分类 → 判定 四步 |
| 2 | 可疑判定维度 | 签名状态、签名主体、文件路径、加载时机、是否在系统目录 |
| 3 | 注入手法识别 | AppInit_DLLs、SetWindowsHookEx 全局钩子、CreateRemoteThread、IFEO、DLL 劫持 |
| 4 | 常见注入源分类 | **按类别非产品**：安全软件 HIPS/沙箱、输入法、屏幕取词/翻译、录屏、远程控制、UI 增强外挂 |
| 5 | 对 WPF 宿主的特有影响 | D3D/DWM 干扰 → 白屏；消息钩子 → 输入异常；GDI 拦截 → 渲染错乱 |
| 6 | 排除法 | 如何确认某模块与现象**无关**（比误判为有关更重要） |
| 7 | 冲突名单的外置与维护 | 由使用方按故障回流积累，知识库不内置 |
| 8 | 本篇覆盖边界 | 判不了什么 |

### 核心约束（spec § 1.3 的落点）

⚠️ **本篇不得内嵌任何具体产品黑名单**。§ 4 按类别描述冲突形态，§ 7 说明名单外置方案。

理由：aha_doctor 的特征库是海量线上故障回流沉淀的产物，无法复制。硬编一份猜测的黑名单，比没有更糟——它会给出错误的确定性。

### 结论强度纪律

本篇多数判据只能给「推测」。"存在无签名第三方 DLL" ≠ "它导致了故障"。§ 6 排除法与结论强度标注在此尤其关键。

### 索引

预估 8-9 条。

### 验证

- [ ] `check_index.py` OK
- [ ] 全篇无具体产品名黑名单（`grep` 抽查常见安全软件名，应无命中）
- [ ] § 6 排除法已写
- [ ] 判据结论强度标注为「推测」者不少于「已确认」者
- [ ] 领域版本升至 `0.4.0`

---

## 任务 5：网络分层（P3）

### 目标

产出 `reference/network-layered-probe.md`。

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 分层排查序列 | 本机 IP → DNS 配置 → hosts → 代理 → LSP → 域名可达性 → 延迟/丢包 → 下载测速 |
| 2 | 每层判据与典型异常形态 | 逐层给判定条件 |
| 3 | hosts 篡改识别 | 文件位置、正常内容、篡改形态 |
| 4 | 代理检测 | 系统代理 / PAC / per-app 代理的差异与各自读取方式 |
| 5 | LSP 与命名空间提供者异常 | 分层服务提供者的正常链与异常形态 |
| 6 | 错误码映射表 | .NET 侧：`SocketError` / `WebExceptionStatus` / WinHTTP 错误码 → 处置建议 |
| 7 | 域名可达性 ≠ 能上网 | 宿主服务域名与通用连通性的区别 |
| 8 | 本篇覆盖边界 | 判不了什么 |

### 两处继承说明

**① § 1 的序列**直接继承 aha_doctor 的网络检测分区顺序——从本机配置向外逐层排除，方向正确。

**② § 6 对应** aha_doctor 的 80+ 条 Chromium net error code 映射表。**但 C# 侧须换成 .NET 错误码体系**，映射关系需自建——这是本篇工作量最大的一节，不可直接抄。

### 索引

预估 8-9 条。

### 验证

- [ ] `check_index.py` OK
- [ ] § 6 映射表为 .NET 错误码，非 Chromium 码
- [ ] § 1 序列每层均有对应判据小节
- [ ] 领域版本升至 `0.5.0`

---

## 任务 6：rules 三篇（P4）

### 目标

产出 `rules/01-diagnostic-safety.md`、`02-evidence-standards.md`、`03-conclusion-strength.md`。

### 为什么排在 P1-P3 之后

rules 是对内容的约束。先有 reference 实体内容，才知道该约束什么；反过来先写 rules 容易写成空泛原则。

### 本任务须建 `rules/` 目录

这是首次产生 rules 内容，此时建目录符合「不预建空目录」。同时更新 `catalog.json` 的 `categories` 为 `["rules", "reference"]`。

### 内容（照 spec § 4，此处只列级别与 enforcement）

**`01-diagnostic-safety.md`**

| § | 标题 | level | enforcement |
|---|---|---|---|
| 1 | 只读优先 | MUST | review |
| 2 | 写操作的确认与回滚 | MUST | review |
| 3 | 提权最小化 | MUST | review |
| 4 | 采集数据的密级 | MUST | review |
| 5 | 禁止进程内注入 | SHOULD | review |

**`02-evidence-standards.md`**

| § | 标题 | level | enforcement |
|---|---|---|---|
| 1 | 原始输出优先 | MUST | review |
| 2 | 采样而非瞬时值 | MUST | review |
| 3 | 故障机器上的降级 | MUST | review |
| 4 | 时间窗口对齐 | SHOULD | review |
| 5 | 环境基线 | SHOULD | advisory |

**`03-conclusion-strength.md`**

| § | 标题 | level | enforcement |
|---|---|---|---|
| 1 | 三档结论强度 | MUST | review |
| 2 | 相关性不等于因果 | MUST | review |
| 3 | 超出覆盖必须显式声明 | MUST | review |
| 4 | 风险计数不是故障计数 | SHOULD | review |

### enforcement 全 review 的理由（须在 README 说明）

按知识库 README 的操作性检验「工具判的是该小节的实质，还是只是它的外壳」——本领域三类规则（诊断安全、取证质量、结论强度）都需人工判断意图与内容，无法静态判定。

⚠️ **不得为凑分布强标 `ci`**。唯一可能标 `ci` 的是"诊断产物须进 .gitignore"，若单独成节再议。

### source 字段

⚠️ **校验器会验证 `source` 的目标文件与锚点真实存在**（`check_source_refs`）。`dotnet-probing-techniques.md` 在任务 9 才产出，因此本任务**不得**直接写指向它的锚点——会直接报错。

本任务先写：

- `01 § 5 禁止进程内注入` → `["reference/aha-doctor-teardown.md"]`（整篇，无锚点）
- `02 § 3 故障机器上的降级` → `["reference/aha-doctor-teardown.md"]`

任务 9 完成后回填为精确锚点（见任务 9「source 回填」）。

⚠️ **`source` 不得指向 teardown 中【推断】标记的内容**。teardown 整篇引用不涉及此问题（指向整篇而非某推断小节），但任务 9 回填精确锚点时须核对。

### 索引

14 条（5+5+4）。全部须填五个字段：`enforcement`、`status`、`applies_to`、`reviewed_at`、`owner`。

### 验证

- [ ] `check_index.py` OK
- [ ] `catalog.json` categories 已更新为 `["rules", "reference"]`
- [ ] 14 条 rule 五字段无遗漏
- [ ] 无 `level: MAY` + `enforcement: ci` 组合（脚本会报错）
- [ ] `source` 均指向**已存在**的文件与锚点
- [ ] 领域版本升至 `0.6.0`

---

## 任务 7：安全软件（P5）

### 目标

产出 `reference/security-software.md`。

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 检测面 | AV 产品清单、防火墙三 profile（域/专用/公用）、WFP 过滤器 |
| 2 | 拦截现象映射 | 文件隔离 → 启动失败；网络拦截 → 连接超时；行为拦截 → 卡死/操作失败 |
| 3 | SecurityCenter2 的能力与局限 | 能列产品，**不能判它拦了什么** |
| 4 | 处置建议排序 | 加白名单 > 临时禁用 > 卸载 |
| 5 | 企业管控环境的特殊性 | 策略下发的安全软件用户无权改 |
| 6 | 本篇覆盖边界 | 判不了什么 |

### 两处说明

**§ 3 是本篇最重要的一节**：WMI `SecurityCenter2` 只能告诉你装了什么，无法告诉你它拦截了哪个操作。**不得由"装了 X 且现象为 Y"推出"X 导致 Y"**——这正是 `rules/03 § 2 相关性不等于因果` 约束的典型场景。

**§ 4 排序**来自 aha_doctor 官方文档：「将飞书添加至安全类软件的白名单，或者退出/卸载相关软件」。

### 索引

预估 6 条。

### 验证

- [ ] `check_index.py` OK
- [ ] § 3 明确写出"不能判它拦了什么"
- [ ] 全篇无具体安全软件产品黑名单
- [ ] 领域版本升至 `0.7.0`

---

## 任务 8：硬件阈值（P5）

### 目标

产出 `reference/hardware-thresholds.md`。

### ⚠️ 本任务含一个延后项：阈值定值依据

**问题**：aha_doctor 的阈值内置于二进制，静态分析读不到。本知识库的阈值须自定。

**处置策略**（spec § 9 第 5 项的落实）：

1. **§ 1 先立"阈值是可调参数"这条元规则**——阈值不是硬判据，须记录定值依据与校准状态
2. **采用行业通用值作为初值**，每条注明来源（微软文档、通用运维经验、或"经验值"）
3. **全部标注 `待实测校准`**，并说明校准方法（在目标环境采集正常机器基线对比）
4. **禁止给出无依据的精确数字**——"CPU > 87.3%"这类伪精确比"CPU 持续高位"更糟

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 阈值的性质 | 可调参数而非硬判据；须记录定值依据与校准状态 |
| 2 | CPU | 使用率 + **持续时长**的联合判据（瞬时高位无意义） |
| 3 | 内存 | 物理可用量、提交量、虚拟内存配置 |
| 4 | 磁盘 | 使用率、剩余容量、队列长度、SSD/HDD 判定 |
| 5 | GPU | 使用率、硬件加速开关、渲染层级 |
| 6 | CPU 型号兼容性 | 指令集要求 |
| 7 | 阈值校准方法 | 如何在目标环境采基线 |
| 8 | 本篇覆盖边界 | 判不了什么 |

### 与 `rules/02 § 2 采样而非瞬时值` 的联动

本篇全部阈值判据须体现"多次采样"要求，§ 2 的"使用率 + 持续时长"是该规则的具体落地。

### 索引

预估 7-8 条。

### 验证

- [ ] `check_index.py` OK
- [ ] 每个阈值均标注定值依据与 `待实测校准`
- [ ] 无伪精确数字
- [ ] § 1 元规则已立
- [ ] 领域版本升至 `0.8.0`

---

## 任务 9：C# 取证手段（P6）

### 目标

产出 `reference/dotnet-probing-techniques.md` —— 实现约束层。

### 为什么单列一篇

前八篇是诊断理论（稳定），本篇是实现手段（随 .NET 版本变）。混在一起会让理论条目跟着实现细节反复改版。

### 内容清单

| § | 标题 | 要点 |
|---|---|---|
| 1 | 取证手段总表 | 检测项 → C# 路径 → 是否需 P/Invoke → **框架差异** |
| 2 | WMI 的权衡 | 最顺手但故障机器上可能挂住；主用 + 超时保护 + P/Invoke 兜底 |
| 3 | 必须 P/Invoke 的项 | `wintrust`/`crypt32` 验签、`fwpuclnt` WFP、`WSCEnumProtocols` LSP、`WinHttpGetIEProxyConfigForCurrentUser` 代理 |
| 4 | 托管封装够用的项 | `Ping`、`NetworkInterface`、`Registry`、`Process.Modules` |
| 5 | 性能计数 | `PerformanceCounter` 在 .NET Core+ 与 Framework 的行为差异 |
| 6 | ETW 与 hook 的取舍 | `TraceEvent` 库适用性与 GC 压力；何时改调 `wpr.exe`；**为什么不用 hook** |
| 7 | 外部工具编排 | `wpr.exe`（Win10+ 内置，免分发）vs `xperf.exe`（需分发） |
| 8 | 发布形态约束 | 自包含 + 单文件；AOT 与 P/Invoke/反射的兼容性 |
| 9 | 本篇覆盖边界 | — |

### 双目标框架分化（本任务特有）

⚠️ **本篇是唯一需要按框架分化的一篇**。目标：.NET 8+ **且** .NET Framework 4.6.2+。

须逐项标注差异，重点：

| 项 | 差异 |
|---|---|
| `PerformanceCounter` | Framework 完整支持；.NET Core+ 部分场景行为不同 |
| `System.Management`（WMI） | Framework 内置；.NET Core+ 需 NuGet 包且仅 Windows |
| `TraceEvent` | 两者均可用，但 API 面有差异 |
| AOT / 单文件 | 仅 .NET 8+ 可用，Framework 无对应能力 |
| P/Invoke 编组 | 基本一致，但 `SafeHandle` 与 `Marshal` 部分 API 有差异 |

**`applies_to` 字段在本篇须按条分化**——只适用于一个框架的条目不得标全集。这是全领域唯一的例外。

### source 回填

本任务完成后，回填任务 6 中两条 rule 的 `source`：

- `01 § 5 禁止进程内注入` → `["reference/dotnet-probing-techniques.md#6. ETW 与 hook 的取舍"]`
- `02 § 3 故障机器上的降级` → `["reference/dotnet-probing-techniques.md#2. WMI 的权衡"]`

### 索引

预估 9-10 条。

### 验证

- [ ] `check_index.py` OK（`source` 锚点存在性由脚本校验）
- [ ] 框架差异逐项标注
- [ ] 按条分化的 `applies_to` 正确
- [ ] 任务 6 的两条 `source` 已回填
- [ ] 领域版本升至 `0.9.0`

---

## 任务 10：VDI 环境（P7，可选）

### ⚠️ 执行前须用户拍板

**这是 spec § 9 第 4 项延后项。**

**判断依据**：目标用户是否有虚拟桌面部署场景？

- **有** → 执行本任务
- **无 / 不确定** → **跳过**，在领域 README 的「本领域不覆盖」中记一行，说明 VDI 判据未收录及原因

⚠️ **不确定时默认跳过**。建一篇无人消费的 reference，比缺一篇更糟——它会进入覆盖率统计与维护负担，却从不被检索。

### 内容清单（若执行）

| § | 标题 | 要点 |
|---|---|---|
| 1 | VDI 环境识别 | 如何判定当前运行在虚拟桌面中 |
| 2 | 磁盘读取速度判据 | VDI 常见瓶颈；与物理机阈值的差异 |
| 3 | 传输协议与图形性能 | 协议类型对渲染表现的影响 |
| 4 | VDI 下哪些常规判据失效 | **本篇最有价值的一节** |
| 5 | 本篇覆盖边界 | — |

### § 4 为什么最重要

VDI 环境下，任务 8 的硬件阈值、任务 4 的 GPU 相关判据大多失效——虚拟化层的存在使物理机经验不成立。若不写清这点，前面几篇的判据会在 VDI 上给出系统性错误结论。

### 索引

预估 4-5 条。

### 验证

- [ ] 用户已确认需要本任务
- [ ] `check_index.py` OK
- [ ] § 4 明确列出哪些既有判据在 VDI 下失效
- [ ] 领域版本升至 `0.10.0`

---

## 任务 11：收口验收

### 目标

全领域一致性验收 + 反查表回填 + 配套 skill 评估。

### 11.1 反查表回填

任务 3 建表时部分路由留了占位，此处统一回填并核对：

- [ ] 每条路由指向的目标文件与章节真实存在
- [ ] 无孤儿路由（指向未建文件）
- [ ] 无孤儿判据（reference 中的判据未被任何路由指向 → 说明反查表有缺口）

### 11.2 全领域一致性

```bash
python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" host-diagnostics --audit
```

- [ ] `check_index.py` OK
- [ ] `--audit` 覆盖率合理（**不追求 100%**，见知识库 README § 覆盖率不追求 100%）
- [ ] 无孤儿文件
- [ ] README 文件地图与实际文件一致
- [ ] 版本升至 `1.0.0`（领域首个稳定版），CHANGELOG 汇总

### 11.3 spec 验收标准逐条核对

照 spec § 8.2：

- [ ] 每条 reference 判据可对应到具体可采集的证据
- [ ] 每条判据标注了结论强度
- [ ] 明确记录了超出覆盖的边界（每篇 § 末尾）
- [ ] 硬件阈值全部标为可调参数并记录依据
- [ ] 无任何条目内嵌具体产品黑名单
- [ ] 与 `dotnet-debugging` 零重复：**抽查 5 条**，确认无同一事实两处登记
- [ ] teardown 中【推断】内容未被任何 `source` 引用

### 11.3.1 删除原分析文档（推迟自任务 1）

⚠️ 不可逆操作，前置条件全部满足后才执行：

```bash
grep -rn "aha-doctor-analysis" --include="*.md" .   # 须无输出（本计划与 spec 中的引用须先更新）
```

- [ ] teardown 已通过 11.3 全部验收
- [ ] 无任何文档引用 `docs/aha-doctor-analysis.md` 路径
- [ ] 删除 `docs/aha-doctor-analysis.md`
- [ ] 删除后再跑一次 `check_index.py` 确认 OK

### 11.4 配套 skill 评估（延后项 3）

**这是 spec § 9 第 6 项。本任务只做评估，不实施。**

按 AGENTS.md 自检要求回答三个问题，结论写入领域 README 或另开 spec：

1. 本知识库是「传感器」（判据/校验），`symptom-routing.md` 是「引导器」——两半是否已配齐？
2. 是否需要一个 skill 把判据编排成完整排查流程（类比 `dotnet-diagnose-triage`）？
3. 若需要，它属于哪个插件？与既有 `dotnet-diagnose-triage` 的边界如何划？

**产出**：一份「需要 / 不需要 / 待工具形态明确后再定」的结论 + 理由。**不在本计划内实施 skill 开发。**

### 11.5 提交

全部任务完成后，用 `commit-cc-plugin` skill 提交。

---

## 附录 A：回滚方案

| 任务 | 回滚方式 |
|---|---|
| 1 | 删除 `knowledge-base/host-diagnostics/`、还原 `catalog.json`；⚠️ `docs/aha-doctor-analysis.md` **无法从 git 恢复**，见下 |
| 2-10 | 删除对应文件、回退 index.jsonl 相关行、回退版本号与 CHANGELOG |

### ⚠️ 任务 1 的删除动作不可逆

**已核实（2026-09-06）**：`docs/aha-doctor-analysis.md` 在 git 中状态为 `??`（未跟踪），**从未提交过**。这意味着：

- `git checkout` / `git restore` **均无法恢复它**
- 一旦删除且迁入内容有误，原分析内容永久丢失

**因此任务 1.7 的执行顺序是强制的**：

1. 先完成 1.4（迁入 `reference/aha-doctor-teardown.md` 并做四处改造）
2. 逐节比对，确认除"能否改配置"一节（有意移除）外内容完整
3. 确认 `check_index.py` OK
4. **最后**才删除 `docs/aha-doctor-analysis.md`

**更稳妥的做法**：任务 1 先不删，把删除动作推迟到任务 11 收口——届时全领域已验证，且中间任务若发现 teardown 有缺漏还能从原文件补。代价是中间阶段两份并存，但 `docs/` 下的文件不进索引、不影响校验。

**建议采用推迟方案**，任务 1 的验收项相应改为「原文件保留待任务 11 删除」。

---

## 附录 B：风险与对策

| 风险 | 影响 | 对策 |
|---|---|---|
| 判据写成概念介绍 | 知识库不可用于实际判断 | § 0.4 模板逐条检验；填不满即重写 |
| 与 `dotnet-debugging` 重复 | 检索互相干扰 | 任务 3 § 6 明确交接判据；任务 11 抽查 5 条 |
| 硬件阈值变成魔数 | 判据不可解释、无法校准 | 任务 8 § 1 先立元规则；全部标 `待实测校准` |
| 内嵌产品黑名单 | 给出错误的确定性 | 任务 4 § 7 名单外置；验证时 grep 抽查 |
| 把【推断】当判据 | 知识库根基不实 | teardown 补「不可引用部分」小节；`source` 校验 |
| 覆盖率被当 KPI 追平 | 产生坏条目 | 任务 11 明确"不追求 100%"；引用知识库 README 三类不登记情形 |
| VDI 篇无人消费 | 维护负担 | 任务 10 执行前拍板；不确定则跳过 |

---

## 附录 C：延后项索引

spec § 9 的三个 ⏳ 在本计划中的落点：

| Spec 延后项 | 落点 | 处置 |
|---|---|---|
| VDI 是否需要 | 任务 10 | 执行前用户拍板；不确定则跳过并在 README 记录 |
| 硬件阈值定值依据 | 任务 8 | 行业通用值 + 全部标 `待实测校准` + § 1 立元规则 |
| 是否配套建 skill | 任务 11.4 | 只评估不实施，产出结论与理由 |