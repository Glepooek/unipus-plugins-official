---
name: sync-cc-tips
description: 从 Claude Code 最新 changelog 自动同步 tips.jsonl：新增未覆盖条目、修正过时内容、删除已废弃功能，同步所有文档数字，最后调用 commit-cc-plugin 提交。触发场景：用户说 "/sync-cc-tips"、"更新tips"、"同步tips"、"tips需要更新"、"从changelog更新tips"、"sync tips"。可附带版本数量参数，如 "/sync-cc-tips 5" 表示只看最近5个版本。
metadata:
  version: "1.5.0"
  author: desktop client team
compatibility: 需要网络访问 raw.githubusercontent.com 拉取 changelog；第二步调用 scripts/ 下两个 Python 脚本（标准库，无第三方依赖）；流程末尾调用 commit-cc-plugin skill 完成提交推送。
allowed-tools: Bash WebFetch Read Edit Task
disable-model-invocation: true
---

# /sync-cc-tips

从 Claude Code 最新 changelog 全自动同步 tips.jsonl，无需人工干预，完成后展示摘要并提交。

## 第一步 — 抓取 changelog

**读取同步锚点：**

```bash
if [ -f .claude/skills/sync-cc-tips/.last-synced-version ]; then
  anchor=$(cat .claude/skills/sync-cc-tips/.last-synced-version)
else
  anchor=""
fi
```

- 文件不存在（首次运行）→ `anchor` 为空，回退到「最新 10 个版本」默认窗口（见下方兜底逻辑）
- 文件存在 → `anchor` 为上次同步到的版本号（如 `2.1.224`），用于下方 awk 截断

直接读取仓库根目录的 `CHANGELOG.md`（纯 Markdown 文本源头，按版本从新到旧排列，无需处理页面折叠块或 JS 渲染，比 releases 页面更完整可靠）。

**按顺序执行，命中即停，不要跳步：**
1. 若 `anchor` 非空，用 awk 管道截断到锚点为止（命中即停，锚点版本本身不含在输出中，因为已在上次同步中处理过）：
   ```bash
   curl -s --max-time 15 https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md \
     | awk -v anchor="## $anchor" '/^## /{ if ($0 == anchor) exit } { print }'
   ```
   若 `anchor` 为空（首次运行），改用无截断的完整抓取，后续按「最新 10 个版本」处理：
   ```bash
   curl -s --max-time 15 https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
   ```
2. 若步骤 1 失败（超时 / 连接被拒绝）→ 输出 `⚠️ curl 不可达，降级为 WebFetch`，改为 `WebFetch: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`（WebFetch 抓取完整内容后，锚点截断改为在读取到的文本上用相同的"遇到 `## {anchor}` 停止"规则人工执行，不依赖 awk）
3. 若步骤 2 也失败 → 等待 2 秒，重试一次步骤 1（同一条命令，不再等待更久）
4. 若步骤 3 仍失败 → **停止整个流程**，报告网络不可达（curl 与 WebFetch 均无法访问），不执行任何写入操作

**成功拿到内容后：**
- 文件中每个版本以 `## {版本号}` 标记（如 `## 2.1.197`），紧随其后为该版本的完整 bullet 列表
- 若 `anchor` 非空：awk 截断后的全部输出即为待处理版本（数量不固定，取决于锚点距今发布了多少个版本）
- 若 `anchor` 为空（首次运行）：提取最靠前（最新）的 **10 个版本**段落作为默认窗口
- 记录版本范围（如 v2.1.183 → v2.1.197），用于摘要展示

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| CHANGELOG.md 内容为空或找不到 `##` 版本标记 | 确认 URL 是否正确（分支名可能变更） | 停止流程，报告解析失败 |
| 锚点版本在 changelog 中找不到（相隔太久，CHANGELOG.md 只保留近期版本，锚点已被滚出文件） | awk 跑到文件末尾都没 exit，等于输出了全部可见内容——检测输出的版本数（`grep -c '^## '`），若 > 30 | 通过 `AskUserQuestion` 询问「距离上次同步已超过 30 个版本，changelog 中未找到锚点版本 v{anchor}，是否继续处理全部可见的 {N} 个版本？」，选项：「继续处理全部可见版本」（推荐）／「取消，我需要先确认是否漏看了历史内容」；选后者立即停止整个流程 |
| awk 截断后输出为空（锚点就是最新版本，无新版本可处理） | 直接判定为 0 新版本 | 等同于触发下方「🚦零变更总闸」，跳过后续所有步骤 |
| 用户传入 `/sync-cc-tips N` 参数 | 忽略锚点截断逻辑，改为无条件抓取完整 CHANGELOG.md 后只取最新 N 个版本段落 | 本次运行结束时**不更新** `.last-synced-version`（范围受限的临时查看，不代表真实同步进度，详见第五步） |

