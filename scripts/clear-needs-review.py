#!/usr/bin/env python3
"""Wave 5, T15 — needs_review 백로그 정리 (멱등, 정책: REVIEW-POLICY.md).

draft:false 이면서 needs_review:true 인 글의 플래그를 false 로 해제.
draft:true 는 유지, needs_review 필드가 없는 글(수동 발행물)은 건드리지 않음.
포스트 삭제/본문 변경 없음. 재실행 시 변경 0건(멱등).
"""
import os, re, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_DIR = os.path.join(ROOT, "src", "content", "blog")


def _clear(content: str):
    """frontmatter 내 needs_review: true (draft:false) 를 false 로. 변경 시만 반환."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return content, False
    fm = m.group(1)
    # draft 확인
    draft_m = re.search(r"^draft:\s*(\S+)", fm, re.MULTILINE)
    draft_val = draft_m.group(1).strip() if draft_m else "false"
    if draft_val.lower() == "true":
        return content, False  # 미발행 → 유지
    if not re.search(r"^needs_review:\s*true", fm, re.MULTILINE):
        return content, False  # 필드 없음 → 유지
    new_fm = re.sub(r"^needs_review:\s*true", "needs_review: false", fm, flags=re.MULTILINE)
    if new_fm == fm:
        return content, False
    return content[:m.start(1)] + new_fm + content[m.end(1):], True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md"))
    cleared = retained = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        new_content, changed = _clear(content)
        if changed:
            cleared += 1
            if not args.dry_run:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                print(f"[APPLY] {os.path.basename(path)}")
            else:
                print(f"[DRY]   {os.path.basename(path)}")
        else:
            retained += 1
    print(f"\n총 {len(files)}개 | 해제 {cleared}건 | 유지 {retained}건"
          + (" (dry-run)" if args.dry_run else " (적용 완료)"))


if __name__ == "__main__":
    main()
