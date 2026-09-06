# 知识库（knowledge-base）

跨插件共享的规范知识库，供人类阅读也供 skill 编程式查询。当前收纳领域：`dotnet`、`csharp`、`wpf`、`git`、`media`、`skill-authoring`、`architecture`、`design-patterns`、`data-structures-algorithms`、`mcp`、`dotnet-debugging`。其中 `dotnet`、`media` 为纯描述性参考领域（无规范条款），其余领域为规范条款 + 参考混合。

## 目录结构

每个领域目录遵循统一模式——**元数据在领域根目录，内容按类型分目录**：

```
<domain>/
├── README.md            # 领域说明、阅读路径、分类说明
├── index.jsonl          # 索引：rule + reference 统一编目
├── rules/               # 规范条款（MUST/SHOULD/MAY 语气）
│   ├── 01-*.md ... 17-*.md
└── reference/           # 描述性知识（无规范语气），首篇内容产生时才建
    └── *.md
```

目录约束：

- `README.md`、`index.jsonl` 是领域导航元数据，始终位于领域根目录，不下沉到分类目录。
- `rules/` 只放可用于合规判断的规范正文；文件编号在 `rules/` 内保持既有顺序。
- `reference/` 与 `rules/` 是**同级并列**关系，不是从属关系；reference 只解释概念、机制、工具和用法。
- 索引的 `file` 始终是相对领域根目录的路径（`rules/05-error-handling.md`、`reference/video-codecs.md`）；正文内交叉引用同样采用该形式，与索引保持一致。
- 后续新增分类（如 `examples/`、`decisions/`、`playbooks/`）必须先定义用途、内容语气、索引 `kind` 与生命周期规则，再建目录，并登记到 `catalog.json`；不预建空目录，也不设"其他"这类无语义收容目录。

根目录另有 `catalog.json` 领域目录册，登记每个领域的内容分类、维护者、状态、主要消费者与最近审阅日期。新增或删除领域时必须同步维护——`check_index.py` 会校验 `catalog.json` 与实际领域目录双向一致（登记了不存在的领域、或存在未登记的领域都会报错）。

领域职责边界：`dotnet` 负责 Runtime、.NET Framework、SDK、目标框架、操作系统兼容性与生命周期；`csharp` 负责 C# 语言和通用工程实践；`wpf` 负责 WPF/XAML 桌面 UI 技术栈；`git` 负责版本控制协作；`media` 负责媒体处理概念；`skill-authoring` 负责 Skill 创建与维护规范；`architecture` 负责语言无关的架构风格、分层契约与设计原则；`design-patterns` 负责设计模式的选用判据与误用识别；`data-structures-algorithms` 负责数据结构与算法的选型判据与复杂度判断；`dotnet-debugging` 负责程序出问题后的取证与定位（征象判据、CLR 可观测结构、dump 与 SOS 命令解读），与 `csharp`/`wpf` 的预防性规范互补而不重叠。领域可以相互引用，但不得复制同一事实或规则。

## 消费方式

skill 需要引用某条规范/知识时，先用 Grep 在对应领域的 `index.jsonl` 中按 `tags`/`title`/`summary` 检索，定位到 `id` 后按 `file` + `anchor` 打开原文件读取具体条款——索引不复制正文，原始 Markdown 文件始终是唯一真相源。

两种消费模式，按场景选择，不互斥：

- **动态检索**：consumer 事先不知道规则具体在哪，先按关键词在 `index.jsonl` 查，再按 `file`+`anchor` 定位原文，适合临时性、探索式引用。
- **固定映射**：consumer 自身已有稳定的分类体系（如代码审查的审查大类），可以直接在自己的文档里写死 `file` § `章节` 引用，不必先过一遍 `index.jsonl`——`csharp-code-review`、`wpf-code-review` 的"审查清单"表格属于此类，是被认可的消费方式，不代表未遵循规范。

