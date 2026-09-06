import tempfile
import unittest
from pathlib import Path

from check_refs import (
    check_consumer,
    collect_consumers,
    extract_refs,
    normalize,
    parse_headings,
)


SPEC = """# 03 · MVVM 架构

## 1. MVVM 框架选型

## 2. ViewModel 基类与可绑定属性

### 2.1 属性变更通知

## 7. 事件与订阅
"""

# 章节标题本身含半角双引号——规范文件里合法且实际出现过
# （media/reference/audio-container-formats.md 曾为 `## 3. "后缀 vs 编码"的判断方法`）
SPEC_QUOTED_HEADING = """# 音频封装格式

## 3. "后缀 vs 编码"的判断方法
"""


class Fixture:
    """构造 <root>/knowledge-base/<domain>/rules|reference/ 与 <root>/plugins/... 的最小仓库结构。"""

    def __init__(self, tmp):
        self.root = Path(tmp)
        self.spec_dir = self.root / "knowledge-base" / "wpf" / "rules"
        self.spec_dir.mkdir(parents=True)
        (self.spec_dir / "03-mvvm.md").write_text(SPEC, encoding="utf-8")
        self.consumer_dir = self.root / "plugins" / "p" / "skills" / "s"
        self.consumer_dir.mkdir(parents=True)

    def consumer(self, body, name="SKILL.md"):
        path = self.consumer_dir / name
        path.write_text(body, encoding="utf-8")
        return path

    def quoted_heading_spec(self):
        """额外写入一份标题含半角双引号的规范文件，返回其领域内相对路径。"""
        (self.spec_dir.parent / "reference").mkdir(exist_ok=True)
        (self.spec_dir.parent / "reference" / "audio-container-formats.md").write_text(
            SPEC_QUOTED_HEADING, encoding="utf-8"
        )
        return "reference/audio-container-formats.md"


class TestNormalize(unittest.TestCase):
    def test_strips_backticks_and_bold(self):
        self.assertEqual(normalize("**`var` 与对象创建**"), "var 与对象创建")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize("  类型   与运算符 "), "类型 与运算符")


class TestParseHeadings(unittest.TestCase):
    def test_maps_number_to_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            headings = parse_headings(f.spec_dir / "03-mvvm.md")
            self.assertEqual(headings["1"], "MVVM 框架选型")
            self.assertEqual(headings["2"], "ViewModel 基类与可绑定属性")
            self.assertEqual(headings["2.1"], "属性变更通知")
            self.assertEqual(headings["7"], "事件与订阅")

    def test_ignores_h1_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            headings = parse_headings(f.spec_dir / "03-mvvm.md")
            self.assertNotIn("03", headings)


