#!/usr/bin/env python3
"""T16 — income-series canonical + noindex consolidation (idempotent).

Scans blog markdown posts whose filename ends with `26-06-.md` (the
income-series batch). Picks ONE hub post (HUB_SLUG) that stays indexable with
self-canonical; every other variant in the batch gets `canonical` pointing at
the hub and `noindex: true` to stop SEO self-cannibalization.

Run with --dry-run first.
"""
import sys, re, os, glob

BLOG_DIR = "/Users/twinssn/Projects/money-aikorea24/src/content/blog"
HUB_SLUG = "서울-35세-직장인-내-월급은-평균-수준일까-소득-통계-총정리-26-06-"
HUB_CANONICAL = f"/blog/{HUB_SLUG}/"
DRY = "--dry-run" in sys.argv


def is_income(name: str) -> bool:
    return name.endswith("26-06-.md")


def split_fm(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def has_field(fm: str, key: str) -> bool:
    return re.search(rf"^{key}\s*:", fm, re.MULTILINE) is not None


def set_field(fm: str, key: str, value: str) -> str:
    fm = re.sub(rf"^{key}\s*:.*\n", "", fm, flags=re.MULTILINE)
    return fm.rstrip("\n") + f"\n{key}: {value}"


def remove_field(fm: str, key: str) -> str:
    return re.sub(rf"^{key}\s*:.*\n", "", fm, flags=re.MULTILINE).rstrip("\n")


files = sorted(glob.glob(os.path.join(BLOG_DIR, "*.md")))
changed = 0
for f in files:
    name = os.path.basename(f)
    if not is_income(name):
        continue
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    fm, body = split_fm(text)
    if fm is None:
        print(f"SKIP (no frontmatter): {name}")
        continue
    slug = name[:-3]
    if slug == HUB_SLUG:
        # Hub: indexable, self-canonical (default). Strip any override flags.
        new_fm = remove_field(fm, "noindex")
        new_fm = remove_field(new_fm, "canonical")
    else:
        new_fm = set_field(fm, "canonical", HUB_CANONICAL)
        new_fm = set_field(new_fm, "noindex", "true")
    if new_fm != fm:
        changed += 1
        if DRY:
            print(f"DRY: {name}")
        else:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write("---\n" + new_fm + "\n---\n" + body)
            print(f"WRITE: {name}")

print(
    f"\n{changed} file(s) would be changed"
    if DRY
    else f"\n{changed} file(s) changed"
)