## 第二步 — 读取现有 tips.jsonl

> **黄金真源 = `tips.jsonl`**（单一真源：`show-tip.sh` 展示与 `sync-cc-tips` 同步均读写它）。每行一个 JSON 对象，字段 `{id, category, title, body}`。`id` 是稳定主键（命令名/flag/功能名），`body` 含真实换行的 `功能/效果/例子`。

**用脚本构建「已覆盖标识符集」（取代 grep 全文正则）：**

```bash
python .claude/skills/sync-cc-tips/scripts/build_alias_index.py
```

输出 JSON：`{"ids": [...], "aliases": [...], "stats": {"entries": N, "ids": N, "aliases": N}}`。

脚本只收录**带语法标记**的标识符——斜杠命令（含 `/plugin:skill` 命名空间）、长短 flag、大写环境变量——并做三类归一化：斜杠/双横前缀剥离、连字符与下划线互换、小写。此外内置 `SEMANTIC_ALIASES` 显式登记字面无关的等价组（`/cost`≡`/usage`≡`/stats`、`/review`≡`/code-review`、`/plugin`≡`/plugins`、`/undo`≡`/rewind`），这类别名归一化覆盖不到，必须硬编码。

> ⚠️ **不要改回收录裸英文词。** 曾用 `\b[a-z][a-zA-Z]{3,}\b` 把正文所有 4 字母以上小写词纳入 aliases，集合膨胀到数千个通用词（`effect`、`when`、`with`…），导致任何 changelog 功能点都能"命中"→ 判重恒为已覆盖、新增恒为 0。这是不报错的静默失效，`scripts/test_build_alias_index.py::TestExtractRejectsNoise` 已锁住该行为。斜杠命令模式同理带路径排除断言，否则 `.claude/settings.json` 的 `/settings` 会被当成命令。

执行后 `ids` / `aliases` 进入对话上下文供 Step 3 逐条查表，不落盘。

**覆盖判断基准**：一个 changelog 功能点的**任意一个主标识符**在 `ids`/`aliases` 中命中 → 视为已覆盖，不新增。**别名归一化解决了别名字面不同判不出的问题**（`/cost`≡`/usage`、`/review`≡`/code-review`、`/plugins`≡`/plugin`、`/undo`≡`/rewind` 这 4 组历史重复即因此产生）。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 文件不存在 / Read 报错 | 确认路径 `plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl` 是否正确 | 停止整个流程，报告路径错误，不做任何修改 |
| 文件存在但内容为空 | 🔴 CHECKPOINT：停下询问用户是否为全新初始化场景 | 若用户确认，继续（视为无旧条目）；否则停止 |
| 从 JSONL 提取的候选标识符里混入明显噪音 | 生成清单后做一次可读性清洗，剔除路径片段、通用英文单词等非真实标识符 | 若某一类别噪音过多难以人工清洗，仍以清洗后的清单为准，不因噪音多而放弃该类别的判重 |

### 辅助：库内残影检测（第二步执行）

判重是单向的（changelog → 已有条目），不检查**已有条目之间互相覆盖**。补齐：

```bash
python .claude/skills/sync-cc-tips/scripts/detect_residue.py
```

输出 JSON：`{"candidates": [{"covers": id, "covered": id, "overlap": 0.xx}], "shared_main": {...}, "stats": {...}}`。

召回需同时满足两条：主标识符相同（只有讲同一个东西才谈得上覆盖）+ `功能：` 段落的中文 bigram 集合达到阈值包含关系。