索引记录字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 必填 | `<domain>.<两位文件编号或 ref>.<slug>`，全局唯一，人工手写；slug 用小写字母/数字/连字符 |
| `kind` | 必填 | `"rule"` \| `"reference"` |
| `level` | rule 必填 | 仅 `rule` 有，`MUST`/`SHOULD`/`MAY`；`reference` 不得有 |
| `file` | 必填 | 相对领域根目录的路径（`rules/*.md` 或 `reference/*.md`） |
| `anchor` | 必填 | 文件内标题文本（非 slug），无锚点留空字符串 |
| `title` | 必填 | 条目标题 |
| `tags` | 必填 | 自由关键词数组 |
| `summary` | 必填 | 一句话摘要 |
| `enforcement` | 可选 | `ci` \| `review` \| `advisory`，表达规则如何执行 |
| `status` | 可选 | `active` \| `deprecated` \| `experimental`，缺省视为 `active`；标 `deprecated` 须同时满足下文"status：废弃条目的过渡期"的三条要求 |
| `source` | 可选 | 依据数组，两种形式：外部 URL，或领域内相对路径 `<file>#<标题文本>` |
| `applies_to` | 可选 | 技术栈、版本或场景边界数组 |
| `reviewed_at` | 可选 | 最近审阅日期，ISO 格式 `YYYY-MM-DD` |
| `owner` | 可选 | 维护责任主体（团队而非个人） |

可选字段在 schema 层面仍是可选的：未填不报错，填了必须合法，`check_index.py` 校验全部字段的类型与枚举取值。但其中四个字段已在全部 `rule` 条目上填满，实际是约定而非可选——**新增 `rule` 条目时须一并填写 `enforcement`、`status`、`applies_to`、`reviewed_at`、`owner`**，漏填不会被校验拦住，只会让该条目成为治理数据里的空洞。`source` 例外，按"规则不自解释时才填"的判据决定（见下文）。

### level 与 enforcement 的分工

两个字段回答不同问题，不可互相替代：

- **`level` 回答"违反有多严重"**——由正文措辞决定：「必须/禁止」→ `MUST`，「应该/不应」→ `SHOULD`，「可以/建议」→ `MAY`。
- **`enforcement` 回答"靠什么拦住"**——由该规则能否被工具无歧义判定决定。

| `enforcement` | 判定标准 | 典型例子 |
|---|---|---|
| `ci` | 存在可自动执行的检查机制（正则校验、静态分析规则、平台保护规则、扫描器），工具能无歧义判定通过与否 | 分支名格式、Conventional Commits 格式、`.Result`/`async void`（Roslyn）、拼接 SQL 与硬编码密钥（扫描器）、CPM 版本落点（csproj） |
| `review` | 需人工判断内容质量或变更意图，工具无法可靠判定 | PR 描述是否讲清背景、版本号语义是否判断正确、分层依赖方向是否越层、mock 是否只 mock 了外部边界 |
| `advisory` | 建议性做法，不作为拦截依据 | CODEOWNERS 配置、测试框架横向对比表、性能优先级排序 |

**判 `ci` 的操作性检验：工具判的是该小节的实质，还是只是它的外壳？** 只判外壳的填 `review`。`git.02.commit-hooks` 是这条检验的原型——"hook 文件是否存在"可自动判定（外壳），但该节的实质要求是"不得绕过 hook"，那只能靠人看提交记录判断，所以是 `review`。同理，`csharp.07.measure-before-optimize` 的实质是"优化前有没有真的测量过"，不是"仓库里有没有 BenchmarkDotNet 引用"。

判据问的是**能不能被工具判定**，不是"本仓库有没有在跑"。本仓库既无 CI 也无 git hook，`enforcement` 对自身是声明性元数据；标 `ci` 的 130 条指的是**被这些规范约束的项目**的 CI 该拦什么——消费者据此决定哪些规则进流水线、哪些进 review 清单。

**一个小节内混有不同级别的条款时，`level` 取该小节最强条款的级别**（实测 76% 的条目属此情形）。这是对消费者安全的默认——不会把强制条款误判为推荐；但反过来，命中一条 `MUST` 条目不代表该小节每句话都是硬性要求，消费者仍需按 `file` + `anchor` 打开正文读具体措辞。这也是"索引只做定位、不复制正文"原则的直接后果。

约束：`level: MAY` 的条目不得标 `enforcement: ci`——可选做法不应作为 CI 拦截依据，该组合由校验器报错。

### source：规则到理由的连接

规范条款只写"要做什么、不能做什么"，**理由、选型对比、例外场景由 `reference/` 承载**——这是 `rules/` 与 `reference/` 分层的目的。`source` 把这层关系登记成可检索的数据，让消费者能从一条规则反查到它的依据，而不必靠人工在两个目录间猜对应关系。

- 内部依据写 `<file>#<标题文本>`（如 `reference/commit-message-tooling.md#2.3 为什么不能靠"团队自觉"代替 hook`），路径相对领域根目录，与 `file` 字段同一形式。
- 外部依据写完整 URL（如 `https://www.conventionalcommits.org/`）。
- `check_index.py` 校验内部引用的文件与锚点真实存在；URL 不做离线校验。因此**迁移 `reference/` 文件或改其标题时，`source` 也是需要同步的引用之一**。
- 规则本身自解释、无独立理由文档时不填——`source` 未填不代表缺失，不追求 100% 覆盖。

