#!/usr/bin/env python3
"""Pre-build/blog quality checker — validates ALL blog posts for known issues.

Usage:
    python3 scripts/check-blog-issues.py          # check all
    python3 scripts/check-blog-issues.py --fix     # check + auto-fix known issues
    python3 scripts/check-blog-issues.py --ci      # exit 1 if any issues found (for CI)

Checks:
    - AI artifacts: <|channel|system|assistant|...>
    - Raw **목차** TOC (redundant — BlogPost layout has built-in TOC)
    - Double H1 (# heading in body after frontmatter)
    - Leading whitespace on first content line
    - Multiple consecutive --- dividers
    - kakaokey/define:vars references
"""

import os, re, sys

BLOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'content', 'blog')

_AI_ARTIFACT_RE = re.compile(r'<\|[^>]*>')
_TOC_RE = re.compile(r'\*\*목차\*\*')
_DOUBLE_H1_RE = re.compile(r'^#\s', re.MULTILINE)
_LEADING_SPACE_RE = re.compile(r'^[ \t]+\S')
_MULTI_HR_RE = re.compile(r'\n-{3,}\n-{3,}\n')
_DEFINE_VARS_RE = re.compile(r'define:vars')
_KAKAO_KEY_RE = re.compile(r'kakaoJsKey')
_TEMPLATE_RE = re.compile(r'\{\{.*?\}\}')

IssueType = str  # one of the check names


def scan_file(fpath: str) -> list[tuple[IssueType, str]]:
    issues = []
    with open(fpath, 'r', encoding='utf-8') as f:
        raw = f.read()

    lines = raw.split('\n')

    # Parse frontmatter
    fm_end = None
    for i, l in enumerate(lines):
        if l.strip() == '---' and i > 0:
            fm_end = i
            break

    if fm_end is None:
        return [("NO_FRONTMATTER", "no frontmatter found")]

    body = '\n'.join(lines[fm_end + 1:])
    body_lines = lines[fm_end + 1:]

    # 1. AI artifacts
    if _AI_ARTIFACT_RE.search(body):
        matches = _AI_ARTIFACT_RE.findall(body)
        issues.append(("AI_ARTIFACT", "; ".join(m[:40] for m in matches)))

    # 2. Raw TOC
    if _TOC_RE.search(body):
        issues.append(("RAW_TOC", "**목차** found in body"))

    # 3. Double H1 (first heading in body starts with #)
    for line in body_lines:
        s = line.strip()
        if s.startswith('# ') and not s.startswith('## ') and not s.startswith('### '):
            issues.append(("DOUBLE_H1", f'body starts with H1: "{s[:50]}"'))
            break
        if s and not s.startswith('#'):
            break

    # 4. Leading whitespace on first non-empty content line
    for line in body_lines:
        s = line.strip()
        if s and not s.startswith('#') and not s.startswith('>') and not s.startswith('-') and not s.startswith('*'):
            if line != s:
                issues.append(("LEADING_SPACE", f'"{s[:50]}"'))
            break

    # 5. Multiple consecutive ---
    if _MULTI_HR_RE.search(body):
        issues.append(("MULTI_HR", "consecutive --- dividers"))

    # 6. Template references
    if _DEFINE_VARS_RE.search(body):
        issues.append(("DEFINE_VARS", "define:vars in body"))
    if _KAKAO_KEY_RE.search(body):
        issues.append(("KAKAO_KEY", "kakaoJsKey in body"))
    if _TEMPLATE_RE.search(body):
        issues.append(("TEMPLATE_SYNTAX", "{{ }} template syntax in body"))

    return issues


def fix_issues(fpath: str) -> list[tuple[IssueType, str]]:
    """Auto-fix known issues in a file. Returns issues that could NOT be auto-fixed."""
    with open(fpath, 'r', encoding='utf-8') as f:
        raw = f.read()

    original = raw
    lines = raw.split('\n')

    # Parse frontmatter
    fm_end = None
    for i, l in enumerate(lines):
        if l.strip() == '---' and i > 0:
            fm_end = i
            break

    if fm_end is None:
        return [("NO_FRONTMATTER", "cannot fix — no frontmatter")]

    body_lines = lines[fm_end + 1:]

    # --- Fix 1: Remove **목차** section ---
    new_body = []
    i = 0
    skip_toc = False
    while i < len(body_lines):
        line = body_lines[i]
        stripped = line.strip()

        if stripped == '**목차**' and not skip_toc:
            skip_toc = True
            i += 1
            continue

        if skip_toc:
            if stripped.startswith('---'):
                skip_toc = False
                i += 1
                continue
            if stripped.startswith('##'):
                skip_toc = False
                new_body.append(line)
                i += 1
                continue
            i += 1
            continue

        new_body.append(line)
        i += 1

    body_text = '\n'.join(new_body)

    # --- Fix 2: Remove <|...> artifacts ---
    body_text = _AI_ARTIFACT_RE.sub('', body_text)

    # --- Fix 3: Fix double H1 ---
    body_parts = body_text.split('\n')
    for j, line in enumerate(body_parts):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## ') and not stripped.startswith('### '):
            body_parts[j] = line.replace('# ', '## ', 1)
            break
        if stripped and not stripped.startswith('#'):
            break

    body_text = '\n'.join(body_parts)

    # --- Fix 4: Fix leading whitespace ---
    body_parts = body_text.split('\n')
    for j, line in enumerate(body_parts):
        stripped = line.strip()
        if stripped and line != stripped:
            body_parts[j] = line.lstrip()
            break
        if stripped:
            break  # already clean
    body_text = '\n'.join(body_parts)

    # Reconstruct
    header = '\n'.join(lines[:fm_end + 1])
    new_raw = header + '\n' + body_text

    if new_raw != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_raw)
        return []
    else:
        # Check what's left
        remaining = []
        for issue, detail in scan_file(fpath):
            if issue not in ("RAW_TOC", "AI_ARTIFACT", "DOUBLE_H1", "LEADING_SPACE"):
                remaining.append((issue, detail))
        return remaining


def main():
    fix_mode = '--fix' in sys.argv
    ci_mode = '--ci' in sys.argv

    all_issues: dict[str, list[tuple[IssueType, str]]] = {}
    total_issues = 0
    error_count = 0

    for fname in sorted(os.listdir(BLOG_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(BLOG_DIR, fname)

        if fix_mode:
            remaining = fix_issues(fpath)
            if remaining:
                all_issues[fname] = remaining
                total_issues += len(remaining)
                error_count += 1
        else:
            issues = scan_file(fpath)
            if issues:
                all_issues[fname] = issues
                total_issues += len(issues)

    # Report
    if all_issues:
        print(f"\n{'='*60}")
        if fix_mode:
            print(f"FIX MODE: {error_count} files have unfixable issues remaining")
        else:
            print(f"SCAN MODE: {len(all_issues)} files with {total_issues} issues")
        print(f"{'='*60}")

        from collections import Counter
        type_counts: Counter[str] = Counter()
        for fname, issues in sorted(all_issues.items()):
            print(f"\n  📄 {fname}")
            for issue, detail in issues:
                print(f"     ❌ [{issue}] {detail}")
                type_counts[issue] += 1

        print(f"\n{'='*60}")
        print("Summary by issue type:")
        for t, c in type_counts.most_common():
            print(f"  {t}: {c}")
        print(f"{'='*60}")

        if ci_mode:
            sys.exit(1)
    else:
        print(f"\n✅ All {len([f for f in os.listdir(BLOG_DIR) if f.endswith('.md')])} blog posts clean — no issues found.")
        sys.exit(0)


if __name__ == '__main__':
    main()