> ⚠️ **输出是待裁决候选，不是判定结果。** 实测 276 条库内的两两覆盖率分布显示，人工确认的真残影（`/doctor` 那两条互为详略版本）只有 **0.263**，而非残影的 `MCP-资源列出 ⊇ MCP-服务器` 却有 **0.333**——两类在数值上交叠，纯词频无法可靠区分。故阈值按召回定为 0.25，宁可多召回几个让人看，不可漏掉真残影。

发现残影候选在第四步变更预览中单独列出，建议合并/删除，交由用户在 CHECKPOINT 裁决。**不要让脚本或模型自行删除**。

## 第三步 — 三类差异识别

依次对 changelog 中每个功能点做判断：

### 📋 差异识别中间过程表（先于三类判定生成）

在做出新增/修改/删除判定之前，先按 changelog 每条 bullet 生成一行记录，汇总成一张表，覆盖窗口内**每一条** bullet（不只是最终判定为新增/修改的那些）：

| Bullet 摘要 | 提取的主标识符 | 命中情况 | 判定 |
|---|---|---|---|
| Added CLAUDE_CODE_PROJECT_DIR_NAME env var... | `CLAUDE_CODE_PROJECT_DIR_NAME` | 未命中 | 🆕 新增 |
| Fixed auto mode in very long sessions... | （无用户可操作标识符，纯 bug fix） | — | ⏭️ 跳过（非用户可操作功能） |
| Added GitLab merge request badge to footer... | `GitLab`, `footer`, `glab` | 命中已有「GitLab 支持扩展」条目 | ⏭️ 跳过（已覆盖，需修改） |

**判定归类为四种：**
- 🆕 新增（判定规则见下方「🆕 新增条件」）
- ✏️ 修改（判定规则见下方「✏️ 修改条件」）
- ⏭️ 跳过（已覆盖 / 非用户可操作功能，两种子原因均需在"命中情况"列写明）
- 🗑️ 删除（判定规则见下方「🗑️ 删除条件」，针对已有 tips 条目而非 changelog bullet，不在本表中逐条列出，单独处理）

跳过计数 = 本表中判定为「⏭️ 跳过」的行数，用于第六步摘要的完整性校验：changelog 窗口内共 M 条 bullet，新增 + 修改 + 跳过（不含针对已有条目的删除判定）应约等于 M，数量对不上说明本表本身有遗漏。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 一条 bullet 涉及多个可拆分的独立功能点（如一条 bullet 合并宣布两个不相关的新 flag） | 拆成两行分别判定 | 不强行捏合成一条 |
| bullet 数量很大（窗口跨度长，一次有 100+ 条） | 中间过程表仍逐条生成 | 不因数量大而抽样或省略——抽样等于放弃了这张表的完整性校验意义 |

### 🆕 新增条件
满足以下**全部条件**才生成新条目：
- 属于对用户操作有实质影响的功能（新 CLI flag、新子命令、新 Hook 事件、新 settings.json 设置项、新交互命令）
- 在 tips.jsonl **全文**中，该功能点的所有主标识符（flag 名、设置项名、命令名、环境变量名）在 `ids`/`aliases` 中均未命中
- **环境可用性门**：该功能在本机 harness 下确实能跑。mac/Linux-only、Enterprise 席位、cloud-SDK、claude.ai 账号等本机用不了的 → 标记 `⏭️ 跳过（本机不可用）`，不占坑

**识别流程**：
1. 提取该功能点的主标识符列表（如 `respondToBashCommands`、`!命令`）
2. 在 `ids`/`aliases` 中逐一查找
3. **任一命中 → 跳过，不新增**；全部未命中 → 标记为新增

**信息补全（生成前必须执行）**：
changelog 的单行描述往往只覆盖核心功能，生成前需补充完整信息：

1. **交叉关联已有 tips** — 在 tips.jsonl 全文中搜索与新功能相关的已有条目，提取可关联的信息：
   - 新功能是否与已有功能形成工作流？（如「可点击附件」与「@ 引用」配合）
   - 新功能是否涉及已有命令/flag？（如「可读会话名」涉及 `-n`、`/rename`、`--resume`）
   - 新功能是否属于已有配置项的子集或扩展？

2. **提取完整参数集** — 从 changelog 原文中提取：
   - settings.json 键名（camelCase 形式）
   - 环境变量名（全大写下划线形式）
   - 支持的值/选项（如 small/medium/large、true/false）
   - 是否为建议性指引（advisory）vs 硬性限制（enforced cap）
   - 相关 CLI flag 或交互命令