class TestExtractRefs(unittest.TestCase):
    def test_resolves_relative_path_via_file_level_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("规范见 knowledge-base/wpf/README.md\n\n| `rules/03-mvvm.md` §2 |\n")
            refs = extract_refs(c, f.root)
            self.assertEqual(refs, [(3, "wpf", "rules/03-mvvm.md", "2", None)])

    def test_splits_multiple_files_on_one_line(self):
        """一行引用两个文件时，每个 § 必须归属到它前面的那个文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "04-xaml.md").write_text("# 04\n\n## 9. 事件与命令\n", encoding="utf-8")
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §2；`rules/04-xaml.md` §9\n")
            refs = extract_refs(c, f.root)
            self.assertEqual([(r[2], r[3]) for r in refs],
                             [("rules/03-mvvm.md", "2"), ("rules/04-xaml.md", "9")])

    def test_captures_quoted_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §7「事件与订阅」\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")

    def test_captures_plain_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 7. 事件与订阅\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")

    def test_range_form_yields_no_bogus_title(self):
        """§1-§5 的连字符不得被当成标题文本。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §1-§2\n")
            self.assertEqual([r[4] for r in extract_refs(c, f.root)], [None, None])

    def test_bare_filename_uses_prior_file_dir_on_same_line(self):
        """同一行先出现完整路径、后用裸文件名省略写法时，裸名须归到前者所在目录。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "04-xaml.md").write_text("# 04\n\n## 9. 事件与命令\n", encoding="utf-8")
            c = f.consumer(
                "见 knowledge-base/wpf/rules/03-mvvm.md §2. ViewModel 基类；另见 `04-xaml.md` §9. 事件与命令\n")
            refs = extract_refs(c, f.root)
            self.assertEqual([r[2] for r in refs], ["rules/03-mvvm.md", "rules/04-xaml.md"])
            self.assertEqual(check_consumer(c, f.root)[0], [])

    def test_captures_title_in_double_quotes(self):
        """`§2 "CI 侧二次校验"` —— 引号形态除「」外还须认英文/全角双引号。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            for quoted in ('"事件与订阅"', '“事件与订阅”'):
                c = f.consumer(f'knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §7 {quoted}\n')
                self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅", quoted)
                self.assertEqual(check_consumer(c, f.root), ([], []), quoted)

    def test_captures_quoted_title_containing_halfwidth_quotes(self):
        """`§3「"后缀 vs 编码"的判断方法」` —— 章节标题自身含半角双引号时仍须可校验。

        回归锁：定界符集合曾与捕获组排除集共用 `"`（`[「“"][^」”"]+[」”"]`），
        导致标题含半角引号的章节无法写出任何能通过校验的引用——忠实照抄标题反而报失效。
        定界符须配对：`「…」` 只被 `」` 终止，内部的 `"` 属标题正文。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            rel = f.quoted_heading_spec()
            title = '"后缀 vs 编码"的判断方法'
            for quoted in (f"「{title}」", f"“{title}”"):
                c = f.consumer(
                    f"knowledge-base/wpf/README.md\n\n`{rel}` §3 {quoted}\n",
                    name=f"C{ord(quoted[0])}.md")
                self.assertEqual(extract_refs(c, f.root)[0][4], title, quoted)
                self.assertEqual(check_consumer(c, f.root), ([], []), quoted)

    def test_halfwidth_quoted_title_still_terminates_on_own_delimiter(self):
        """半角 `"…"` 形态不受本次放宽影响：它必须仍被下一个 `"` 终止。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer('knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §7 "事件与订阅"\n')
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")
            self.assertEqual(check_consumer(c, f.root), ([], []))

    def test_subsection_title_separated_by_space_only(self):
        """`§ 2.1 属性变更通知` —— 子章节号里的点已被编号吃掉，标题靠空格分隔。

        回归锁：曾因把「必须有点号分隔」当作标题判据，导致 csharp-code-review 已修好的
        5 处 `§ 2.x 标题` 集体退回脆弱引用状态。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 2.1 属性变更通知\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "属性变更通知")
            self.assertEqual(check_consumer(c, f.root), ([], []))

    def test_prose_continuation_after_number_is_not_a_title(self):
        """散文写法「§2 的 hook 不可绕过要求」中，§2 后面是句子续写而非标题。

        判据是结构而非标点枚举：带标题的引用，编号与标题之间必有分隔符
        （`§ 7. 集成测试` 的点号、`§7「事件与订阅」` 的书名号）；散文续写没有。
        这类引用按脆弱引用处理（无法交叉校验），不是失效。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer(
                "knowledge-base/wpf/README.md\n\n"
                "`rules/03-mvvm.md` §2 的可绑定属性要求源自本文件第 1 节\n")
            self.assertIsNone(extract_refs(c, f.root)[0][4])
            problems, fragile = check_consumer(c, f.root)
            self.assertEqual(problems, [])
            self.assertEqual(len(fragile), 1)

    def test_prose_continuation_without_space_is_not_a_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §7要求订阅须配对取消\n")
            self.assertIsNone(extract_refs(c, f.root)[0][4])
            self.assertEqual(check_consumer(c, f.root)[0], [])

    def test_plain_title_stops_at_chinese_period(self):
        """散文式引用「§ 7. 事件与订阅。后面还有一句」——句号后的内容不属于标题。

        skill 里的引用写在表格单元格中，靠 `、`/`；` 天然分隔，从没踩到这个边界；
        知识库正文是散文，句号才是句子终止符。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer(
                "knowledge-base/wpf/README.md\n\n"
                "通用原则见 `rules/03-mvvm.md` § 7. 事件与订阅。本篇只写差异：\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")
            self.assertEqual(check_consumer(c, f.root)[0], [])

    def test_plain_title_stops_at_fullwidth_comma(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer(
                "knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 1. MVVM 框架选型，另见下文\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "MVVM 框架选型")

    def test_plain_title_stops_at_closing_quote(self):
        """整句转述包裹引用时（「修复方向见 `x.md § 2. 标题`」），闭引号不属于标题。

        `plugins/*/skills/*/references/*.md` 纳入检查后首次出现的形态：判据句被原文
        转述、外层用「」包裹，闭引号紧跟标题之后。不排除会把它吞进标题判出假失效。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer(
                "原文即为：「修复方向见 `knowledge-base/wpf/rules/03-mvvm.md § 7. 事件与订阅`」。\n")
            self.assertEqual(extract_refs(c, f.root)[0][4], "事件与订阅")
            self.assertEqual(check_consumer(c, f.root)[0], [])

    def test_kb_spec_file_resolves_relative_ref_against_own_domain(self):
        """知识库正文里的 `rules/xxx.md` 相对引用，基准领域是该文件自身所在领域。

        skill 靠正文中出现的 knowledge-base/<domain>/ 定基准，知识库正文没有这种自指路径，
        只能从文件自身路径推断——否则同领域内的 `rules/...` § 引用一律无法解析。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            spec = f.spec_dir / "11-testing.md"
            spec.write_text("# 11\n\n分层见 `rules/03-mvvm.md` § 7. 事件与订阅\n", encoding="utf-8")
            refs = extract_refs(spec, f.root)
            self.assertEqual([(r[1], r[2], r[4]) for r in refs],
                             [("wpf", "rules/03-mvvm.md", "事件与订阅")])
            self.assertEqual(check_consumer(spec, f.root)[0], [])

    def test_kb_cross_domain_full_path_overrides_own_domain(self):
        """正文写完整跨领域路径时，按路径里的领域解析，不被自身领域覆盖。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            other = f.root / "knowledge-base" / "csharp" / "rules"
            other.mkdir(parents=True)
            (other / "12-testing.md").write_text("# 12\n\n## 1. 测试策略与金字塔\n", encoding="utf-8")
            spec = f.spec_dir / "11-testing.md"
            spec.write_text(
                "# 11\n\n通用原则见 `knowledge-base/csharp/rules/12-testing.md` § 1. 测试策略与金字塔。"
                "WPF 侧的差异：\n", encoding="utf-8")
            refs = extract_refs(spec, f.root)
            self.assertEqual([(r[1], r[2], r[4]) for r in refs],
                             [("csharp", "rules/12-testing.md", "测试策略与金字塔")])
            self.assertEqual(check_consumer(spec, f.root)[0], [])

    def test_ambiguous_domain_skips_relative_refs(self):
        """一个文件引用了两个领域时，相对路径无法定基准，不猜。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md knowledge-base/csharp/README.md\n\n`rules/03-mvvm.md` §2\n")
            self.assertEqual(extract_refs(c, f.root), [])


class TestCheckConsumer(unittest.TestCase):
    def test_passes_when_number_and_title_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 7. 事件与订阅\n")
            problems, fragile = check_consumer(c, f.root)
            self.assertEqual((problems, fragile), ([], []))

    def test_detects_renumbered_section_via_title_mismatch(self):
        """核心场景：章节重编号后号仍存在，但标题对不上——必须报错。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 1. 事件与订阅\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("标题不符", problems[0])
            self.assertIn("MVVM 框架选型", problems[0])

    def test_detects_missing_section_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 99. 不存在的章节\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("无 § 99 章节", problems[0])

    def test_lists_existing_numbers_in_error(self):
        """报错须列出现有章节号，便于直接修复。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 99. x\n")
            problems, _ = check_consumer(c, f.root)
            self.assertIn("1, 2, 2.1, 7", problems[0])

    def test_detects_missing_target_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/99-gone.md` § 1. x\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(len(problems), 1)
            self.assertIn("引用的文件不存在", problems[0])

    def test_bare_number_reported_as_fragile_not_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` §2、§7\n")
            problems, fragile = check_consumer(c, f.root)
            self.assertEqual(problems, [])
            self.assertEqual(len(fragile), 2)
            self.assertIn("ViewModel 基类与可绑定属性", fragile[0])

    def test_title_prefix_match_accepted(self):
        """引用只写标题前半段（如省略括注）时视为匹配，避免逼迫逐字复制。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            (f.spec_dir / "06-controls.md").write_text(
                "# 06\n\n## 8. 绘制与图形（联动 08 章）\n", encoding="utf-8")
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/06-controls.md` § 8. 绘制与图形\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(problems, [])

    def test_subsection_number_checked_independently(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            c = f.consumer("knowledge-base/wpf/README.md\n\n`rules/03-mvvm.md` § 2.1 属性变更通知\n")
            problems, _ = check_consumer(c, f.root)
            self.assertEqual(problems, [])


class TestCollectConsumers(unittest.TestCase):
    def test_finds_skill_and_reference_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            f.consumer("x")
            f.consumer("y", name="CLI-REFERENCE.md")
            names = {p.name for p in collect_consumers(f.root)}
            self.assertTrue({"SKILL.md", "CLI-REFERENCE.md"} <= names)

    def test_finds_kb_spec_and_reference_files(self):
        """知识库正文自身也是消费者——去重产生的跨领域 § 引用就写在这里。"""
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            ref_dir = f.root / "knowledge-base" / "wpf" / "reference"
            ref_dir.mkdir(parents=True)
            (ref_dir / "why-mvvm.md").write_text("# why\n", encoding="utf-8")
            rels = {p.relative_to(f.root).as_posix() for p in collect_consumers(f.root)}
            self.assertIn("knowledge-base/wpf/rules/03-mvvm.md", rels)
            self.assertIn("knowledge-base/wpf/reference/why-mvvm.md", rels)

    def test_ignores_kb_changelog_and_readme(self):
        """知识库的 CHANGELOG 与 README 记录的是历史事实与消费方式说明，不校验。

        7.2.1 起 CHANGELOG 按领域拆分（不再有根 knowledge-base/CHANGELOG.md），
        领域级 CHANGELOG.md 同样不应被当作消费者扫描。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            kb = f.root / "knowledge-base"
            (kb / "README.md").write_text("可写死 `file` § `章节` 引用\n", encoding="utf-8")
            (kb / "wpf" / "README.md").write_text("# wpf\n", encoding="utf-8")
            (kb / "wpf" / "CHANGELOG.md").write_text("`rules/99-gone.md` §1 迁移记录\n", encoding="utf-8")
            rels = {p.relative_to(f.root).as_posix() for p in collect_consumers(f.root)}
            self.assertNotIn("knowledge-base/README.md", rels)
            self.assertNotIn("knowledge-base/wpf/README.md", rels)
            self.assertNotIn("knowledge-base/wpf/CHANGELOG.md", rels)

    def test_ignores_changelog(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(tmp)
            f.consumer("x")
            f.consumer("历史记录里的 `rules/99-gone.md` § 1 不该被校验", name="CHANGELOG.md")
            names = {p.name for p in collect_consumers(f.root)}
            self.assertNotIn("CHANGELOG.md", names)


if __name__ == "__main__":
    unittest.main()
