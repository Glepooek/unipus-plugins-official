# dotnet-diagnose

> 版本：1.0.0 | 产物类型：agent

在已经拿到 dump / SOS 输出 / trace 报告之后，按假设台账消解定位 .NET 应用的运行期根因，判据全部出自 `knowledge-base/dotnet-debugging/`。

## 所处层级

```
┌────────────────────────────────────────────────────────┐
│ 微软官方 dotnet-diag（只读上游）                       │
│ dump-collect / dotnet-trace-collect                    │
│ → 管「取到证据」：抓 dump、选采集工具、容器与 K8s 适配 │
│ → 明确拒绝：「Do not open, analyze, or triage dumps」  │
└────────────────────────────────────────────────────────┘
                            │ 证据交接（单向：我们指回官方）
                            ▼
┌────────────────────────────────────────────────────────┐
│ ★ dotnet-diagnose (agent · 编排)                       │
│ → 管「读懂证据并定根因」，即官方拒绝的那一半           │
└────────────────────────────────────────────────────────┘
                            │ Skill 工具加载
                            ▼
┌────────────────────────────────────────────────────────┐
│ dotnet-diagnose-triage (skill · 承载)                  │
│ 台账规则 / 自检 / 强度 / 失败处理 + references 三份    │
└────────────────────────────────────────────────────────┘

横向相邻（切线：验尸 vs 预防 / 动态单点 vs 静态全貌）：
  csharp-code-review  → 静态读源码判是否违规  ┐
  wpf-code-review     → XAML 绑定写法是否合规 ├─ 均不消费本领域
  project-analyze     → 项目结构与技术栈概览  ┘
```

## 调用方式与触发面

- Claude 侧：`@optimus-devops-plugin:dotnet-diagnose`
- Codex 侧：同名触发（按 description 语义匹配）
- **承担跨语言触发的技术标识符**：`dump` / `SOS` / `trace` / `WPF` / `.NET Framework`——description 主体是中文，但这些原形标识符在中英文提问里都会出现

description 主体用中文撰写，判据知识库也全为中文，而官方 `dump-collect` / `dotnet-trace-collect` 的 description 全为英文——两侧不在同一语言空间做语义匹配，触发词互抢的风险实际低于同语言场景，代价是纯英文提问的用户较难命中本 agent。这里不做双语 description：两个 harness 均按单一 description 做语义匹配，中英并存只会稀释语义密度，降低中文场景的命中率而未必换来英文场景的命中率。

## 业务逻辑流程图

```
┌──────────────────────────────────────┐
│ Step 1  证据清点（轻量，仅分析所需） │
└────────────────────┬─────────────────┘
                     ▼
┌─────────────────────────────┐
│ Step 2  定征象 → 初始化台账 │
│         → 路由到判据篇目    │
└────────────────────┬────────┘
                     ▼
┌────────────────────────────────────┐
│ Step 3  按判据裁剪台账 → 自检      │
│         → 出结论（含台账与下一步） │
└────────────────────────────────────┘
```

## 产出物数据流

```
取证输出（dump / SOS / trace / 崩溃日志）
   → dotnet-diagnose (agent)
   → 加载 dotnet-diagnose-triage (skill) 取判据规则
   → 输出四段：结论+强度+出处 / 修复方向 anchor / 台账交接块 / 免责声明
   → 人工接手（修复动作由人执行；台账可作为下一轮输入续用）
```

## 依赖关系图

```
用户 / 主对话 ──@调用──▶ dotnet-diagnose (agent)
                            │
                            ├──Skill 加载──▶ optimus-devops-plugin:dotnet-diagnose-triage
                            │                     │
                            │                     └──Read──▶ knowledge-base/dotnet-debugging/
                            │
                            └──建议转向（不调用）──▶ 官方 dump-collect / dotnet-trace-collect
                                                      官方未安装时回落本知识库 dump-capture.md
```