3. **补全用法示例** — 为每个功能点提供完整的使用方式：
   - CLI 命令必须是完整可执行形式：`claude --xxx`
   - 配置项需给出 settings.json 键名和示例值
   - 交互命令需给出触发方式和预期结果（`/xxx:yyy` 或注册来源）
   - 若有多种使用方式（CLI + 交互 + 配置），全部列出
   - **不写裸缩写 / 不可执行简称**：`/tdd`、`debugging`、`parallel-agents` 这类敲不出来、无处注册的标识符一律不得作为例子

**完整性校验（生成后必须执行）**：
生成条目后，对照检查以下清单，任一项缺失则补充：

| 检查项 | 要求 |
|--------|------|
| settings.json 键名 | 配置类功能必须包含 camelCase 键名 |
| 环境变量名 | 有环境变量的功能必须包含全大写形式 |
| 版本号 | 标注引入版本（如 v2.1.196） |
| 多种用法 | 有 CLI + 交互两种方式的，全部列出 |
| 关联功能 | 与已有 tips 有配合关系的，互相引用 |
| 限制说明 | advisory vs enforced、仅 -p 模式、仅特定平台等 |

生成格式（每条一行 JSON，写入 tips.jsonl）：
```json
{"id":"/xxx","category":"[分类]","title":"🔰 标题","body":"功能：一句话说明\n效果：使用场景和收益\n例子：claude --完整命令 具体说明"}
```
- `id` 取主标识符（命令名 / flag / 功能名），无主标识符用标题 slug，全库唯一
- `body` 内用真实换行（JSON 里为 `\n`）而非字面 `\n`
- 分类从现有分类中选最匹配：`[交互]`、`[工具]`、`[Hook]`、`[配置]`、`[CLI]`、`[集成]`、`[工作流与自动化]`、`[排障]`、`[Skill]`、`[MCP]`、`[高级]`、`[Skill·superpowers]`

### ✏️ 修改条件
以下情况原地更新已有条目（不改变条目位置）：
- 已有条目的命令语法与 changelog 不符（如 flag 名称变更）
- 已有条目描述的行为已被新版本改变
- 已有条目的例子中使用了已不存在的 flag 或子命令
- **不修改**：仅措辞差异、风格调整、无实质差异的改动

**修改即覆盖旧语义，不追加版本沿革**：同一条目只保留最新语义，不在 `body` 里逐版本累积"v2.1.196 新增…v2.1.220 改为…"这类历史。**长度自检**：修改后条目长度不超过全库条目长度中位数的 2 倍（超出说明在堆历史，应压缩为当前语义）。

### 🗑️ 删除条件
以下情况将在第四步变更预览时列出待删条目：
- changelog 明确标注 `Removed`、`Deprecated`、`no longer available`
- 功能已被完全移除（不是"有了更好的替代"，而是彻底消失）
- **不删除**：changelog 只是新增了替代功能，旧功能仍可用

### 格式校验（每条写入前执行）
- 必须是合法 JSON 单行，含 `id`/`category`/`title`/`body` 四字段
- `body` 必须包含"功能："、"效果："、"例子："三个字段。允许分平台拆成多行"例子（Windows）："、"例子（Linux/Mac）："——**校验时按行首 `例子` 判断，不要求 `例子` 与 `：` 紧邻**（曾因字面匹配 `例子：` 把 `--add-dir` 的括号后缀写法误判为缺字段）
- 例子中的可执行形式必须是以下**三种形态之一**，禁止裸缩写：
  1. CLI 完整命令：`claude --xxx`
  2. 斜杠命令：`/xxx`
  3. skill 名 + 完整触发形式：`/xxx:yyy` 或注明注册来源
- **如果校验不通过** → 修正后再写入，不跳过也不写入不合格条目；若无法修正则跳过该条并在摘要中注明

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| "完整性校验"清单某项在 changelog 原文中确实找不到对应信息（如未提供 settings.json 键名） | 交叉检索该功能关联的已有 tips 条目或同版本其他条目上下文推断 | 若仍无法确认，跳过该项校验并在摘要中注明"信息不全，需人工补充"，不编造数值 |
| 同一功能点同时命中🆕新增与✏️修改条件（如新 flag 替换了旧 flag 的部分行为） | 优先按✏️修改处理，原地更新旧条目，不重复新增 | 若归属仍有歧义，在变更预览中单独列出并说明歧义原因，交由用户在 CHECKPOINT 处裁决 |

