---
name: dotnet-diagnose-triage
description: 解读已取得的 .NET 取证输出并按假设台账定位根因：SOS 命令输出逐列语义、dump 类型与符号的可用性前置校验、假设消解与跨轮续用、WPF 专属归因（Dispatcher 死锁与四类泄漏堆形态）、.NET Framework 4.x 分析侧。判据全部引用 knowledge-base/dotnet-debugging/，不复制正文。触发词：这个 dump 说明什么问题、SOS 输出怎么读、!dumpheap 结果分析、!syncblk 死锁判断、!gcroot 根链读法、托管内存泄漏定位、线程池饥饿判断、WPF 窗口关不掉泄漏、崩溃日志异常链、analyze dump output、read SOS output。不做取证抓取——需要抓 dump 或选采集工具时转 dump-collect / dotnet-trace-collect。
metadata:
  version: "1.0.0"
  author: desktop client team
  category: quality
compatibility: 纯文本推理，无运行时依赖。判据来源 knowledge-base/dotnet-debugging/（须与本仓库同处一个工作树才能读到）。不执行任何诊断命令——抓取 dump 与采集 trace 由用户自行完成或转微软官方 dotnet-diag 插件。
allowed-tools: Read Glob Grep
---

# .NET 取证输出解读与根因定位

## 概述

本 skill 是 `dotnet-diagnose` agent 的承载层，把 `knowledge-base/dotnet-debugging/` 的 74 条判据组织成可执行的**假设消解循环**。

**做什么**：读懂已经拿到的证据（dump / SOS 输出 / trace 报告 / 崩溃日志），按知识库判据裁剪候选根因，给出带出处与强度标注的结论。

**不做什么**：不抓 dump、不选采集工具、不执行任何诊断命令。这一半由微软官方 `dump-collect` / `dotnet-trace-collect` 覆盖且更完备（含容器与 K8s 适配），我们专做官方明确拒绝的分析侧。

**为什么核心数据结构是台账而不是流程步骤**：知识库每条命令条目的第 4 段固定为「判据：能证实 / 排除什么假设」，这些判据在语义上就是假设集上的消解算子；两张决策表的「候选根因」列就是初始假设集。因此本 skill 只需写清循环规则，判据本身一律按 `file § anchor` 引用。

## 假设台账

## 出结论前的自检

## 三种结论强度

## 失败处理

## 与官方产物的交接

## dump 处置合规
