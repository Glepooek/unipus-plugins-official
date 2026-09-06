#!/usr/bin/env python3
"""校验消费者 skill 中对 knowledge-base 章节号（`§ N`）引用的有效性。

`check_index.py` 校验的是 index.jsonl 的 anchor（标题**文本**），管不到 skill 正文里
写的 `§ 7` 这类**位置引用**——规范文件章节重编号后，`§ 7` 依然「存在」，只是指向了
别的内容，不会有任何报错。本脚本填这个缺口。

三类检查：
- **存在性**：引用的章节号在目标文件中有对应标题。
- **一致性**：引用同时写了标题文本时，该文本须与章节号对应的标题匹配——
  这是真正能挡住重编号的一环，因为号和标题必须同时对得上。
- **脆弱性报告**：只写章节号、没写标题的引用无法做一致性校验，
  重编号时会静默失效。这类引用会被列出并建议补标题，但不算失败。

用法：
    python check_refs.py            # 校验全部消费者
    python check_refs.py --strict   # 把脆弱引用也算作失败
"""
import re
import sys
from pathlib import Path

# 消费者文件：plugins 下的 SKILL.md 与被 skill 引用的参考文档，以及知识库正文自身
# ——跨领域去重会在正文里留下 `csharp/rules/12-testing.md § 1` 这类引用，形态与 skill
# 里的一样脆弱。knowledge-base 的 CHANGELOG/README 与领域 README.md 不在其中：
# 前两者记录历史事实与消费方式说明，后者是文件地图（只列路径不引章节）。
CONSUMER_GLOBS = (
    "plugins/*/skills/*/SKILL.md",
    "plugins/*/skills/*/*REFERENCE*.md",
    "plugins/*/skills/*/references/*.md",
    "knowledge-base/*/rules/*.md",
    "knowledge-base/*/reference/*.md",
)

# 领域识别：任何 knowledge-base/<domain>/ 出现处，用于给相对路径引用定基准
# （领域元数据文件与根 README 同名，故领域提取与文件路径提取分开）
DOMAIN_RE = re.compile(r'knowledge-base/(?P<domain>[a-z0-9-]+)/')

# 目标文件 token：完整路径 / 领域内相对路径 / 同目录裸文件名
FULL_PATH_RE = re.compile(r'knowledge-base/(?P<domain>[a-z0-9-]+)/(?P<rel>(?:rules|reference)/[a-z0-9][a-z0-9-]*\.md)')
REL_PATH_RE = re.compile(r'`(?P<rel>(?:rules|reference)/[a-z0-9][a-z0-9-]*\.md)`')
BARE_NAME_RE = re.compile(r'`(?P<name>[a-z0-9][a-z0-9-]*\.md)`')

# 章节引用：§ 后跟编号，可选跟标题（引号包裹，或 `.`/空格 分隔的裸文本）
#
# 引号形态认「」/""/“”三种——实际写法都出现过，只认一种会把另两种判成脆弱引用。
# 三种形态各写一个分支、各自只排除自己的闭定界符，不能合并成
# `[「“"][^」”"]+[」”"]`：那样写等于隐式规定「章节标题不得含半角双引号」，
# 因为标题里的 `"` 会提前终止捕获。规范文件的标题含半角引号是合法的
# （如 `## 3. "后缀 vs 编码"的判断方法`），此时忠实照抄标题的引用反而会被
# 判成失效——校验器不该反过来限制被校验内容的用字。
#
# 两处不能放宽：
# 1. 编号与裸标题之间必须有 `.`/`．`/空格 分隔——`§7要求订阅须配对` 里紧贴编号的
#    文字是句子续写，不是标题。
# 2. 空格分隔的形态还须排除以助词/动词打头的续写：`§2 的 hook 不可绕过要求`、
#    `§3 要求 CI 集成 secret scanning` 都是散文，不是标题。这类按裸引用（脆弱、
#    不可交叉校验）处理，而不是拿续写文本去比标题得出假失效。
#    点号分隔的形态无此歧义（`§ 7. 集成测试`），不做该排除。
#    子章节形态 `§ 2.1 属性变更通知` 只能靠空格分隔（点号已被编号吃掉），所以不能
#    简单地要求"必须有点号"——那会让所有 `§ N.M 标题` 退回脆弱状态。
# 裸标题的终止符含中文句号与全角逗号：正文是散文，「§ 7. 集成测试。WPF 侧只补一条：」
# 里句号之后不属于标题；skill 的引用写在表格单元格中靠 `、`/`；` 分隔，踩不到这个边界。
PROSE_LEAD = r'的|地|得|要求|规定|说明|定义|提到|指出|所述|中|里|与|和|及'
SECTION_RE = re.compile(
    r'§\s*(?P<num>\d+(?:\.\d+)*)'
    r'(?:'
    r'\s*「(?P<cjk>[^」]+)」'
    r'|\s*“(?P<curly>[^”]+)”'
    r'|\s*"(?P<straight>[^"]+)"'
    r'|\s*[.．]\s*(?P<plain>[^§|；;、。，\n]*)'
    rf'|[ 　](?!(?:{PROSE_LEAD}))(?P<spaced>[^§|；;、。，\n]*)'
    r')?'
)