### 🚦 零变更总闸（唯一判定点）
若本轮识别结果为 **0 新增 + 0 修改 + 0 删除**（包括全部 bullet 均判定为 ⏭️ 跳过的情况）→ 跳过 tips.jsonl 写入、跳过第四步 CHECKPOINT、跳过第五步文档数字同步，但**仍需推进 `.last-synced-version`** 到本轮处理到的最新版本并单独提交（commit message 注明"仅推进同步锚点，无 tips.jsonl 变更"），避免下次运行重新扫描这段已确认无实质变更的区间。仅输出「本次 changelog 检查完成，所有功能点已在 tips.jsonl 覆盖或非用户可操作，已推进同步锚点至 v{最新版本}」后结束。第四步、第六步中对"0 变化"的提及均以本节为准，不重复判断。

## 第四步 — 写入 tips.jsonl

> 🔴 **CHECKPOINT**（仅在变更数 > 0 时触发，0 变化场景见「🚦 零变更总闸」）：写入前展示变更预览——列出「📥 新增 N 条 / ✏️ 修改 N 条 / 🗑️ 删除 N 条 / ⏭️ 跳过 N 条」及每条标题，用 `AskUserQuestion` 发起确认：
> - `question`: "以上是本次识别到的变更（N 新增 / N 修改 / N 删除 / N 跳过），是否写入 tips.jsonl 并继续后续提交流程？"
> - `options`: 「确认写入并提交」（推荐）／「取消，不做任何修改」
> - 选「确认写入并提交」→ 继续执行写入和第五步数字同步
> - 选「取消，不做任何修改」或用户通过 Other 输入自定义文本（视为非明确同意） → **立即停止**，输出「操作已取消，tips.jsonl 未修改」，不执行任何写入或提交，`.last-synced-version` 也不更新

```
Edit: plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl
```

- **新增**：追加到文件末尾，每条为一行合法 JSON 对象
- **修改**：原地替换对应条目所在行，保持位置不变
- **删除**：移除对应条目所在行

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| Edit 工具报错（文件锁 / 权限不足） | 等待 2 秒后重试一次 | 停止流程，报告错误路径，不继续第五步 |
| 写入后读回内容与预期不符 | 重新执行 Edit | 停止流程，提示用户手动检查文件状态 |
| 删除条目后空行残留 | 再次定位并删除残留在行 | 在摘要中标注"空行可能残留，请人工确认" |

## 第五步 — 同步文档数字

统计写入后 tips.jsonl 的实际条目总数：**以 JSON 行数为准**（每条 tip 一行 JSON 对象，主计数方式），**不要在任何计数上加 1**。

本文件为 JSONL 格式，**每条 tip 独占一行**，没有 `---` 分隔符（那是旧 `tips.txt` 的格式）。条目数 = 非空行数。

```bash
f=plugins/optimus-devops-plugin/hooks/sessionstart/tips.jsonl
grep -c '^{' "$f"      # 条目数（主计数，每行一个 JSON 对象）
wc -l "$f"              # 行数（应与上面相等；文件末尾无空行时两者一致）
```

行数不一致或有空行说明格式有破损，回到第四步修复后重新计数。另可用「旧条目数 + 新增 − 删除」做第三重校验，三者应一致。

**共 6 处含条目总数**，逐一将旧数字替换为新总数。⚠️ **下表是已知同步点，不是权威清单——务必以下方全仓库扫描结果为准**（该清单曾两轮漏项，2→4→6 处；经过见 `known-issues.md`）。扫描发现表外命中时，先补表再改数字：

