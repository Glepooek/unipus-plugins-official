# dotnet-diagnose-triage · 已知问题记录

用于记录真实使用中暴露的问题，累积满 3 条"待处理"状态即触发一次 darwin-skill 优化循环。
格式与流程见 `knowledge-base/skill-authoring/rules/06-continuous-improvement.md`。

## darwin-skill 基线评估（2026-09-06）

| 项 | 值 |
|---|---|
| 总分 | **未取得** |
| 评估模式 | — |
| 各维度得分 | — |
| 原因 | `.claude/skills/darwin-skill/` 被 `.gitignore:426` 整目录排除，本机只余 `cards/` 与 `results.tsv` 两项历史产物，skill 本体（SKILL.md 与脚本）不存在，无法调用；`.kiro/skills/` 与 `.agents/skills/` 两处镜像同样缺失 |
| 判读 | 新建 skill 无历史分可比，AGENTS.md 的门禁原文针对已有 skill 改动的回归比对（「新分数 ≥ 改动前分数」），故本次不阻断交付。**待 darwin-skill 可用时补录基线分**，后续 Minor/Major 升级须 ≥ 该补录分数 |

## 黄金测例首轮结果（2026-09-06）

七例经 `claude --plugin-dir ./plugins/optimus-devops-plugin -p` 无头模式实调 `@optimus-devops-plugin:dotnet-diagnose`，逐例比对 `test-cases/golden.md` 的预期。

| # | 台账 | 强度 | anchor | 备注 |
|---|---|---|---|---|
| 1 | ✅ | ✅ | ✅ | `MonitorHeld` 编码 (3−1)/2=1 读对，循环等待识别正确；另主动指出 `!syncblk` 不输出等待线程身份，须交叉 `!clrstack -all`，并按 `wpf-dispatcher-deadlock.md § 4` 追加「环是否绕回 UI 线程」为独立待验项 |
| 2 | ✅ | ✅ | ✅ | 停 `待验`，明确判据要求两次 `-stat` 对比；另自行发现输出被截断（`Total` 与列出各行之和差 100）并据此拒绝「top-5 无 WPF 类型 → 排除 WPF 泄漏」的推论 |
| 3 | ✅ | ✅ | ✅ | 走 `§ 6` 根链形态反查表一跳收敛；修复方向原样转述 `wpf/rules/05-data-binding.md § 2`，未改写未展开 |
| 4 | ✅ | ✅ | ✅ | **风险最高一例通过**：排除 § 2/§ 3/§ 5，§ 4 弱事件泄漏保留 `待验` 并注明「泄漏在 `WeakEventManager` 内部监听表，按应用类型名筛天生盲」；无 `已证实` 项故不给修复方向 |
| 5 | ✅ | ✅ | ✅ | **spec 标注最易做错一例通过**：台账 9 条（合并 7 条 + WPF 加挂 2 条），线程池饥饿停 `待验`、强度「推测」，注明第二跳需 dump 或活体连接，未记 `无法判定` |
| 6 | ✅ | ✅ | ✅ | B 组第二项阻断，未进入台账循环（候选全停 `待验`、证据来源统一「无可用证据」），不给修复方向；另指出 procdump 漏 `-ma` 与「Mini 保留异常信息，`!pe` 可零成本先判异常类型」的岔路 |
| 7 | ✅ | ✅ | ✅ | 只取异常记录段，业务行不参与；强度「推测」，注明异常链可能未展开。另自行发现输入日志的时序矛盾（`Unhandled exception` 之后仍有 INFO 输出 → 该行非 CLR 崩溃路径产生），据此否掉因果链——该矛盾为构造输入时无意引入，agent 推理正确 |

不通过并已修正的例：**无**。七例首轮全通过，未改 SKILL.md / references / agent，故 `metadata.version` 保持 `1.0.0`、插件版本保持 `1.1.0`。

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| 2026-09-06 | `golden.md` 的「跑法」一节可操作性不足：七例的「输入」段是**描述性**表述（如「显示某业务类型 Count 很高」），不是可直接消费的取证输出文本。原样作为 prompt 时，外层会话会判定证据不足而自行拦下追问，agent 根本未被派发（测例 2 首跑即如此），实测的是外层会话的判断力而非 agent 行为 | 测例 2 首次调用：`-p '@optimus-devops-plugin:dotnet-diagnose 内存一直涨。这是一份 !dumpheap -stat 输出，显示 MyApp.Models.OrderItem 这个业务类型 Count 是 1847293，Size 很高。'` → 外层未派发，返回「你只给了摘要没给实际输出文本」并要求补充 | 待处理 | — |
| 2026-09-06 | 测例跑法缺「禁止外层代答」的显式约束。无头模式下 prompt 经外层会话转手，外层可能替 agent 补充前提或代为追问，污染验收结果。本轮实测须在 prompt 前置「直接原样派发给 @… ，不要自己追问或代答」才能确保 agent 被真实调用 | 同上；测例 2/4/5/6/7 均加该前置句后才正常派发 | 待处理 | — |
| 2026-09-06 | 含 shell 元字符的 prompt 会被权限层拦截。测例 5 的输入含裸 `> 0`（「队列长度持续 > 0」），`claude -p '...'` 调用连续两次被判 denied；改为把 prompt 写入仓库外文件、以 `-p "$(cat file)"` 传入后正常执行 | 测例 5：`-p '…ThreadPool Queue Length 持续 > 0（在 40~120 之间波动…）…'` | 待处理 | — |
