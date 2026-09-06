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

| 日期 | 问题描述 | 触发场景/prompt | 状态 | 优化后版本 |
|---|---|---|---|---|
| — | 暂无记录 | — | — | — |