### reviewed_at：读过才填

`reviewed_at` 的语义是「该条目的正文最近一次被人实际读过并确认仍然成立的日期」，不是「索引行最近一次被编辑的日期」。批量刷新这个字段而不读正文，会把它变成一个看起来在治理、实际什么都不保证的数字——比留空更糟，因为留空至少诚实地表示"没人审过"。

因此批量填治理元数据时，按领域逐文件读正文再填，不要按 `id` 列表批处理。这一约束在 5.0.0 推广 `enforcement` 时验证过：读正文是判 `enforcement` 的必要输入，顺带暴露了 `skill-authoring` 三条 `level` 与正文措辞不符——不读正文的批处理两件事都做不到。

### status：废弃条目的过渡期

条目不再适用时**不直接删索引行**，而是标 `status: deprecated` 走一个过渡期。直接删除会让按旧 `id` 检索的消费者只得到"查不到"，而不是"已废弃，改用 X"——线索断在最需要它的地方（3.0.0 删 `csharp.15.quality-gate-overview` 即是此形态）。

废弃条目必须同时满足三条，否则 `check_index.py` 报错：

- **正文小节保留，标题加「已废弃」标记**，节首一行说明替代去向与移除计划。正文不删，是为了让按 `file` + `anchor` 定位的旧引用仍能读到内容与指引；`anchor` 保持不变。标记文本固定用「已废弃」，换成「弃用」「过时」检不出。
- **`summary` 须含替代去向**：条目 `id`（`git.03.pr-conventions`）或规范文件路径（`git/rules/03-pull-requests.md`）。只标废弃不给去向，比直接删更糟——检索者拿到一条死规则且无路可走。
- **不得保留 `enforcement: ci`**：已废弃的规则不应仍作为 CI 拦截依据，改 `advisory` 或删该字段。

其他条目的 `source` 不得指向已废弃的小节（该小节随时会被移除，届时 `source` 静默失效），校验器一并拦截。废弃属不兼容语义变化，按 Major 升版本；废弃条目在下一个 Major 版本移除正文与索引行。当前废弃条目数可用 `check_index.py --audit` 查看。

例外：**从未被外部引用、且刚建立不久的条目**（当次提交内的笔误、重复登记）直接删除即可，无消费者需要过渡期。

## 索引粒度规范

粒度不均会让动态检索在不同领域的召回能力不可比较，因此统一如下判断标准：

- **可独立判断的规则原则上单独登记一条**：一条规则若能脱离上下文单独用于合规判断（"断言库须团队统一"、"脚本禁止交互提示"），就应有自己的索引条目，锚点指向其所在小节。
- **导航性标题不作为规则登记**：领域 README 的阅读路径、文件地图、"权威参考"等章节是导航，不承载判断依据，不登记。
- **reference 可按文档或按独立主题登记**：描述性文档以整篇为单位登记是被认可的做法（media、dotnet 领域即如此）；仅当一篇 reference 内部存在多个会被独立检索的主题时，才拆成多条。因此审计报告的覆盖率**只统计 `rule` 类文件**，不对 reference 计算标题覆盖率。
- **文件级汇总条目与节级条目可以并存**：早期以整篇为单位登记的 `rule` 条目（如 `skill-authoring.01.format`）已被消费者按文件引用，补充节级条目时保留它作为文件入口，不改 ID——改 ID 属破坏性变更。
- 覆盖率用 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" --audit` 查看，输出每个规范文件的 `indexed / eligible_headings`。`anchor` 指向三级标题时，其父二级章节记为已覆盖——按更细粒度登记不该被算成未登记。

### 覆盖率不追求 100%

**覆盖率是诊断指标，不是达标指标**——它回答"有多少小节可被检索到"，而有些小节本就不该被检索到。把它当 KPI 追平，会逼出两类坏条目：给操作指南强造 rule 条目，以及给已由别处承载的约束造第二个检索入口。以下三类小节**有意不登记**，它们构成的缺口是正确状态：

