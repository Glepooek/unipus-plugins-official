---
paths:
  - "**/SKILL.md"
---

> 文档类规范（编辑铁律、CHANGELOG.md、README.md）见 `.claude/rules/doc-conventions.md`；agent 规范见 `.claude/rules/agent-conventions.md`。本篇只承载 SKILL.md 自身的约定。

## Skill frontmatter 规范

**通用规范见 `knowledge-base/skill-authoring/`**——SKILL.md 格式（六字段约束、目录结构、progressive disclosure、文件引用）见 `rules/01-skill-format.md`；描述优化见 `rules/02-description-optimization.md`；质量评估见 `rules/03-skill-evaluation.md`；脚本使用见 `rules/04-script-usage.md`；最佳实践见 `rules/05-best-practices.md`。本篇只承载**本仓库专属约定**。

每个 skill 维护**独立的语义版本**，与仓库 marketplace 版本号分开管理。frontmatter 遵循开放 Agent Skills 规范（agentskills.io），只允许 `name`/`description`/`license`/`compatibility`/`metadata`/`allowed-tools` 六个顶层字段（各字段约束见 `knowledge-base/skill-authoring/rules/01-skill-format.md`），出现其他顶层字段会导致跨 runtime 严格校验器报"Unexpected fields in frontmatter"错误。

### metadata.version

新增或修改 skill 时，必须同步更新 SKILL.md frontmatter 中 `metadata.version` 字段：

| 变更类型 | Skill 版本升级 |
|---|---|
| 新增功能、新增章节、新增参数 | **Minor** `x.X.x` |
| 修改/修复已有内容、文档优化、重构 | **Patch** `x.x.X` |
| 破坏性变更（接口不兼容、删除用户可见功能） | **Major** `X.x.x` |

版本号放在 `metadata` 下而非顶层，是为了兼容上述开放规范。

### metadata.author

所有 skill 统一署名：

```yaml
metadata:
  author: desktop client team
```

### metadata.category

标注该 skill 的工作形态，用于跨插件横向检索（与插件归属的领域分类正交，插件回答"属于哪个业务领域"，category 回答"是什么形状的工作"）。可选字段，取值：

| 取值 | 适用场景 |
|---|---|
| workflow | 流程编排类（多阶段、pipeline、交接式工作流） |
| quality | 质量保障类（review、评分、一致性校验、性能诊断） |
| generator | 代码/文档生成类（创建 PRD、代码、测试用例、报告等产物） |
| tool | 工具类（格式转换、数据同步、CI 触发、脚本初始化等） |
| platform | 平台专项类（如未来出现 android/ios/harmony 专属 skill） |
| decision | 决策支持类（给出选型结论/适用性判断/权衡依据，不产出代码或文件，落地实现留给人工接手） |

### compatibility

一句话描述运行环境依赖（≤500字符），必须基于该 skill 实际用到的工具/依赖据实填写，不得凭空编造。常见依赖类型：语言运行时（Python/Node.js/.NET SDK）、第三方 CLI（lark-cli、JMeter）、MCP server——引用 MCP server 时须注明是本仓库 `plugins/optimus-mcp-servers/.mcp.json` 内置（如 `mastergo-magic-mcp`、`FeishuProjectMcp`）还是需要用户自行配置（如 Figma/Sketch/Chrome DevTools MCP）。

### allowed-tools

空格分隔的预授权工具列表，必须基于该 skill 实际调用的工具据实填写：
- Claude Code 内置工具写原名（如 `Read Write Bash Grep Glob WebFetch TodoWrite Task`）
- MCP 工具只写 server 命名空间，不精确到具体工具全名，避免 MCP server 改名/升级后 allowed-tools 跟着失效
- 会派发子代理或调用其他 skill 的技能必须包含 `Task`

```yaml
---
name: my-skill
description: ...
metadata:
  version: "1.2.0"
  author: desktop client team
  category: workflow
compatibility: 需要 Node.js 环境及已配置的 XXX MCP server。
allowed-tools: Read Write Bash Task
---
```

## 执行前置校验

skill 正式执行任务前（进入具体业务 Step 之前），必须先做以下四类检查——但每类检查仅在该 skill 确实存在可检查的对应项时才要求，没有文件输入/输出、没有声明 `compatibility` 的 skill（如纯对话编排类）不必为不适用的类别写占位说明。

前置校验作为独立 Step 呈现（如"Step 1：确认环境"承担依赖检查，或单独的"Step N：执行前校验"承担运行条件检查），不要混入 SKILL.md 的"失败处理"章节——失败处理记录的是**执行中**才会暴露的报错，前置校验是**执行前**的主动探测。

### 四类检查项

