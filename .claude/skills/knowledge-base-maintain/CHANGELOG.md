# Changelog

## [1.9.3] - 2026-09-06

### Changed
- `check_refs.py` 的 `CONSUMER_GLOBS` 增补 `plugins/*/skills/*/references/*.md`——此前只覆盖同级 `*REFERENCE*.md`，不含 `references/` 子目录，而这恰是 anchor 密度最高的位置。随 `dotnet-diagnose-triage` 落地首次暴露此缺口

## [1.9.2] - 2026-08-30

### Added
- 新增 `known-issues.md` 使用期反馈记录机制（空模板），配套仓库新增的 skill 持续优化硬性约定，见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`

## [1.9.1] - 2026-08-29

### Added
- `check_orphan_files` 单元测试补 `test_changelog_is_not_orphan`，与既有 `test_readme_is_not_orphan` 对称——1.9.0 把 `DOMAIN_META_FILES` 扩为含 `CHANGELOG.md` 时漏配对应测试，仅靠其他测试间接覆盖

### Fixed
- 补记 1.9.0 遗漏的一条 Added：`DOMAIN_META_FILES` 新增 `CHANGELOG.md`（原仅 `README.md`）——9 个领域各自新建的 `CHANGELOG.md` 若不加入孤儿文件白名单，会被 `check_orphan_files` 误报为未索引的孤儿 Markdown

## [1.9.0] - 2026-08-29

### Added
- `check_index.py` 新增 `check_domain_versions`：校验每个领域 `README.md` 顶部 `> 版本：x.y.z` 与该领域 `CHANGELOG.md` 首个版本条目一致，接入 `run_checks` 的全局检查区。取消全局版本号后版本号散落 9 处，靠人看必然漂移——README 说 7.2.1 而 CHANGELOG 最新是 8.0.0 这类不一致不会被任何其他检查发现，而消费者读的正是 README 那一行
- Step 5 问题表新增 5 行、失败处理表新增 1 行，覆盖新校验的报错形态

### Changed
- **Step 6 整节重写**：版本号与 CHANGELOG 由「根 `README.md` + 根 `CHANGELOG.md`」改为「各领域 `README.md` + 各领域 `CHANGELOG.md`」。新增判断：一次变更涉及多个领域时，每个领域各自升版本、各自写 CHANGELOG，跨领域迁移两侧级别可以不同（迁出侧通常 Major，迁入侧可能只是 Minor）
- Step 6 版本级别表的 Major 行补入「领域改名或条目 `id` 变更」——本次 `algorithms` → `data-structures-algorithms` 属此类，旧表未覆盖
- Step 2 新建领域流程要求同时创建 `CHANGELOG.md`（首条目 `1.0.0`）与带版本行的 `README.md`；新领域起始 `1.0.0`，不套用 7.2.0 分叉点
- 领域元数据文件路径由 `00-README.md` 改为 `README.md`（Step 2、Step 4 迁移五处、失败处理表）

## [1.8.0] - 2026-08-28

### Added
- Step 3 新增批量为已有条目补治理字段的操作约束：**按领域逐文件读正文再填，不按 `id` 列表批处理**。`reviewed_at` 的语义是"正文最近被人实际读过并确认仍成立"，不读正文就刷日期是假声明——比留空更糟，留空至少诚实表示"没人审过"；且读正文本就是判 `enforcement` 的必要输入。知识库 5.0.0 把 `enforcement` 从 3.7% 推到 100% 时按此执行，顺带发现 `skill-authoring` 三条 `level` 标 SHOULD 但正文含「必须/禁止」，批处理两件事都做不到
- Step 5 常见问题表新增 `字段 source 必须是数组`——`source` 是数组字段，单个依据也要写成 `["..."]`，本次推广时真踩到

### Changed
- Step 3 第 4 点由"按需填写可选治理字段"改为"`rule` 条目须一并填 `enforcement`/`status`/`applies_to`/`reviewed_at`/`owner`"。schema 层它们仍可选（漏填不报错），但全库 326 条已填满，漏填只会留一个校验器抓不到的空洞
- `enforcement` 的判断依据补入外壳检验：**工具判的是该小节的实质，还是只是它的外壳（文件放哪、有没有引入某个包）？只判外壳 → `review`**。并明确问的是"能不能被工具判定"而非"本仓库有没有在跑"——本仓库无 CI，该字段描述的是被规范约束的项目该怎么拦

## [1.7.0] - 2026-08-28

### Fixed
- 覆盖率统计改为按 `anchor` 落点计算（新增 `covered_sections`）。旧实现用 `min(条目数, 二级章节数)` 封顶，只比数量不看落点：条目集中在同一小节时，多出的条目会把另一小节的真实空缺掩盖成满分——实测 `csharp/rules/12-testing.md` 17 条记 14/14，真实只覆盖 13 个。`anchor` 指向三级标题时归属到其父二级章节（`csharp/rules/02-coding-style.md` 的 15 条全部指向 h3，不该被算成未登记）
- 修正后 `csharp` 由虚高的 82.6% 回到真实的 81.8%——一个会自我掩盖缺口的指标，比没有指标更危险：它让人以为已经补完

### Added
- Step 2 新增按覆盖率缺口批量补条目的前置判断：`--audit` 的缺口里混着有意不登记的小节，照数字追平会同时给指南性章节强造 rule 条目、给已有真源的约束造第二个检索入口。附快速筛法（正文行数 / `必须`条数 / 代码块数的比值）与「一节里每条都带『见/联动 X 章』→ 它是导航节」这一判据
- Step 5 说明覆盖率是诊断指标而非达标指标，指向根 README 新增的「覆盖率不追求 100%」章节
- `test_check_index.py` 76 → 78 个单测。`test_extra_entries_do_not_mask_an_uncovered_section` 复刻 `12-testing.md` 的真实形态（3 条全落在同一小节，另一小节空缺），旧算法在此记满分

## [1.6.0] - 2026-08-28

### Added
- 新增"废弃条目"场景与 Step 4.5：`status: deprecated` 此前是纯枚举占位——全库 326 条无一使用，废弃只能走「直接删索引行」（3.0.0 删 `csharp.15.quality-gate-overview` 即是），外部消费者按旧 `id` 检索只得到「查不到」，而不是「已废弃，改用 `git.03.pr-conventions`」，线索断在最需要它的地方
- 废弃方式定为**保留正文 + 标题加「已废弃」标记 + `anchor` 不变**。若废弃时改 `anchor`，所有按 `file`+`anchor` 固定映射的消费者会立刻失效——那等于用一个破坏性变更去实现一个本意是「给过渡期」的机制
- Step 4.5 先区分废弃与删除：约束仍成立只是换了归属、或规则不再适用 → 标废弃；从未被引用且刚建立不久的条目（当次提交内的笔误）→ 直接删，无消费者需要过渡期
- `check_index.py` 新增 `check_deprecated`：废弃条目须①正文标题带「已废弃」（否则按 `file`+`anchor` 读正文的人毫不知情）②`summary` 含替代去向（条目 `id` 或规范文件路径——只标废弃不给去向比直接删更糟）③不得保留 `enforcement: ci`（已废弃却仍在 CI 拦截是矛盾状态）
- `check_source_refs` 新增：活跃条目的 `source` 不得指向已废弃小节——该小节将在下一个 Major 移除，届时 `source` 静默失效
- `--audit` 新增废弃条目统计（全库计数 + 各领域 id 清单）。保留正文的废弃方式尤其需要这个计数，否则废弃小节会无声堆积
- `test_check_index.py` 66 → 76 个单测。另做了一轮沙箱验证：拿真实的 326 条索引与真实规范文件走完整废弃流程，反例三条校验全部拦住且报错文本直接给出修法，正例零报错且审计正确计数——单测的合成 fixture 只证明逻辑对，证明不了废弃不会连带打断其他校验

### Changed
- Step 5 常见问题表新增废弃相关四类；Step 6 版本表标明废弃属 Major；失败处理表新增「要废弃的条目仍被消费者引用」（先改消费者引用再标废弃；替代去向未定时不要先标废弃）
- `description` 与场景表加入"废弃"，触发词新增"废弃规范条目"

## [1.5.0] - 2026-08-28

### Added
- `check_refs.py` 扫描范围扩到 `knowledge-base/*/rules/` 与 `knowledge-base/*/reference/`（38 → 101 个文件）。此前只看 `plugins/*/skills/`，而跨领域去重恰恰把 `§ 章节号` 引用写进了知识库正文——刚做完的 C# ↔ WPF 去重新增 4 处这类引用，全部落在旧扫描范围之外。生成引用的操作若不配套扩大看守范围，等于亲手埋下一次静默失效
- 引用的基准领域改为优先取消费者文件自身所在领域：知识库正文里的 `rules/xxx.md` 相对引用没有自指的 `knowledge-base/<domain>/` 路径可依，靠内容提取一律解析不出来
- 扩范围实测在 `git/reference/commit-message-tooling.md:183` 抓到一处**真实错误**：声称 `rules/02-commit-messages.md` §2 有「CI 侧二次校验」这一说法，但 §2 只讲本地 hook，该措辞在规范中根本不存在，真正对应的是 §3 的「CI 集成 secret scanning」。已修正为引用 §3
- 顺带补齐知识库正文内 11 处裸章节号引用的标题，全库 `--strict` 由 12 处问题降为 0

### Changed
- `SECTION_RE` 标题解析修三类形态问题（扩范围即是对解析器的压力测试——散文引用的标点比 skill 表格自由得多）：
  - 裸标题终止符补中文句号与全角逗号，否则「§ 7. 集成测试。WPF 侧只补一条：」会把整句吞成标题
  - 编号与裸标题之间要求 `.`/`．`/空格 分隔，且空格形态排除以助词打头的续写（`§2 的 hook 不可绕过要求` 是散文不是标题）。判据取结构而非标点枚举：带标题的引用必有分隔符，句子续写没有
  - 引号形态由只认 `「」` 扩为 `「」`/`""`/`""` 三种
- `test_check_refs.py` 21 → 31 个单测。其中 `test_subsection_title_separated_by_space_only` 是回归锁——中途曾把「必须有点号分隔」当判据，导致 `csharp-code-review` 已修好的 5 处 `§ 2.x 标题` 集体退回脆弱状态（子章节号里的点已被编号吃掉，标题只能靠空格分隔）
- Step 5 说明校验范围含知识库正文自身；Step 2 查重处置表补充「改为引用时须带章节标题」——否则去重解决了重复，却制造了不可校验的位置引用

## [1.4.0] - 2026-08-28

### Added
- 新增 `scripts/find_duplicates.py`：报告语义重复的条目候选。`check_duplicate_ids` 只查 `id` 字符串重复，挡不住同一条约束被两个领域各自写一遍——这类重复本仓库踩过两次（v1.5.0 按单个文件迁移协作条款漏掉散落项、3.0.0 发现 git ↔ csharp 语义环），两次都靠人工通读才发现
- 新增"查重"场景（Step 1 场景表第 4 项），可独立运行不改内容；Step 2 末尾新增写入前查重与三种情形（真重复/合理分层/语义环）的处置表
- 新增 `scripts/test_find_duplicates.py`，24 个单测；其中 `TestKnownDuplicateRegression` 用 3.0.0 那次人工发现的真实条目原文做回归基准——若评分改动让它们掉出候选，等于回退到人工通读时代

### Changed
- 首次实现用标准 Jaccard 相似度，在已知答案上实测真重复仅得 0.058、低于同批纯巧合词项对。改为**重叠占较短一方的比例**（规范 summary 长度差异大，Jaccard 分母会把真重复稀释），并对 4 字以上共有片段加权。改后已知的 3 对重复排名 3/4/7（共 1488 对候选）
- 候选筛选**不按 tags 交集**：3.0.0 那对真重复的 tags 交集为空（领域名本身占一个 tag 位，跨领域条目 tags 天然不相交），按 tags 筛会一个都检不出。tags 只作加分项
- 输出的"共有词项"把滑动窗口 n-gram 拼回完整短语（7 个 4-gram → 1 条「视为已泄露须立即轮换」），否则人看到的是同一短语的碎片

## [1.3.0] - 2026-08-28

### Added
- 新增 `scripts/check_refs.py`：校验消费者 skill 中对规范文件的 `§ 章节号` 引用。补上了此前无人看守的缺口——`check_index.py` 校验的是索引 `anchor` 的标题**文本**，管不到 skill 正文里写的 `§ 7` 这类**位置引用**；章节重编号后 `§ 7` 依然「存在」，只是指向了别的内容，不会有任何报错
- `check_refs.py` 三类检查：存在性（章节号有对应标题）、一致性（引用同时写了标题时须与该章节号的标题匹配——这是唯一能挡住重编号的一环）、脆弱性报告（只写号不写标题的引用无法交叉校验，列出并建议补标题，默认只告警，`--strict` 可视为失败）
- 新增 `scripts/test_check_refs.py`，21 个单测覆盖多文件同行归属、裸文件名的同目录省略写法、`§1-§5` 范围形态、跨领域歧义时不猜、以及"重编号后标题不符必须报错"的核心负向场景
- Step 5 新增章节号引用校验命令与四类问题的成因表；Step 4 新增第 5 点，明确重排/重命名章节时须同步消费者引用

### Changed
- `compatibility` 字段同步为 `scripts/` 下两个校验脚本

## [1.2.0] - 2026-08-27

### Added
- `check_index.py` 新增 `source` 内部引用校验：`<file>#<标题文本>` 形式的文件与锚点必须真实存在，外部 URL 不做离线校验——不校验等于新增一批无人看守的引用，与规范文件迁移后失效的正文交叉引用是同一类腐烂
- `check_index.py` 新增组合约束：`level: MAY` 不得配 `enforcement: ci`（可选做法不作为 CI 拦截依据）；`kind: reference` 不得有 `enforcement`
- `--audit` 报告新增治理元数据维度：全库 `enforcement` 填写率、各领域 `enforcement` 分布
- Step 3 补充 `enforcement` 与 `source` 的填写判断依据，并明确禁止把 `reference/` 的理由复制进规范正文
- Step 5 常见问题表新增 `source` 引用失效与 `MAY`+`ci` 两类；`test_check_index.py` 从 55 个测试扩展到 66 个

### Changed
- Step 4 迁移/重命名时需同步的引用由四处增加为五处，新增"索引 `source` 字段中的内部引用"

## [1.1.0] - 2026-08-27

### Added
- `check_index.py` 新增校验维度：schema 必填字段与类型、`kind`/`level`/`enforcement`/`status` 枚举、`id` 格式与领域前缀一致性、`file` 路径越界（`..`/绝对路径）、孤儿文件（未被索引引用的 Markdown）、`reviewed_at` ISO 日期格式
- `check_index.py` 新增 `--audit` 健康报告：记录数、`kind`/`level` 分布、规范文件的二级标题索引覆盖率、孤儿文件清单
- `check_index.py` 新增 `catalog.json` 双向一致性校验：登记了不存在的领域、存在未登记的领域、登记的分类目录不存在、非法 `status`、重复登记均报错
- Step 2 补充索引粒度判断指引；Step 4 补充迁移/重命名时需同步的四处引用（索引 `file`、领域 README 文件地图、正文交叉引用、消费者 skill 引用含 Markdown 链接目标）
- Step 5 补充常见校验问题对照表（7 类）；失败处理新增孤儿文件与 `catalog.json` 未登记两类
- `test_check_index.py` 从 18 个测试扩展到 55 个，覆盖全部新增校验维度

### Changed
- 校验作用域说明明确化：传 domain 只缩小"文件与锚点"范围，`id` 全局唯一 / `id` 前缀归属 / `catalog.json` 一致性三项始终按全局判定（此前单领域检查会漏报跨领域重复 `id`）
- 正文归属路径改为 `<domain>/rules/`（规范）与 `<domain>/reference/`（描述性），对应知识库目录结构调整
- 新建领域时须同步在 `knowledge-base/catalog.json` 追加领域记录
- Step 7 提交规则统一为一律走 `commit-cc-plugin`，与仓库根 `AGENTS.md` 一致（此前写作 `knowledge-base/` 不受该流程约束，与仓库强制要求矛盾）

## [1.0.2] - 2026-08-22

### Changed
- 领域说明文件路径更新：`knowledge-base/<domain>/README.md` → `00-README.md`（新建领域与规范级别参照示例同步改为 `csharp/00-README.md`）

## [1.0.1] - 2026-08-22

### Changed
- 校验脚本迁入本 skill 的 `scripts/` 子目录，随 skill 分发；运行命令改为 `python ".claude/skills/knowledge-base-maintain/scripts/check_index.py" <domain>`

## [1.0.0] - 2026-08-22

### Added
- 初始版本：引导新增/修改/迁移 knowledge-base 条目，同步索引、CHANGELOG、版本号，调用 check_index.py 做一致性校验