| 不登记的情形 | 例子 | 原因 |
|---|---|---|
| 落地模板与快速上手 | `csharp/rules/01-project-structure.md` 附录 `Directory.Build.props` 模板、`12-testing.md` § 13 框架快速上手 | 模板每行都注着"见第 N 节"，约束的真源在被引的那些小节；快速上手是语法教学，零规范措辞。登记它们等于给同一约束造第二个入口 |
| 通篇是跨章导航的小节 | `csharp/rules/07-performance.md` § 10 并发与数据（两条均"见 `08` 章"） | 每条都带"见/联动 X 章"标注的小节是导航而非规范，条款真源在被指向的章节 |
| 约束已由其他领域/章节承载 | `csharp/rules/14-security.md` § 6 依赖与供应链（真源 `csharp.10.vulnerability-scanning`）、`15-quality-review.md` § 1 静态分析（真源 `csharp.01.static-analysis`）| 同一约束在两处登记，检索者拿到两条却无从判断哪条是准——这正是"领域可以相互引用，但不得复制同一事实或规则"要防的形态 |

**"联动 X 章"是重复的可靠信号**：一节里若每条条款都带这类标注，先怀疑它是导航节，判断其条款真源在哪，而不是直接给它登记条目。若真源与本节各写了同一约束的一半，正确处置是先去重（本节改为引用真源 + 只留特有条），再给收窄后的内容登记。

## 维护约定

- 新增/修改一条规范/reference 时，同一次提交里必须同步更新对应 `index.jsonl`。
- 改动后运行 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>` 做一致性自检（脚本随 `knowledge-base-maintain` skill 分发）。校验分两类作用域：
  - **单领域检查**（传参）：该领域的 schema、字段枚举、`id` 格式、`file` 存在与路径越界、`anchor` 匹配、孤儿文件。
  - **全局检查**（始终执行，即使只传一个领域）：`id` 全局唯一、`id` 前缀与领域归属一致、`catalog.json` 与实际领域双向一致。
- 加 `--audit` 输出健康报告（记录数、`kind`/`level` 分布、规范文件的标题索引覆盖率、孤儿文件）。
- 规范条款可选择性引用 `reference/*.md` 加强依据；引用单向，reference 不反向声明被谁引用。
- **版本号按领域独立管理**：各领域版本号见该领域 `README.md` 顶部，变更历史见该领域 `CHANGELOG.md`；知识库不再有全局版本号（7.2.0 为分叉点，此前的全局版本历史已按领域归入各自 CHANGELOG）。一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG。`check_index.py` 校验领域 README 版本行与其 CHANGELOG 最新条目一致。日常新增/修改建议通过 `/knowledge-base-maintain` skill 完成，会自动同步索引与版本号。
- 不做自动生成索引的脚本——`tags`/`summary`/`level` 需要语义判断，机械提取质量不可靠。
- 索引覆盖是渐进式的，不要求一次性覆盖全部规范文件——新增/优化 skill 引用到某条规则时，若该规则尚未登记索引，随手补一行即可，不必专项排期回填。
- 迁移或重命名规范/reference 文件时，必须同步更新五处：索引 `file` 字段、索引 `source` 字段中的内部引用、领域 README 文件地图、正文交叉引用、消费者 skill 的引用路径（含 Markdown 链接目标）。
- **外部作品的许可证隔离**：`data-structures-algorithms/reference/` 提取自《Hello 算法》，以 CC BY-NC-SA 4.0 授权，独立于本仓库其余部分（`reference/LICENSE` 为其许可证全文，非 Markdown 故不登记索引）。SA 条款在**目录级别**隔离：不得把自撰规范内容混入该目录，也不得整段复制其正文到 `rules/`——`rules/` 只能引用它作为理由出处（`source` 字段）。该目录不接受本地编辑，更新时重新从上游 tag 提取。

## 与仓库已有资产的关系

- `plugins/optimus-backend-plugin/skills/csharp-code-review`：审查规则以 `knowledge-base/csharp/` 为准，见该 skill 的"权威参考"章节。
- `plugins/optimus-frontend-plugin/skills/wpf-code-review`、`wpf-project-conventions`：代码审查与项目结构判断依据见 `knowledge-base/wpf/`。
- `.claude/rules/skill-conventions.md`：SKILL.md 的仓库专属约定（版本号、author、category、compatibility、allowed-tools、前置校验、需求预告、持续优化）；通用规范引用 `knowledge-base/skill-authoring/`。
- `.claude/rules/doc-conventions.md`：CHANGELOG.md 与 README.md 的格式规范（含 skill / agent 两栏差异）、编辑铁律。
- `.claude/rules/agent-conventions.md`：agent 的仓库专属约定（选型判据、`agents/` 目录硬约束、frontmatter、配套文档位置、独立版本化）。