| 文件 | 位置 | 形式 |
|---|---|---|
| `.claude-plugin/marketplace.json` | `optimus-devops-plugin` 的 `description` | `SessionStart（N条技巧智能轮播）` |
| `plugins/optimus-devops-plugin/hooks/README.md` | 「技巧分类」小节首行 | `tips.jsonl 包含 N 条技巧，涵盖以下分类：` |
| `plugins/optimus-devops-plugin/.codex-plugin/plugin.json` | `interface.longDescription` | `SessionStart（N条技巧智能轮播）` |
| `.kiro/steering/plugins.md` | devops 插件文件清单中的 tips.jsonl 行 | `` - `hooks/sessionstart/tips.jsonl` — N条技巧库 `` |
| `.kiro/steering/structure.md` | 「关键文件」表中的 tips.jsonl 行 | `` \| `plugins/.../tips.jsonl` \| N 条使用技巧 \| `` |
| `.kiro/steering/product.md` | 「智能会话增强」条 | `N条使用技巧自动轮播` |

先用一条命令定位全部候选，再按下表甄别，避免误改：

```bash
# Bash — 全仓库扫，避免遗漏未收录的新同步点
# 用 '条.*技巧' 而非 '条技巧'：structure.md 写的是「N 条使用技巧」，中间插了字
grep -rnE '条[^，。|]*技巧' --include='*.json' --include='*.md' . | grep -vE 'sync-cc-tips/(SKILL|CHANGELOG)\.md'
```

```powershell
# PowerShell（本机默认 shell，无 grep）——分文件输出以区分两个同名 README.md
foreach ($f in @('.claude-plugin/marketplace.json','README.md','plugins/optimus-devops-plugin/hooks/README.md','plugins/optimus-devops-plugin/.codex-plugin/plugin.json','.kiro/steering/plugins.md','.kiro/steering/structure.md','.kiro/steering/product.md')) {
  Write-Output "=== $f ==="
  Select-String -Path $f -Pattern '条[^，。|]*技巧' -Encoding utf8 | ForEach-Object { "  L{0}: {1}" -f $_.LineNumber, $_.Line.Trim() }
}
```

> PowerShell 的 `Select-String` 在多文件模式下 `Filename` 只取 basename，`README.md` 与 `hooks/README.md` 会混淆，务必按上面的写法逐文件循环输出。

| 命中位置 | 是否更新 | 原因 |
|---|---|---|
| `marketplace.json` devops `description` | ✅ 更新 | 条目总数 |
| `hooks/README.md`「tips.jsonl 包含 N 条技巧」 | ✅ 更新 | 条目总数 |
| `.codex-plugin/plugin.json`「longDescription」 | ✅ 更新 | 条目总数（Codex 侧描述，与 marketplace description 同文案） |
| `.kiro/steering/plugins.md`「tips.jsonl — N条技巧库」 | ✅ 更新 | 条目总数 |
| `.kiro/steering/structure.md`「tips.jsonl \| N 条使用技巧」 | ✅ 更新 | 条目总数（措辞是「条**使用**技巧」，旧窄正则命中不到） |
| `.kiro/steering/product.md`「N条使用技巧自动轮播」 | ✅ 更新 | 条目总数（同上，措辞插了「使用」二字） |
| `hooks/README.md`「默认每次显示 6 条技巧」 | ❌ 不动 | 单次展示条数，与总数无关 |
| `hooks/README.md`「每条技巧一个 JSON 对象」 | ❌ 不动 | 格式说明，不含数字 |
| `show-tip.sh`「每次选择 N 条技巧」「合并多条技巧」 | ❌ 不动 | 脚本注释，且脚本逻辑不在本 skill 职责范围 |
| `README.md` 插件列表行「SessionStart（技巧轮播）」 | ❌ 不动 | 有意不含数字，避免多处同步失准 |
| `marketplace.json` 顶层 `description` | ❌ 不动 | 仅工具链概述，从不含条目数 |

> 若某一天 `README.md` 或顶层 `description` 被改成含具体数字的表述，需同步扩充上表——但**不要主动往这些位置添加数字**，同步点越少越不易失准。

**版本号升级不在本 skill 定义**——由 `commit-cc-plugin` 第二步按 AGENTS.md 触发矩阵统一处理，本 skill 只交接事实：本次改动落在 `plugins/optimus-devops-plugin/hooks/` 内，届时应升该插件的两份 `plugin.json`（Patch）。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| 某处文件不存在（如路径变更） | 跳过该处，继续更新其余文件 | 在摘要中列出"未同步"文件，不阻断提交 |
| 数字 pattern 在六处应更新位置中找不到 | 用上面的全仓库 `grep -rnE '条[^，。\|]*技巧'` 确认格式是否变更 | 跳过并在摘要注明，不修改该文件 |
| 六处数字更新后彼此不一致 | 以 tips.jsonl 实际 `^{` 行数为准 | 报告具体不一致位置 |

