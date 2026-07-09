#!/usr/bin/env python3
"""Wave 4, T14 — 기존 100+ 블로그 포스트의 CTA 복사문을 variant 기반으로 백필.

기존 포스트는 구 pipeline이 하드코딩한 CTA 복사문을 그대로 들고 있음.
이 스크립트는 각 포스트의 CTA 블록쿼트 헤드라인만 새 variant 복사(mid/end)로
교체한다. src 토큰(/my-persona?src=inline-peer-{cat}-{persona} 등)은 그대로 보존하므로
T5 귀속 파싱과 광고 배치는 영향을 받지 않는다.

- cat/persona 는 CTA 링크의 src 토큰에서 추출 (frontmatter에 persona 키가 없음)
- A/B 인덱스 = filename 기준 결정적 해시 (재빌드 일관성, 재실행 no-op)
- 멱등: 한 번 바꾼 뒤 재실행하면 0건 변경
- 금지: 헤딩/표/needs_review 플래그 변경 없음 (CTA 헤드라인 줄만 교체)
"""
import os, re, sys, hashlib, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")
CONFIG_PATH = os.path.join(ROOT, "scripts", "auto-writer", "config", "category_map.yaml")

try:
    import yaml
except ImportError:
    print("PyYAML 필요: pip install pyyaml", file=sys.stderr); sys.exit(1)

with open(CONFIG_PATH, encoding="utf-8") as f:
    CTA_VARIANTS = yaml.safe_load(f).get("cta_variants", {})

DEFAULT_MID = ["내 또래 평균이 궁금하다면 확인해보세요", "비슷한 조건 사람들은 어떻게 살까요?"]
DEFAULT_END = ["지금 내 페르소나 분석하기 →", "내 상황 맞춤 통계 보러가기 →"]


def _ab_index(filename: str) -> int:
    return int(hashlib.md5(filename.encode("utf-8")).hexdigest(), 16) % 2


def _variants(cat: str, persona: str):
    v = CTA_VARIANTS.get(f"{cat}-{persona}", CTA_VARIANTS.get("default", {}))
    mid = v.get("mid", DEFAULT_MID)
    end = v.get("end", DEFAULT_END)
    return mid, end


def _rewrite(content: str, filename: str):
    """CTA 블록쿼트 헤드라인을 variant 복사로 교체. 변경된 경우만 새 문자열 반환."""
    idx = _ab_index(filename)
    changed = False

    # 인라인 CTA (peer / stats) — 둘 다 mid(약함) 복사 사용
    def _inline_repl(m):
        nonlocal changed
        pre, headline, sub, link = m.group(1), m.group(2), m.group(3), m.group(4)
        kind, cat, persona = m.group(5), m.group(6), m.group(7)
        mid, _ = _variants(cat, persona)
        new_head = mid[idx % len(mid)]
        if new_head != headline:
            changed = True
        return f"{pre}**{new_head}**\n> {sub}\n>\n> {link}"

    inline_pat = re.compile(
        r"(> )\*\*(.+?)\*\*\n> (.+?)\n>\n> (\[[^\]]+\]\(/my-persona\?src=inline-(peer|stats)-([a-z]+)-([a-z]+)\))"
    )
    content = inline_pat.sub(_inline_repl, content)

    # END CTA (persona.aikorea24.kr/my-persona?src=cta-{persona}) — end(강함) 복사 사용
    def _end_repl(m):
        nonlocal changed
        pre, headline, sub, link = m.group(1), m.group(2), m.group(3), m.group(4)
        persona = m.group(5)
        _, end = _variants("general", persona)
        new_head = end[idx % len(end)]
        if new_head != headline:
            changed = True
        return f"{pre}**{new_head}**\n> {sub}\n>\n> {link}"

    end_pat = re.compile(
        r"(> )\*\*(.+?)\*\*\n> (.+?)\n>\n> (\[[^\]]+\]\(https://persona\.aikorea24\.kr/my-persona\?src=cta-([a-z]+)\))"
    )
    content = end_pat.sub(_end_repl, content)

    return content, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="변경 대상만 출력, 실제 쓰기 안 함")
    args = ap.parse_args()

    files = sorted(
        os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR)
        if f.endswith(".md")
    )
    to_change = 0
    errors = 0
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            new_content, changed = _rewrite(content, os.path.basename(path))
            if changed:
                to_change += 1
                if not args.dry_run:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(new_content)
                    print(f"[APPLY] {os.path.basename(path)}")
                else:
                    print(f"[DRY]   {os.path.basename(path)}")
        except Exception as e:
            errors += 1
            print(f"[ERROR] {os.path.basename(path)}: {e}", file=sys.stderr)

    print(f"\n총 {len(files)}개 파일 | 변경 {to_change}건 | 오류 {errors}건"
          + (" (dry-run)" if args.dry_run else " (적용 완료)"))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
