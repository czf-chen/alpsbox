# -*- coding: utf-8 -*-
"""Release integrity test for the v1.0.0 public layout.

Goals: any reader arriving from GitHub can tell, without reading source code:
  * what the tool does (per-subject ALPS + QC) and what it deliberately does
    NOT do (group statistics / clinical diagnosis);
  * that ALPS has no official/standard implementation;
  * that this repository's "reference implementation" means the MIT-licensed
    gbarisano/alps alps.sh (with commit, licence and companion paper);
  * where the bundled ROI masks come from (source, licence, sha256).

It also guards against regressions in the release structure: English-first
entry point with a language switcher, Chinese mirror, docs index, changelog,
one-paragraph-per-reference citation formatting, and no group-analysis
functionality in the shipped package.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from alpsbox import citations as C  # noqa: E402
from alpsbox import helptext, help_pages, i18n, report  # noqa: E402
# Import every user-facing module so that all message catalogs are registered
# before the English-translation audit below.
from alpsbox import qc, plotting, roi_preview  # noqa: E402,F401
from alpsbox import text_cli, text_pipeline, text_qc  # noqa: E402,F401
from alpsbox import text_report, text_roi, text_ui  # noqa: E402,F401

# Tests must not write the user's language preference
i18n.set_lang("zh_CN", save=False)

failures = []


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


# The documented startup default is English, independent of system locale
# or a previously saved preference.
check(i18n.init_lang() == "en", "startup language is English")
i18n.set_lang("zh_CN", save=False)


def read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


# =====================================================================
# 1. citations.py constants
# =====================================================================
print("=== 1. citations.py ===")
check(C.REPO_URL == "https://github.com/gbarisano/alps", "reference repo URL")
check(re.fullmatch(r"[0-9a-f]{40}", C.REPO_COMMIT) is not None,
      "reference commit is a 40-char sha")
check(C.ACCESS_DATE and re.fullmatch(r"\d{4}-\d{2}-\d{2}", C.ACCESS_DATE),
      "access date formatted")
check("MIT License" in C.CITATION_REF_SOFTWARE, "software citation states MIT")
check(C.REPO_COMMIT in C.CITATION_REF_SOFTWARE, "software citation has commit")
check("doi:10.14336/AD.2023.0321-2" in C.CITATION_REF_PAPER,
      "companion paper DOI")
check("2024;15(4):1885-1898" in C.CITATION_REF_PAPER,
      "companion paper volume/issue/pages")
check("doi:10.1007/s11604-017-0617-z" in C.CITATION_ALPS_METHOD,
      "Taoka 2017 DOI")
check("2017;35(4):172-178" in C.CITATION_ALPS_METHOD, "Taoka 2017 pages")
check("ROIs_JHU_ALPS" in C.CITATION_ROI_MASKS
      and "MIT" in C.CITATION_ROI_MASKS, "ROI mask provenance citation")
for lang, name in (("zh_CN", "REFERENCE_CITATION_ZH"),
                   ("en", "REFERENCE_CITATION_EN")):
    v = getattr(C, name)
    check(all(t in v for t in (C.REPO_URL, C.REPO_COMMIT[:7],
                               "10.14336/AD.2023.0321-2",
                               "10.1007/s11604-017-0617-z")),
          "%s has repo/commit/both DOIs" % name)
check(len(C.ref_defaults_table()) >= 4, "reference-implementation defaults table")

# one reference per paragraph (blank line between entries)
_joined = C.format_citations([C.CITATION_ALPS_METHOD, C.CITATION_REF_SOFTWARE,
                              C.CITATION_REF_PAPER])
_paras = [p for p in _joined.split("\n\n") if p.strip()]
check(len(_paras) == 3, "format_citations: one reference per paragraph")
check(all("\n" not in p.strip() or p.strip().count("\n") == 0
          for p in _paras), "format_citations: no references packed on one line")

# =====================================================================
# 2. Release files and English-first entry point
# =====================================================================
print("\n=== 2. Repository files ===")
readme = read("README.md")
readme_zh = read("README.zh-CN.md")
citations_md = read("docs/CITATIONS.md")
prov = read(os.path.join("alpsbox", "data", "ROIs_JHU_ALPS", "PROVENANCE.md"))
cff = read("CITATION.cff")
changelog = read("CHANGELOG.md")

check(readme.lstrip().startswith("# ALPSbox"), "README is English-first")
check("README.zh-CN.md" in readme, "README links the Chinese mirror")
check("README.md" in readme_zh, "Chinese README links back to English")
check("docs/" in readme, "README links docs/")
check("CITATION.cff" in readme, "README links CITATION.cff")
check("PROVENANCE.md" in readme, "README links ROI provenance")
check("LICENSE" in readme and "LICENSE_Barisano_alps.txt" in readme,
      "README licence section points at both code and ROI licences")

for rel in ("docs/README.md", "docs/INSTALL.md", "docs/FAQ.md",
            "docs/CITATIONS.md", "docs/VALIDATION.md", "docs/WHY_ALPSBOX.md",
            "docs/zh-CN/README.md", "docs/zh-CN/INSTALL.md",
            "docs/zh-CN/FAQ.md", "docs/zh-CN/CITATIONS.md",
            "docs/zh-CN/VALIDATION.md", "docs/zh-CN/WHY_ALPSBOX.md",
            "CHANGELOG.md", "CITATION.cff", "LICENSE",
            "LICENSE_Barisano_alps.txt", ".gitignore",
            "examples/demo_synthetic_cohort/README.md",
            "examples/demo_synthetic_cohort/README.zh-CN.md"):
    check(os.path.isfile(os.path.join(ROOT, rel)), "file exists: %s" % rel)

check("1.0.0" in changelog, "CHANGELOG starts at v1.0.0")
check("## [1.0.0]" in changelog, "CHANGELOG has a 1.0.0 section")
check("0.10.0" not in changelog, "CHANGELOG has no pre-release history")

for label, text in (("README", readme), ("README.zh-CN", readme_zh),
                    ("docs/CITATIONS.md", citations_md),
                    ("docs/zh-CN/CITATIONS.md",
                     read("docs/zh-CN/CITATIONS.md"))):
    check(C.REPO_URL in text, "%s has reference repo URL" % label)
    check(C.REPO_COMMIT in text or C.REPO_COMMIT[:7] in text,
          "%s has commit" % label)
    check("MIT" in text, "%s has MIT licence" % label)
    check("10.14336/AD.2023.0321-2" in text, "%s has companion DOI" % label)
    check("10.1007/s11604-017-0617-z" in text, "%s has Taoka DOI" % label)

lic = read("LICENSE")
check("MIT License" in lic and "ALPSbox contributors" in lic,
      "root LICENSE (code): MIT + copyright")
check("sha256" in prov and "MIT" in prov, "PROVENANCE has sha256 and MIT")
for fn, sha in (
        ("L_SCR.nii.gz",
         "20c1ffd62c349aab3d2775735d46c2d6368a9fc50e567d5688721d164c28046c"),
        ("L_SLF.nii.gz",
         "e487cad947663c311109bb15b5876b9e824f0ee6f25169c0f1b398cdc6eeb8c2"),
        ("R_SCR.nii.gz",
         "6389228ac11f5b1ea7233db82a66174a59ba3672c99d36b798de989a5243b199"),
        ("R_SLF.nii.gz",
         "79ef530240a88558339de1f1d84643700c77469da9b9d1c658a74ed80a389e15")):
    check(fn in prov and sha in prov, "PROVENANCE records %s sha256" % fn)
check("cff-version: 1.2.0" in cff and "type: software" in cff,
      "CITATION.cff structure")
check("10.14336/AD.2023.0321-2" in cff and "gbarisano/alps" in cff,
      "CITATION.cff has both-paper/repo references")
check('version: "1.0.0"' in cff, "CITATION.cff version matches release")

# positioning: per-subject only, group analysis is downstream
position_markers = ("does not", "not a", "out of scope", "downstream")
check(any(m in readme.lower() for m in position_markers),
      "README states what the tool does not do")
check("group" in readme.lower(), "README mentions group statistics are downstream")

# =====================================================================
# 3. GUI / user-visible text
# =====================================================================
print("\n=== 3. GUI text ===")
roi_label = i18n.STRINGS["proc.roi_bundled"]
check("gbarisano/alps" in roi_label["zh_CN"]
      and "gbarisano/alps" in roi_label["en"], "ROI source label names repo")
for key in ("tip.bet_f", "tip.reg_cost", "tip.template", "tip.denoise"):
    for lang in ("zh_CN", "en"):
        v = i18n.STRINGS[key][lang]
        marker = "文献：" if lang == "zh_CN" else "Reference"
        check(marker in v, "%s[%s] has formal citation marker" % (key, lang))
        check("10.14336/AD.2023.0321-2" in v,
              "%s[%s] has companion DOI" % (key, lang))
        check("gbarisano/alps" in v, "%s[%s] names reference repo" % (key, lang))

for lang, marker, no_off in (("zh_CN", "没有官方", "没有官方"),
                             ("en", "no official", "no official")):
    i18n.set_lang(lang, save=False)
    refs = helptext.references_text()
    check("gbarisano/alps" in refs, "references page[%s] names repo" % lang)
    check("10.14336/AD.2023.0321-2" in refs, "references page[%s] has paper" % lang)
    check(no_off in refs.lower(), "references page[%s] says no official" % lang)
    body = help_pages.body("method")
    check(C.REPO_URL in body, "help-method[%s] names repo" % lang)
    check("10.14336/AD.2023.0321-2" in body, "help-method[%s] has paper" % lang)
    home = help_pages.body("quickstart")
    check("group" in home.lower() or "组" in home,
          "help-quickstart[%s] mentions group scope" % lang)

# every registered English translation must be free of Chinese characters
# (home.more_langs legitimately lists language names in their own scripts)
CJK = re.compile(r"[\u4e00-\u9fff]")
ALLOW_CJK_KEYS = {"home.more_langs"}
bad_en = []
for key, entry in i18n.STRINGS.items():
    en = entry.get("en")
    if key in ALLOW_CJK_KEYS:
        continue
    if en and CJK.search(str(en)):
        bad_en.append(key)
check(not bad_en, "no CJK left in English GUI strings (%r)"
      % (bad_en or "none"))

# HTML report (report.py): English output must stay free of Chinese text, and
# the batch report must not compute group-level statistics.
_REC = {
    "subject": "demo", "ok": True, "method": "eddy_gpu", "qc": "需注意",
    "alps_L": "1.284382", "alps_R": "1.565163", "alps_mean": "1.424773",
    "r_wm": "0.781061", "rms_rel_mean": "0.167252", "n_vol": 66,
    "n_outlier": 20, "bet_f": "0.500000",
    "regqc_range_pct": "9.075536", "regqc_level": "提示",
}
_report_dir = tempfile.mkdtemp(prefix="alpsbox_rpt_")
_en_html = report.build_html(_REC, os.path.join(_report_dir, "en.html"),
                             lang="en")
_en_text = open(_en_html, encoding="utf-8").read()
check('<html lang="en">' in _en_text, "English report declares lang=en")
check("ALPS analysis report" in _en_text, "English report has English title")
check(not CJK.search(_en_text), "English report has no CJK characters")
check("no official standard implementation" in _en_text,
      "English report keeps the no-official-implementation note")
_zh_html = report.build_html(_REC, os.path.join(_report_dir, "zh.html"),
                             lang="zh_CN")
_zh_text = open(_zh_html, encoding="utf-8").read()
check('<html lang="zh-CN">' in _zh_text and "ALPS 分析报告" in _zh_text,
      "Chinese report keeps its zh-CN title")
_en_batch = report.build_batch_html(
    [_REC, {"subject": "bad", "ok": False}],
    os.path.join(_report_dir, "en_batch.html"), lang="en")
_en_batch_text = open(_en_batch, encoding="utf-8").read()
check(not CJK.search(_en_batch_text), "English batch report has no CJK")
check("ALPS_mean 均值" not in _en_batch_text
      and "standard deviation" not in _en_batch_text.lower(),
      "batch report has no group-level statistics")

i18n.set_lang("zh_CN", save=False)

# CLI parser: no group subcommand, reference source in help
from alpsbox import cli  # noqa: E402

parser = cli.build_parser()
for act in parser._actions:
    if act.dest == "cmd":
        check("group" not in act.choices, "CLI has no group subcommand")
        run_help = " ".join(
            " ".join(sa.option_strings) + " " + (sa.help or "")
            for sa in act.choices["run"]._actions)
        check("--no-bundled-roi" in run_help, "CLI flag --no-bundled-roi")
        check("--no-official-roi" in run_help,
              "legacy alias --no-official-roi retained")
        check("gbarisano/alps" in run_help, "CLI help names reference repo")
        break
else:
    check(False, "CLI parser exposes subcommands")

# =====================================================================
# 3b. Tool text hygiene
# =====================================================================
# User-facing text must not promise unimplemented features, define the
# audience, or quote this lab's internal research data (external users do
# not have those data).
print("\n=== 3b. Tool text hygiene ===")
FORBIDDEN = (
    "更多语言", "more languages", "日本語", "한국어", "deutsch",
    "非影像专业", "non-imaging", "made for non-imaging",
    "本工具实测", "本工具健康对照", "n=24", "外部 15 例", "24 例健康",
    "课题组", "本课题", "v4 手工", "p0 验证", "独有", "唯一", "优势",
)
bad_text = []
for key, entry in i18n.STRINGS.items():
    for lang, txt in entry.items():
        low = str(txt).lower()
        for pat in FORBIDDEN:
            if pat.lower() in low:
                bad_text.append("%s[%s]: %s" % (key, lang, pat))
check(not bad_text, "GUI/CLI 文案无未实现承诺/内部数据 (%r)" % (bad_text[:5] or "none"))
check("home.more_langs" not in i18n.STRINGS,
      "语言选择不承诺尚未实现的语言")

# helptext + help pages (both languages)
bad_help = []
for lang in ("zh_CN", "en"):
    i18n.set_lang(lang, save=False)
    bodies = []
    for key in helptext.HELP.keys():
        try:
            bodies.append((key, helptext.HELP[key]))
        except Exception:
            pass
    for page in helptext.PAGES_ORDER:
        try:
            bodies.append((page, help_pages.body(page)))
        except Exception:
            pass
    for key, body in bodies:
        low = str(body).lower()
        for pat in FORBIDDEN:
            if pat.lower() in low:
                bad_help.append("%s[%s]: %s" % (key, lang, pat))
i18n.set_lang("zh_CN", save=False)
check(not bad_help, "帮助文案无未实现承诺/内部数据 (%r)" % (bad_help[:5] or "none"))

# Internal-research markers must not reappear in the code either
# (strings and comments are checked alike)
INTERNAL = ("本工具实测", "本工具健康对照", "n=24", "外部 15", "课题组",
            "本课题", "v4 手工", "0.77%", "43.9%", "11.2%", "5.8%", "−0.77")
bad_internal = []
for base, _dirs, names in os.walk(os.path.join(ROOT, "alpsbox")):
    for fn in names:
        if not fn.endswith(".py"):
            continue
        rel = os.path.relpath(os.path.join(base, fn), ROOT)
        src = read(rel)
        for pat in INTERNAL:
            if pat in src:
                bad_internal.append("%s: %s" % (rel, pat))
check(not bad_internal, "源码无内部研究数据标记 (%r)"
      % (bad_internal[:5] or "none"))

# =====================================================================
# 3c. Windows launcher
# =====================================================================
# The launcher used to fail for every user because %~dp0 ends with a
# backslash, which Windows argument parsing turns into a literal quote; the
# resolved WSL path was therefore empty. These checks keep the fix in place.
print("\n=== 3c. Windows launcher ===")
bat = read("ALPSbox-GUI.bat")
check('set "HERE=%~dp0"' in bat, "launcher captures its own folder")
check('if "%HERE:~-1%"=="\\" set "HERE=%HERE:~0,-1%"' in bat,
      "launcher strips the trailing backslash before wslpath")
check("ALPSBOX_WSL_DISTRO" in bat, "launcher supports ALPSBOX_WSL_DISTRO")
check("ALPSBOX_DRY_RUN" in bat, "launcher supports dry-run mode")
check('wsl.exe -d "%ALPSBOX_WSL_DISTRO%"' not in bat,
      "launcher does not quote the distro name")
check("wslpath" in bat and "run_gui.sh" in bat,
      "launcher resolves its folder via wslpath and runs run_gui.sh")
gitattr = read(".gitattributes")
check("*.bat" in gitattr and "eol=crlf" in gitattr,
      ".gitattributes keeps the .bat file CRLF")

# =====================================================================
# 4. No group-analysis functionality in the shipped package
# =====================================================================
print("\n=== 4. Release scope ===")
group_patterns = (
    "cmd_group", "group_report", "_page_group", "group.ttest",
    "downstream_group_analysis",
)
bad_group = []
for base, _dirs, names in os.walk(os.path.join(ROOT, "alpsbox")):
    for fn in names:
        if not fn.endswith(".py"):
            continue
        rel = os.path.relpath(os.path.join(base, fn), ROOT)
        text = read(rel)
        for pat in group_patterns:
            if pat in text:
                bad_group.append("%s: %s" % (rel, pat))
check(not bad_group, "no group-analysis code in package (%r)"
      % (bad_group or "none"))

for label in ("README.md", "README.zh-CN.md", "CHANGELOG.md"):
    text = read(label).lower()
    bad = [w for w in ("group comparison test", "group t-test", "组间统计功能",
                       "组分析功能", "组水平统计", "组间比较功能") if w in text]
    check(not bad, "%s: no group-analysis feature claims" % label)

# =====================================================================
# 5. Wording audit: no unsourced "official" claims
# =====================================================================
print("\n=== 5. Wording audit ===")
FILES = ["README.md", "README.zh-CN.md", "CHANGELOG.md", "CITATION.cff",
         "LICENSE_Barisano_alps.txt"]
for base, dirs, names in os.walk(os.path.join(ROOT, "docs")):
    for fn in names:
        if fn.endswith(".md"):
            FILES.append(os.path.relpath(os.path.join(base, fn), ROOT))
for base, _dirs, names in os.walk(os.path.join(ROOT, "alpsbox")):
    for fn in names:
        if fn.endswith(".py"):
            FILES.append(os.path.relpath(os.path.join(base, fn), ROOT))
for base, _dirs, names in os.walk(os.path.join(ROOT, "examples")):
    for fn in names:
        if fn.endswith((".md", ".py")):
            FILES.append(os.path.relpath(os.path.join(base, fn), ROOT))

# Allowed contexts: "there is no official standard implementation", a legacy
# name note, an unrelated "official installer" for a dependency, or an explicit
# disclaimer; each must be self-evident from the surrounding lines.
ALLOW = re.compile(
    r"(没有官方|no official|not an official|does not claim|does not imply|"
    r"no certified|certified|旧称|旧文档|旧名|older documentation|"
    r"no-official-roi|official installer|official FSL|"
    r"官方标准或认证|官方标准/认证|官方标准实现|官方 ALPS」|official/standard|"
    r"不声称|不是)", re.I)
PAT = re.compile(r"官方|official", re.I)
bad = []
for rel in FILES:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        continue
    lines = open(p, encoding="utf-8").read().splitlines()
    for i, ln in enumerate(lines):
        if not PAT.search(ln):
            continue
        window = [lines[j] for j in range(max(0, i - 1),
                                         min(len(lines), i + 2))]
        if any(ALLOW.search(w) for w in window):
            continue
        bad.append("%s:%d: %s" % (rel, i + 1, ln.strip()[:110]))
check(not bad, "no unsourced official claims: %d" % len(bad))
for b in bad[:15]:
    print("      !", b)

# user-visible labels must not say "official ROI"
bad_label = []
for key, entry in i18n.STRINGS.items():
    for lang, text in entry.items():
        if re.search(r"官方\s*ROI|official\s+ROI", str(text), re.I):
            bad_label.append("%s[%s]" % (key, lang))
check(not bad_label, "no official-ROI label (%r)" % (bad_label or "none"))

# =====================================================================
# 6. Markdown relative links resolve
# =====================================================================
print("\n=== 6. Documentation links ===")
md_files = ["README.md", "README.zh-CN.md", "CHANGELOG.md", "docs/README.md",
            "docs/INSTALL.md", "docs/FAQ.md", "docs/CITATIONS.md",
            "docs/VALIDATION.md", "docs/WHY_ALPSBOX.md"]
md_files += [os.path.relpath(os.path.join(base, fn), ROOT)
             for base, _dirs, names in os.walk(os.path.join(ROOT, "docs"))
             for fn in names if fn.endswith(".md")]
LINK = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")
broken = []
for rel in sorted(set(md_files)):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        continue
    for target in LINK.findall(open(p, encoding="utf-8").read()):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(p), target))
        if not os.path.exists(resolved):
            broken.append("%s -> %s" % (rel, target))
check(not broken, "relative documentation links resolve (%d broken)"
      % len(broken))
for b in broken[:15]:
    print("      !", b)

print("\nRESULT:", "PASS" if not failures else "FAIL")
for f in failures:
    print("  !", f)
sys.exit(0 if not failures else 1)
