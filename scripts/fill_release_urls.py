# -*- coding: utf-8 -*-
"""Fill the public repository URL and the Zenodo DOI into the release files.

Usage
-----
    python scripts/fill_release_urls.py --repo-url https://github.com/<owner>/alpsbox
    python scripts/fill_release_urls.py --doi 10.5281/zenodo.1234567
    python scripts/fill_release_urls.py --repo-url ... --doi ...

Run from the repository root. The script is idempotent: missing placeholders are
reported, an unchanged URL is skipped, and an already applied DOI is skipped.
`--repo-url` also works after the URL has been filled (for example if the
repository is renamed or transferred): it replaces the current URL found in
`pyproject.toml`/`CITATION.cff`.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

PLACEHOLDER = "https://github.com/your-org/alpsbox"
CURRENT_URL_RE = re.compile(
    r"https://github\.com/[^/\s\"']+/alpsbox")
URL_FILES = [
    "README.md",
    "README.zh-CN.md",
    "docs/INSTALL.md",
    "docs/zh-CN/INSTALL.md",
    "CITATION.cff",
    "pyproject.toml",
]


def read(rel: str) -> str:
    with open(rel, encoding="utf-8") as fh:
        return fh.read()


def write(rel: str, text: str) -> None:
    with open(rel, "w", encoding="utf-8") as fh:
        fh.write(text)


def current_repo_url() -> str:
    """Return the repository URL currently recorded in the release files."""
    for rel in ("pyproject.toml", "CITATION.cff"):
        if not os.path.isfile(rel):
            continue
        for match in CURRENT_URL_RE.finditer(read(rel)):
            return match.group(0)
    return ""


def fill_repo_url(repo_url: str) -> int:
    if not re.fullmatch(r"https://github\.com/[^/\s]+/alpsbox/?", repo_url):
        print("error: --repo-url must look like "
              "https://github.com/<owner>/alpsbox", file=sys.stderr)
        return 2
    repo_url = repo_url.rstrip("/")
    old_urls = [PLACEHOLDER]
    current = current_repo_url()
    if current and current != repo_url:
        old_urls.append(current)
    elif current == repo_url:
        print("nothing to do: repository URL is already %s" % repo_url)
        return 0
    changed = 0
    for rel in URL_FILES:
        if not os.path.isfile(rel):
            print("warning: missing file", rel)
            continue
        text = read(rel)
        n = 0
        for old in old_urls:
            n += text.count(old)
            text = text.replace(old, repo_url)
        if n:
            write(rel, text)
            changed += 1
            print("updated %-28s (%d occurrence(s))" % (rel, n))
    if not changed:
        print("nothing to do: no repository URL found to replace")
    return 0


def add_badge(text: str, doi: str) -> str:
    badge = ("[![DOI](https://zenodo.org/badge/DOI/%s.svg)]"
             "(https://doi.org/%s)" % (doi, doi))
    if badge in text:
        return text
    anchor = ("[**English**](README.md) | [**简体中文**](README.zh-CN.md)")
    if anchor in text:
        return text.replace(anchor, anchor + "\n\n" + badge, 1)
    return text


def fill_doi(doi: str) -> int:
    if not re.fullmatch(r"10\.5281/zenodo\.\d+", doi):
        print("error: --doi must look like 10.5281/zenodo.<number>",
              file=sys.stderr)
        return 2

    # README (both languages): badge + line in the citation section
    for rel in ("README.md", "README.zh-CN.md"):
        if not os.path.isfile(rel):
            continue
        text = read(rel)
        if doi in text:
            print("skip %-28s (DOI already present)" % rel)
            continue
        text = add_badge(text, doi)
        link = "https://doi.org/%s" % doi
        if rel == "README.md":
            needle = "Machine-readable metadata is in [CITATION.cff](CITATION.cff)"
            extra = ("Archived release (Zenodo): [%s](%s).\n\n" % (doi, link))
        else:
            needle = "机器可读元数据见 [CITATION.cff](CITATION.cff)"
            extra = ("归档版本（Zenodo DOI）：[%s](%s)。\n\n" % (doi, link))
        if needle in text:
            text = text.replace(needle, extra + needle, 1)
        write(rel, text)
        print("updated", rel)

    # CITATION.cff: identifiers block
    if os.path.isfile("CITATION.cff"):
        text = read("CITATION.cff")
        if doi in text:
            print("skip CITATION.cff (DOI already present)")
        else:
            block = ('identifiers:\n'
                     '  - type: doi\n'
                     '    value: "%s"\n' % doi)
            m = re.search(r"^date-released:.*\n", text, flags=re.M)
            if m:
                text = text[:m.end()] + block + text[m.end():]
                write("CITATION.cff", text)
                print("updated CITATION.cff")
            else:
                print("warning: date-released line not found in CITATION.cff")

    # docs/CITATIONS (both languages)
    for rel, anchor in (
            ("docs/CITATIONS.md",
             "A machine-readable `CITATION.cff` is provided"),
            ("docs/zh-CN/CITATIONS.md",
             "仓库内提供了机器可读的 `CITATION.cff`")):
        if not os.path.isfile(rel):
            continue
        text = read(rel)
        if doi in text:
            print("skip", rel)
            continue
        if anchor in text:
            extra = ("Archived release: ALPSbox v1.0.0. *Zenodo*. "
                     "doi:%s (https://doi.org/%s)\n\n" % (doi, doi)
                     if rel.endswith("CITATIONS.md") and "zh-CN" not in rel
                     else "归档版本：ALPSbox v1.0.0。*Zenodo*。"
                          "doi:%s（https://doi.org/%s）\n\n" % (doi, doi))
            text = text.replace(anchor, extra + anchor, 1)
            write(rel, text)
            print("updated", rel)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-url", help="public GitHub repository URL")
    ap.add_argument("--doi", help="Zenodo DOI, e.g. 10.5281/zenodo.1234567")
    args = ap.parse_args(argv)
    if not args.repo_url and not args.doi:
        ap.print_help()
        return 2
    if not os.path.isfile("README.md") or not os.path.isdir("alpsbox"):
        print("error: run this script from the repository root", file=sys.stderr)
        return 2
    rc = 0
    if args.repo_url:
        rc = fill_repo_url(args.repo_url) or rc
    if args.doi:
        rc = fill_doi(args.doi) or rc
    print("done")
    return rc


if __name__ == "__main__":
    sys.exit(main())