> 🔴 **CHECKPOINT**：若命中上表"数字不一致"分支，报告具体差异位置后用 `AskUserQuestion` 发起确认：
> - `question`: "同步文档数字时发现不一致：{具体差异位置}。是否以 tips.jsonl 实际 `^{` 行数（{X}）为准继续提交？"
> - `options`: 「以 tips.jsonl 实际行数为准，继续提交」（推荐）／「取消本次提交，我要手动检查」
> - 选「取消本次提交，我要手动检查」或 Other 自定义文本 → 停止本次提交，`.last-synced-version` 不更新——不得在未确认的情况下直接进入第六步。

## 第六步 — 展示摘要并提交

按以下格式输出执行摘要：

```
✅ sync-cc-tips 完成 · v{锚点版本} → v{最新版本}

📥 新增  N 条
  · [分类] 条目标题
  · ...

✏️  修改  N 条
  · [分类] 条目标题 → 修改说明
  · ...

🗑️  删除  N 条
  · [分类] 条目标题（删除原因）
  · ...

⏭️  跳过  N 条（已覆盖 / 非用户可操作功能）

📊 条目总数：{旧数} → {新数}
📄 已同步：marketplace.json · hooks/README.md · .codex-plugin/plugin.json · .kiro/steering/{plugins,structure,product}.md
🔖 版本：两份 plugin.json {旧版本} → {新版本}（Patch）
🔖 同步锚点：v{锚点版本} → v{最新版本}

---
进入提交流程...
```

摘要展示完毕后，立即调用 `commit-cc-plugin` skill 完成提交推送。

| 触发条件 | 一线处理 | 仍失败兜底 |
|---|---|---|
| `commit-cc-plugin` skill 不可用 | 提示用户手动执行：`git add` → `git commit` → `git push` | 输出待提交的完整 diff 供用户参考 |
| 提交被 hook 拦截（pre-commit 失败） | 报告 hook 输出，不强制绕过 | 停止，提示用户修复后手动重试提交 |

## ⛔ 不要做什么（反例黑名单）

| 反模式 | 原因 | 替代做法 |
|---|---|---|
| 把 changelog 里所有更新项都加入 tips.jsonl | tips 面向用户实用技巧，不是版本记录——内部重构、bug fix、依赖升级不应出现 | 只加对用户操作有实质影响的功能（新 flag、新命令、新设置项） |
| 只用条目标题判断是否已覆盖 | tips.jsonl 每条含完整正文，次级功能点只出现在功能/效果/例子字段而非标题 | 必须扫描 tips.jsonl **全文**，用主标识符（flag 名/设置项名/命令名）做精确匹配 |
| 0变化时仍然提交 | 产生无意义 commit，污染 git 历史 | 触发「🚦 零变更总闸」直接终止，不进入 Step 4-6，不调用 commit-cc-plugin |
| 修改 show-tip.sh 脚本逻辑 | 脚本逻辑不在本 skill 职责范围内 | 只修改 tips.jsonl 数据文件 |
| 删除旧功能条目，但该功能仍可用（只是有了替代方案） | 用户可能仍在用旧方式 | 仅在 changelog 明确标注 Removed/Deprecated 时删除 |
| 用估算数字代替实际计数更新文档 | 估算不准会导致文档与实际不符 | 必须先统计实际 `^{` 行数再更新，且不加 1 |
| 抓取失败后继续执行后续步骤 | 基于空数据的操作可能误删现有条目 | 第一步失败 → 立即停止，不执行任何写入操作 |
| 在本 skill 内自行决定版本号怎么升 | 规则的唯一依据是 AGENTS.md 触发矩阵，写第二份必然与之分叉——曾长期误写为升 marketplace 顶层 version 且漏升 `.claude-plugin/plugin.json` | 交给 `commit-cc-plugin` 第二步统一处理，本 skill 只交接「改动落在 `plugins/optimus-devops-plugin/hooks/` 内」这一事实 |

> `.claude/` 下的 skill 文件本身不触发版本号升级（遵循 CLAUDE.md 规范）