| # | 类别 | 检查内容 | 适用条件 |
|---|---|---|---|
| 1 | 依赖检查 | `compatibility` 字段中声明的运行时/CLI/MCP server 等依赖是否已就绪 | frontmatter 声明了 `compatibility` |
| 2 | 输入参数检查 | 输入文件/路径是否存在、格式是否符合预期 | 接收文件路径类输入 |
| 3 | 输出参数检查 | 输出路径的**父目录**是否存在且可写；不检查输出文件本身是否存在——未生成前不存在是正常状态，文件已存在时的覆盖策略由各 skill 自行处理（如 `-y`/`-n`），不属于前置校验范畴 | 会写入文件 |
| 4 | 运行条件检查 | 与业务逻辑强相关的前提条件（如目标分辨率、时间范围是否落在合法区间内） | 核心操作存在此类前提 |

### 运行条件检查的分类：硬约束 vs 可协商风险

第4类不能一律报错终止，需先判断性质：

| 性质 | 判断标准 | 处理方式 | 示例 |
|---|---|---|---|
| **硬约束** | 违反后操作在逻辑/物理上无法执行或产出无意义结果，用户确认也无法绕过 | 检查失败 → 报错终止 | 起始时间超过视频总时长；目标格式与源文件容器不兼容 |
| **可协商风险** | 技术上可以执行，只是带来质量/效果上的妥协，用户知情后可自行决定是否接受 | 检查失败 → 🔴 CHECKPOINT 显式确认，用户同意后继续执行，不算任务失败 | 放大分辨率导致画质损失；宽高比不一致导致画面拉伸 |

不确定某个运行条件属于哪一类时，默认按"可协商风险"处理并加 CHECKPOINT——把可协商的风险误判为硬约束，会导致 skill 过度拒绝用户已明确知情仍想执行的操作。

类别1-3（依赖/输入/输出）不适用本分类，检查失败一律报错终止——这三类是执行的物理前提，不存在"用户确认后仍可继续"的空间。

## 需求预告：执行前一次性告知，而非逐步反应式发现

四类检查默认在**执行到对应 Step 时**才触发——若用户的触发语句缺了必要信息（如未给输入文件、未指定目标参数），会导致逐步卡在某个 Step 才反过来追问，多轮来回才能凑齐信息。这是执行时的正确性保障，不是执行前的可发现性保障，两者要分开满足。

skill 处理用户请求的**第一步**，必须先对比"该 skill 需要哪些信息"与"用户已在触发语句或上下文中提供了哪些"，一次性列出缺失项统一询问，不要逐个 Step 卡顿式追问：

- **依赖检查项不参与本环节的比对**：依赖是否具备（如 ffmpeg 是否安装）是系统状态，不是用户能在触发语句里主动提供的信息，不得作为"缺失项"询问用户，也不计入"信息是否齐全"的判定——依赖状态只能靠 Step 1 类的实际检测确认，需要时可在预告中作提示性说明（如"执行时会自动检测 ffmpeg 环境"），但不构成阻塞或询问理由
- **仅对用户可提供的信息做齐全性比对**：输入侧信息（文件路径等）、输出信息（保存位置）、运行条件参数（如目标分辨率、目标时间段）——这些是用户能够、也应当在触发语句或上下文中给出的信息，才纳入"缺失项"判断范围
- 用户已在触发语句或上下文中明确提供的项，**不得**重复询问——只问真正缺失的部分。判断"是否已提供"依据当前对话上下文，不要求用户复述已说过的内容
- 若用户可提供的信息已经齐全，跳过预告，直接进入 Step 1 正常执行——依赖检查项不计入此判断，不会导致"信息永远不齐全"
- 预告环节不做实际系统调用（不检测依赖是否真的安装、不检测文件是否真的存在）——这些仍由四类检查项在对应 Step 中完成；预告只做"信息是否齐全"的静态比对

## Skill 持续优化的强制约定

完整机制（创建后基线评估、`known-issues.md` 格式、累积阈值触发优化、与 darwin-skill 的现实边界）见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`，本篇只说明本仓库的落地范围。

**适用范围**：本约定自 2026-08-30 生效起，适用于此后**新建**的 skill。已有 skill 的回填按"先试点、验证后推广"分阶段进行——当前处于试点阶段（见下），试点结果确认可行后再推广至全仓库其余插件；本次生效**不代表**尚未回填 `known-issues.md` 的其他现有 skill 立即被判定为不合规。

**当前试点范围**：`plugins/optimus-decision-plugin/` 的 8 个 skill；`.claude/skills/`（除自身不受仓库版本管辖的 `darwin-skill/` 外）的 `commit-cc-plugin`、`knowledge-base-maintain`、`record-tools`、`sync-cc-docs-to-youdaonote`、`sync-cc-tips`、`test-locally` 共 6 个 skill。
