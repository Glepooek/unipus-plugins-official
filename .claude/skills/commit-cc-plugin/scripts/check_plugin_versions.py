#!/usr/bin/env python3
"""校验每插件两份 plugin.json 的 version 是否同值。

版本真源是「两份 plugin.json 构成的一对」——改动插件内容后，两份在同一次改动内
一起升到同一个新值。不存在抄录关系与主从关系：新版本号由本次改动的性质决定
（见 AGENTS.md 版本管理规则的触发矩阵与幅度表），两份文件同等地是这个决定的记录。

因此发现不一致时，正确处置是回头判断本次改动该升什么号，然后把两份都写成那个号，
而不是拿一边覆盖另一边——那样有 50% 概率把正确的一边改错。
"""
import json
import pathlib
import sys

CLAUDE_ALLOWED_KEYS = {"name", "version", "agents"}


def _load(path):
    """返回 (data, err)。err 非 None 时 data 为 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as e:
        return None, f"无法解析 JSON：{e}"
    except OSError as e:
        return None, f"无法读取：{e}"


def check_plugin(plugin_dir):
    """校验单个插件目录，返回问题描述列表。"""
    name = plugin_dir.name
    claude_f = plugin_dir / ".claude-plugin" / "plugin.json"
    codex_f = plugin_dir / ".codex-plugin" / "plugin.json"

    # 两份都没有 → 不是本仓插件目录（如临时文件夹），跳过
    if not claude_f.exists() and not codex_f.exists():
        return []

    problems = []

    if not claude_f.exists():
        problems.append(
            f"[{name}] 缺 .claude-plugin/plugin.json"
            f"——Claude 侧会落到 git commit SHA 而非语义化版本")
        return problems
    if not codex_f.exists():
        problems.append(
            f"[{name}] 缺 .codex-plugin/plugin.json"
            f"——Codex 侧读不到该插件的版本号")
        return problems

    claude, err = _load(claude_f)
    if err:
        return [f"[{name}] .claude-plugin/plugin.json {err}"]
    codex, err = _load(codex_f)
    if err:
        return [f"[{name}] .codex-plugin/plugin.json {err}"]

    va, vb = claude.get("version"), codex.get("version")
    if va is None:
        problems.append(f"[{name}] .claude-plugin/plugin.json 缺 version 字段")
    if vb is None:
        problems.append(f"[{name}] .codex-plugin/plugin.json 缺 version 字段")

    if va is not None and vb is not None and va != vb:
        problems.append(
            f"[{name}] 两份 plugin.json 版本不一致："
            f".claude-plugin = {va}，.codex-plugin = {vb}。"
            f"请按本次改动的性质（见 AGENTS.md 版本管理规则的幅度表）确定应升到的版本号，"
            f"并把两份都改成该值")

    extra = set(claude) - CLAUDE_ALLOWED_KEYS
    if extra:
        problems.append(
            f"[{name}] .claude-plugin/plugin.json 有多余字段 {sorted(extra)}"
            f"——只应写 name / version / agents，其余元数据在 marketplace.json 声明，"
            f"重复维护会产生第二真源")

    return problems


def check_all(repo_root):
    """遍历 plugins/ 下所有目录，返回全部问题描述列表。"""
    repo_root = pathlib.Path(repo_root)
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.is_dir():
        return [f"plugins/ 目录不存在：{plugins_dir}"]

    problems = []
    for d in sorted(plugins_dir.iterdir()):
        if d.is_dir():
            problems.extend(check_plugin(d))
    return problems


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    problems = check_all(root)
    if problems:
        print("插件版本号校验未通过：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("插件版本号校验通过：所有插件的两份 plugin.json 同值")
    return 0


if __name__ == "__main__":
    sys.exit(main())
