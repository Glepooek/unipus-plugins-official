import json
import pathlib
import shutil
import tempfile
import unittest

from check_plugin_versions import check_all


def make_plugin(root, name, claude_ver, codex_ver, claude_extra=None):
    """在临时仓库里造一个插件。ver 传 None 表示不建该文件。"""
    base = root / "plugins" / name
    if claude_ver is not None:
        d = base / ".claude-plugin"
        d.mkdir(parents=True, exist_ok=True)
        body = {"name": name, "version": claude_ver}
        if claude_extra:
            body.update(claude_extra)
        (d / "plugin.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if codex_ver is not None:
        d = base / ".codex-plugin"
        d.mkdir(parents=True, exist_ok=True)
        (d / "plugin.json").write_text(
            json.dumps({"name": name, "version": codex_ver}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    base.mkdir(parents=True, exist_ok=True)
    return base


class TestCheckPluginVersions(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        (self.root / "plugins").mkdir()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_two_files_same_version_passes(self):
        make_plugin(self.root, "p-ok", "1.2.3", "1.2.3")
        self.assertEqual(check_all(self.root), [])

    def test_version_mismatch_is_reported_with_both_values(self):
        make_plugin(self.root, "p-bad", "1.0.2", "1.0.1")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("p-bad", problems[0])
        self.assertIn("1.0.2", problems[0])
        self.assertIn("1.0.1", problems[0])

    def test_error_message_does_not_name_an_authoritative_side(self):
        """报错措辞不得写「以某一份为准」——正确动作是回头判断本次改动该升什么号。"""
        make_plugin(self.root, "p-bad", "2.0.0", "1.0.0")
        msg = check_all(self.root)[0]
        for forbidden in ("以 .claude-plugin 为准", "以 .codex-plugin 为准", "为准"):
            self.assertNotIn(forbidden, msg)
        self.assertIn("本次改动", msg)

    def test_missing_claude_plugin_json_is_reported(self):
        make_plugin(self.root, "p-no-claude", None, "1.0.0")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".claude-plugin/plugin.json", problems[0])

    def test_missing_codex_plugin_json_is_reported(self):
        make_plugin(self.root, "p-no-codex", "1.0.0", None)
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn(".codex-plugin/plugin.json", problems[0])

    def test_missing_version_field_is_reported(self):
        base = self.root / "plugins" / "p-no-ver" / ".claude-plugin"
        base.mkdir(parents=True)
        (base / "plugin.json").write_text('{"name": "p-no-ver"}\n', encoding="utf-8")
        codex = self.root / "plugins" / "p-no-ver" / ".codex-plugin"
        codex.mkdir(parents=True)
        (codex / "plugin.json").write_text(
            '{"name": "p-no-ver", "version": "1.0.0"}\n', encoding="utf-8")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("version", problems[0])

    def test_invalid_json_is_reported_not_raised(self):
        base = self.root / "plugins" / "p-broken" / ".claude-plugin"
        base.mkdir(parents=True)
        (base / "plugin.json").write_text("{not json", encoding="utf-8")
        codex = self.root / "plugins" / "p-broken" / ".codex-plugin"
        codex.mkdir(parents=True)
        (codex / "plugin.json").write_text(
            '{"name": "p-broken", "version": "1.0.0"}\n', encoding="utf-8")
        problems = check_all(self.root)   # 不得抛异常
        self.assertEqual(len(problems), 1)
        self.assertIn("无法解析", problems[0])

    def test_multiple_plugins_all_reported(self):
        make_plugin(self.root, "p-ok", "1.0.0", "1.0.0")
        make_plugin(self.root, "p-bad1", "1.0.0", "2.0.0")
        make_plugin(self.root, "p-bad2", "3.0.0", "4.0.0")
        problems = check_all(self.root)
        self.assertEqual(len(problems), 2)

    def test_claude_side_extra_fields_are_reported(self):
        """.claude-plugin/plugin.json 只应有 name / version / agents。"""
        make_plugin(self.root, "p-extra", "1.0.0", "1.0.0",
                    claude_extra={"description": "不该写在这里"})
        problems = check_all(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("description", problems[0])

    def test_agents_field_is_allowed(self):
        make_plugin(self.root, "p-agents", "1.0.0", "1.0.0",
                    claude_extra={"agents": ["./agents/x.agent.md"]})
        self.assertEqual(check_all(self.root), [])

    def test_directory_without_any_plugin_json_is_skipped(self):
        """plugins/ 下可能有非插件目录（如临时文件夹），不报错。"""
        (self.root / "plugins" / "not-a-plugin").mkdir()
        self.assertEqual(check_all(self.root), [])


if __name__ == "__main__":
    unittest.main()