# 目标文件标题：## / ### 等，编号在标题文本开头
HEADING_RE = re.compile(r'^(#{2,6})\s+(?P<num>\d+(?:\.\d+)*)[.．]?\s+(?P<text>.+)$')

# 标题被判定为"实际没写标题"的形态：空、纯标点、范围连字符残留
NOISE_TITLE_RE = re.compile(r'^[-—－、；;。，,：:\s]*$')


def normalize(text):
    """去反引号、折叠空白，与 check_index.py 的 normalize_heading 保持一致的宽松度。"""
    return re.sub(r'\s+', ' ', text.replace('`', '').replace('*', '')).strip()


def parse_headings(path):
    """返回 {章节号: 标题文本}。同号重复出现时保留首个（正常规范文件不应出现）。"""
    headings = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = HEADING_RE.match(line)
        if m and m.group("num") not in headings:
            headings[m.group("num")] = normalize(m.group("text"))
    return headings


def iter_file_segments(line, default_domain, last_dir):
    """把一行按目标文件 token 切段，产出 (领域, 领域内相对路径, 该文件之后的文本, 新的 last_dir)。

    一行可以引用多个文件（例如 `rules/13-api-design.md` § 2；`rules/05-error-handling.md` 全篇），
    每个文件只认领它之后、下一个文件 token 之前的 § 引用。
    """
    tokens = []
    for m in FULL_PATH_RE.finditer(line):
        tokens.append((m.start(), m.end(), m.group("domain"), m.group("rel")))
    for m in REL_PATH_RE.finditer(line):
        if default_domain and not any(s <= m.start() < e for s, e, _, _ in tokens):
            tokens.append((m.start(), m.end(), default_domain, m.group("rel")))

    # 裸文件名（同目录省略写法）需要目录上下文：优先取本行前面已出现的文件所在目录，
    # 否则回退到上一行遗留的 last_dir。必须在收集完带路径的 token 之后再算。
    tokens.sort()
    for m in BARE_NAME_RE.finditer(line):
        if any(s <= m.start() < e for s, e, _, _ in tokens):
            continue
        if not default_domain:
            continue
        prior = [rel for s, _, _, rel in tokens if s < m.start() and "/" in rel]
        ctx = prior[-1].rsplit("/", 1)[0] if prior else last_dir
        if ctx:
            tokens.append((m.start(), m.end(), default_domain, f"{ctx}/{m.group('name')}"))

    tokens.sort()
    for i, (_, end, domain, rel) in enumerate(tokens):
        stop = tokens[i + 1][0] if i + 1 < len(tokens) else len(line)
        last_dir = rel.rsplit("/", 1)[0] if "/" in rel else last_dir
        yield domain, rel, line[end:stop], last_dir


def own_domain(consumer_path, repo_root):
    """消费者本身就是知识库正文时，返回它所属领域，否则 None。

    知识库正文里的 `rules/xxx.md` 相对引用没有自指的 knowledge-base/<domain>/ 路径可依，
    只能从文件自身位置推断基准领域；skill 不在知识库内，返回 None 走内容提取那条路。
    """
    try:
        parts = consumer_path.relative_to(repo_root).parts
    except ValueError:
        return None
    return parts[1] if len(parts) > 2 and parts[0] == "knowledge-base" else None


