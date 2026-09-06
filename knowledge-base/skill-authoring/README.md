# Skill 创建规范

> 版本：7.3.0

> 面向团队的 Skill 创建总纲，参考 [Agent Skills](https://agentskills.io) 开放标准。覆盖 SKILL.md 格式规约、描述优化、质量评估、脚本使用与最佳实践，指导创建**可跨 runtime 使用、能精准触发、产出可靠**的 skill。

## 文档目的

本规范统一团队创建 Agent Skill 的方式，目标是让创建的 skill **可被 agent 精准发现与触发、加载后产出可靠结果、并随真实使用持续改进**。它不是对 agentskills.io 的翻译堆砌，而是提炼为团队可执行的规则（MUST/SHOULD/MAY），并落地的具体做法。

## 适用范围与读者

- **适用范围**：所有新 skill 的创建、既有 skill 的改造与优化；本仓库 `plugins/*/skills/` 与 `.claude/skills/` 下的 skill 均适用
- **读者**：所有会创建/维护 skill 的开发者。新人用于建立基线，资深成员用于对齐质量边界

## 规范级别

沿用 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) 语义。各篇正文使用对应措辞，级别决定违反后的处置：

| 级别 | 措辞 | 含义 | 违反处置 |
|---|---|---|---|
| **必须 MUST** | "必须"、"禁止" | 硬性要求，无正当理由不得违反 | 视为缺陷，CI / review 拦截 |
| **应该 SHOULD** | "应该"、"不应" | 推荐做法，除非有明确理由 | review 说明理由后可豁免 |
| **建议 MAY** | "可以"、"建议" | 可选做法，团队不强制 | 无 |

## 规范如何执行

规范通过以下手段落地：

1. **格式校验**：用 [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) 校验 SKILL.md frontmatter 与命名规范（`skills-ref validate ./my-skill`）
2. **前置检查**：按 `.claude/rules/skill-conventions.md` 的仓库专属约定（版本号、author、category、allowed-tools 写法）自查；CHANGELOG.md / README.md 的格式要求见 `.claude/rules/doc-conventions.md`
3. **触发验证**：按 `rules/02-description-optimization.md` 用 eval 查询集验证 description 触发准确率
4. **质量评估**：按 `rules/03-skill-evaluation.md` 跑 with-skill / without-skill 基线对比，记录 pass_rate / tokens / time
5. **模板兜底**：新 skill 的 SKILL.md 结构参照 `rules/01-skill-format.md` 的推荐章节

## 阅读路径

| 读者 | 必读 | 选读 |
|---|---|---|
| 首次创建 skill | `01` `04` | `02` `05` `06` |
| 优化既有 skill | `02` `03` `05` `06` | 其余 |
| 全部成员 | 本文件、`01` | — |

## 文件地图

| 编号 | 文件 | 主题 |
|---|---|---|
| — | `README.md` | 总则、级别、执行、索引 |
| 01 | `rules/01-skill-format.md` | SKILL.md 格式规约：目录结构、frontmatter、正文、文件引用、progressive disclosure |
| 02 | `rules/02-description-optimization.md` | 描述优化：触发机制、写作原则、trigger eval、train/validation 切分 |
| 03 | `rules/03-skill-evaluation.md` | skill 质量评估：测试用例、assertions、grading、benchmark、迭代循环 |
| 04 | `rules/04-script-usage.md` | 脚本使用：one-off 命令、自包含脚本、agentic 设计 |
| 05 | `rules/05-best-practices.md` | 最佳实践：经验来源、上下文预算、控制校准、指令模式 |
| 06 | `rules/06-continuous-improvement.md` | 持续优化：创建后基线评估、known-issues.md 反馈记录、累积阈值触发 darwin-skill 优化 |

## 索引与机器消费

本领域下的 `index.jsonl` 是供 skill 编程式检索的索引（不重复正文，只做定位），字段说明与维护约定见仓库根 `knowledge-base/README.md`。`reference/` 目录存放不带 MUST/SHOULD/MAY 语气的讲解性内容（详细机制、示例、对比），与 `rules/` 下的规范文件是并列关系，不是从属关系——规范篇引用 reference 加强依据，reference 不反向声明——新增/修改任一类内容都需同步 `index.jsonl`，建议通过 `/knowledge-base-maintain` skill 完成。

## 更新与豁免

- 每篇文件头部记录本文件更新历史（日期 + 变更摘要），随变更提交
- 规范修订走 PR，review 通过后合入，并同步更新本文件的地图与阅读路径
- **豁免**：遇规范与场景冲突，在 PR 中显式注明"豁免原因"，由 reviewer 裁量；系统性豁免需求应推动规范修订，而非长期例外

## 与仓库已有资产的关系

- `.claude/rules/skill-conventions.md`：仓库级规则文件，聚焦 SKILL.md 的专属约定（版本号、author、category、allowed-tools、前置校验、需求预告、持续优化）；其中涉及"如何创建 skill"的规范引用本领域各篇
- `.claude/rules/doc-conventions.md`：CHANGELOG.md 与 README.md 章节规范，skill 与 agent 共用（两者在「所处层级」「触发词」两章有分叉写法）
- `.claude/rules/agent-conventions.md`：agent 产物的专属约定，与 skill 是并列的两套规范，不互相套用
- `darwin-skill`：skill 自动优化评估，与 `rules/03-skill-evaluation.md` 的评估方法论互补（darwin 侧重评分自动化，本领域侧重 eval 驱动迭代）
- `skill-creator`（外部）：agent 自动化创建 skill 的参考实现，与本领域规范配套使用

## 权威参考

- [Agent Skills 规范](https://agentskills.io/specification)
- [Agent Skills 最佳实践](https://agentskills.io/skill-creation/best-practices)
- [优化 skill 描述](https://agentskills.io/skill-creation/optimizing-descriptions)
- [评估 skill 输出质量](https://agentskills.io/skill-creation/evaluating-skills)
- [在 skill 中使用脚本](https://agentskills.io/skill-creation/using-scripts)
