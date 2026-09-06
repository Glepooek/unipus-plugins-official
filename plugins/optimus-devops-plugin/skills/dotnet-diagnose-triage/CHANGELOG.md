## [1.0.1] - 2026-09-06

### Fixed
- `test-cases/golden.md` 七例「输入」段由描述性摘要改为**可直接消费的原始取证输出文本**——原表述（如「显示某业务类型 Count 很高」）会让无头模式的外层会话判定证据不足而自行拦下追问，agent 根本不被派发，实测的是外层会话而非 agent
- 「跑法」一节新增三条跑法约束与无头命令范式：前置「不要自己追问或代答」、含 shell 元字符时走文件 + `-p "$(cat file)"`、输出落盘仓库外 `$HOME/dd-golden/`
- 修正两处构造缺陷：测例 2 的 `Total` 与各行之和不一致（`2369086` → `2368986`）及三行数值空格错位；测例 7 删除异常行之后的 INFO 业务行（进程终止后不应再有）
- 测例 1 补 `!clrstack -all` 交叉证据——`!syncblk` 本身不输出等待线程身份（`sos-locks-and-async.md § 1`「注意」段），原输入的「互为等待方」是分析者结论而非证据

### Changed
- `known-issues.md` 补录 darwin-skill 基线分 **88.3**（按 `knowledge-base/skill-authoring/reference/darwin-skill-optimization.md § 2` 的九维 rubric 手工评出，公式经 `results.tsv` 三条历史记录反推校准）；修正此前「本体被 gitignore 排除」的错误归因——实为从未进入版本库

## [1.0.0] - 2026-09-06

### Added
- 新建 skill：`knowledge-base/dotnet-debugging/` 的首个消费者，承载假设台账消解循环
- 主干六节：假设台账（四字段 / 初始化 / 关闭 / 出口 / 跨轮续用）、自检四项、三结论强度、九条失败处理、与官方产物的交接、dump 处置合规
- `references/` 三份按下钻频次分文件：`symptom-hypothesis-map.md`（征象映射 + 二维路由 + 第二跳）、`evidence-precheck.md`（A/B 两组清点 + 崩溃日志定位）、`verdict-forms.md`（判据两形态 + 修复方向四档）
- `test-cases/golden.md` 七个黄金测例