def extract_refs(consumer_path, repo_root):
    """从消费者文件提取 (行号, 领域, 相对路径, 章节号, 引用标题或 None) 五元组。"""
    text = consumer_path.read_text(encoding="utf-8")

    # 相对路径引用的基准领域：知识库正文取自身所在领域；skill 取正文中唯一出现的领域名
    # （出现多个领域时无法定基准，不猜）。完整路径引用不受此影响，各自按路径里的领域解析。
    default_domain = own_domain(consumer_path, repo_root)
    if default_domain is None:
        domain_names = set(DOMAIN_RE.findall(text))
        default_domain = next(iter(domain_names)) if len(domain_names) == 1 else None

    refs = []
    last_dir = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        for domain, rel, tail, last_dir in iter_file_segments(line, default_domain, last_dir):
            for m in SECTION_RE.finditer(tail):
                title = (m.group("cjk") or m.group("curly") or m.group("straight")
                         or m.group("plain") or m.group("spaced") or "")
                title = normalize(title)
                if NOISE_TITLE_RE.match(title):
                    title = None
                refs.append((line_no, domain, rel, m.group("num"), title))
    return refs


def check_consumer(consumer_path, repo_root):
    """返回 (problems, fragile)：problems 为失效引用，fragile 为无标题的不可校验引用。"""
    problems, fragile = [], []
    rel_consumer = consumer_path.relative_to(repo_root).as_posix()
    heading_cache = {}

    for line_no, domain, rel, num, title in extract_refs(consumer_path, repo_root):
        target = repo_root / "knowledge-base" / domain / rel
        if target not in heading_cache:
            heading_cache[target] = parse_headings(target) if target.exists() else None
        headings = heading_cache[target]

        if headings is None:
            problems.append(f"{rel_consumer}:{line_no}: 引用的文件不存在：knowledge-base/{domain}/{rel}")
            continue
        if num not in headings:
            problems.append(
                f"{rel_consumer}:{line_no}: knowledge-base/{domain}/{rel} 无 § {num} 章节"
                f"（该文件现有章节号：{', '.join(sorted(headings, key=lambda s: [int(x) for x in s.split('.')]))}）"
            )
            continue
        if title is None:
            fragile.append(f"{rel_consumer}:{line_no}: § {num} → {domain}/{rel}（现为「{headings[num]}」）")
            continue
        actual = headings[num]
        if title not in actual and not actual.startswith(title):
            problems.append(
                f"{rel_consumer}:{line_no}: knowledge-base/{domain}/{rel} § {num} 标题不符——"
                f"引用写「{title}」，实际为「{actual}」"
            )
    return problems, fragile


def collect_consumers(repo_root):
    found = []
    for pattern in CONSUMER_GLOBS:
        found.extend(sorted(repo_root.glob(pattern)))
    return found


def main():
    repo_root = Path(__file__).resolve().parents[4]
    strict = "--strict" in sys.argv[1:]

    all_problems, all_fragile, checked = [], [], 0
    for consumer in collect_consumers(repo_root):
        problems, fragile = check_consumer(consumer, repo_root)
        all_problems.extend(problems)
        all_fragile.extend(fragile)
        checked += 1

    total = len(all_problems) + len(all_fragile)
    if all_fragile:
        print(f"⚠️ {len(all_fragile)} 处引用只写了章节号、未写标题，无法交叉校验，章节重编号时会静默失效：")
        for f in all_fragile:
            print(f"   {f}")
        print("   建议补上标题文本（形如 `§ 2.2 类型与运算符` 或 `§2「码率控制模式」`），使其可被自动校验。\n")

    if all_problems:
        for p in all_problems:
            print(p, file=sys.stderr)
        print(f"\n共 {len(all_problems)} 处失效引用", file=sys.stderr)
        sys.exit(1)
    if strict and all_fragile:
        print(f"--strict 模式：{len(all_fragile)} 处脆弱引用视为失败", file=sys.stderr)
        sys.exit(1)

    print(f"OK: 检查 {checked} 个消费者文件，章节号引用全部有效"
          + (f"（其中 {len(all_fragile)} 处为不可校验的裸引用）" if all_fragile else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
