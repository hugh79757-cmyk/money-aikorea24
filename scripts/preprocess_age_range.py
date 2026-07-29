#!/usr/bin/env python3
"""
benefits-clean.json → age_range 전처리 파이프라인

안전한 규칙만으로 target 텍스트에서 age_range 추출:
  C1: "N~M세" 완전범위 → [N, M]
  C2: "65세 이상" (category=senior 한정) → [N, 100]
  함정: 자녀/아동 연령은 절대 파싱 금지

원칙: 정확도 > 커버리지. 애매하면 비워둔다.
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

# ── 경로 ──
DATA_DIR = Path(__file__).resolve().parent.parent / "public"
DATA_PATH = DATA_DIR / "benefits-clean.json"
BACKUP_PATH = DATA_DIR / "benefits-clean.backup.json"


# ── 정규식 ──
# 함정 탐지 (파싱보다 먼저 실행)
# 연령이 자녀/아동을 수식하는 패턴
RE_TRAP_CHILD = re.compile(
    r'(?:만\s*)?\d+\s*세\s*(?:미만|이하)?\s*(?:의\s*)?(?:자녀|아동|어린이|아이|손자|자녀분)'
)
RE_TRAP_PAREN = re.compile(
    r'(?:자녀|아동|어린이|손자|아이)\s*[\(（]\s*(?:만\s*)?\d+\s*세'
)

# C1: 완전범위 "N~M세" (하이픈, 물결, 전각 대시 등)
RE_C1 = re.compile(
    r'(?:만\s*)?(\d+)\s*[~\-∼–—]\s*(\d+)\s*세'
)

# C2: 노인 하한 "65세 이상" 등 (category=senior 한정)
RE_C2_SENIOR = re.compile(
    r'(6[5-9]|[7-9]\d|100)\s*세\s*(?:이상|초과)'
)


def is_trap(target: str) -> bool:
    """연령이 자녀/아동을 수식하는 함정 표현인가?"""
    if not target:
        return False
    if RE_TRAP_CHILD.search(target):
        return True
    if RE_TRAP_PAREN.search(target):
        return True
    return False


def extract_c1(target: str):
    """C1 완전범위 추출. 성공 시 (min, max), 실패 시 None."""
    if not target:
        return None
    m = RE_C1.search(target)
    if not m:
        return None
    lo, hi = int(m.group(1)), int(m.group(2))
    # 유효성 검증
    if lo < 0 or hi > 120 or lo > hi:
        return None
    return (lo, hi)


def extract_c2_senior(target: str):
    """C2 senior 하한만 추출. 성공 시 (min, 100), 실패 시 None."""
    if not target:
        return None
    m = RE_C2_SENIOR.search(target)
    if not m:
        return None
    lo = int(m.group(1))
    if lo < 65 or lo > 120:
        return None
    return (lo, 100)


def process_benefits(benefits: list) -> dict:
    """전체 처리. 결과 통계 dict 반환."""
    stats = {
        'original': 0,
        'parsed_c1': 0,
        'parsed_senior': 0,
        'trap_skipped': 0,
        'empty': 0,
        'c1_samples': [],
        'senior_samples': [],
        'trap_samples': [],
    }

    for b in benefits:
        age_range = b.get('age_range')
        target = b.get('target') or ''
        category = b.get('category') or ''

        # ── a) 이미 age_range 있음 → 건드리지 않음 ──
        if age_range and len(age_range) == 2 and age_range[0] is not None:
            b['age_source'] = 'original'
            stats['original'] += 1
            continue

        # ── b) 함정 검사 (파싱보다 먼저!) ──
        if is_trap(target):
            b['age_range'] = []
            b['age_source'] = ''
            stats['trap_skipped'] += 1
            if len(stats['trap_samples']) < 10:
                stats['trap_samples'].append({
                    'name': b.get('name', '?')[:40],
                    'target': target[:200],
                    'reason': '자녀/아동 연령 감지'
                })
            continue

        # ── c) C1 완전범위 ──
        c1 = extract_c1(target)
        if c1 is not None:
            b['age_range'] = list(c1)
            b['age_source'] = 'parsed_c1'
            stats['parsed_c1'] += 1
            if len(stats['c1_samples']) < 20:
                stats['c1_samples'].append({
                    'name': b.get('name', '?')[:40],
                    'target': target[:150],
                    'extracted': list(c1)
                })
            continue

        # ── d) C2 senior (category=senior 한정) ──
        if category == 'senior':
            c2 = extract_c2_senior(target)
            if c2 is not None:
                b['age_range'] = list(c2)
                b['age_source'] = 'parsed_senior'
                stats['parsed_senior'] += 1
                if len(stats['senior_samples']) < 20:
                    stats['senior_samples'].append({
                        'name': b.get('name', '?')[:40],
                        'target': target[:150],
                        'extracted': list(c2)
                    })
                continue

        # ── e) 파싱 실패 → 비워둠 ──
        b['age_range'] = []
        b['age_source'] = ''
        stats['empty'] += 1

    return stats


def print_report(stats: dict, total: int):
    """검증 리포트 출력"""
    pct = lambda n: f"{n/total*100:.1f}%"

    print("=" * 60)
    print("  age_range 전처리 검증 리포트")
    print("=" * 60)
    print(f"\n  전체 레코드: {total}건")
    print(f"  ─────────────────────────────────────")
    print(f"  original (기존 유지):    {stats['original']:>5}건  ({pct(stats['original'])})")
    print(f"  parsed_c1 (완전범위):    {stats['parsed_c1']:>5}건  ({pct(stats['parsed_c1'])})")
    print(f"  parsed_senior (65세+):   {stats['parsed_senior']:>5}건  ({pct(stats['parsed_senior'])})")
    print(f"  trap_skipped (함정제외): {stats['trap_skipped']:>5}건  ({pct(stats['trap_skipped'])})")
    print(f"  empty (파싱안됨):        {stats['empty']:>5}건  ({pct(stats['empty'])})")

    filled = stats['original'] + stats['parsed_c1'] + stats['parsed_senior']
    print(f"\n  ▶ age_range 채워짐: {filled}/{total} ({pct(filled)})")
    before_original = stats['original']  # 539 기준
    after = filled
    print(f"  ▶ coverage: {before_original}/{total} ({pct(before_original)}) → {after}/{total} ({pct(after)})")
    print(f"  ▶ 증가: +{after - before_original}건 ({pct(after)})")

    # ── C1 샘플 ──
    print(f"\n{'─' * 60}")
    print(f"  [parsed_c1] 샘플 {len(stats['c1_samples'])}건 (육안 검수용)")
    print(f"{'─' * 60}")
    for s in stats['c1_samples']:
        print(f"  [{s['name']}]")
        print(f"    target: {s['target']}")
        print(f"    → age_range: {s['extracted']}")
        print()

    # ── Senior 샘플 ──
    if stats['senior_samples']:
        print(f"{'─' * 60}")
        print(f"  [parsed_senior] 샘플 {len(stats['senior_samples'])}건 (육안 검수용)")
        print(f"{'─' * 60}")
        for s in stats['senior_samples']:
            print(f"  [{s['name']}] (category=senior)")
            print(f"    target: {s['target']}")
            print(f"    → age_range: {s['extracted']}")
            print()

    # ── 함정 샘플 ──
    if stats['trap_samples']:
        print(f"{'─' * 60}")
        print(f"  [함정 제외] 샘플 {len(stats['trap_samples'])}건")
        print(f"{'─' * 60}")
        for s in stats['trap_samples']:
            print(f"  ❌ [{s['name']}]")
            print(f"     target: {s['target']}")
            print(f"     이유: {s['reason']}")
            print()

    # ── 추가 검증: 비정상 range 탐지 ──
    print(f"{'─' * 60}")
    print("  [추가 검증] 비정상 range 스캔")
    anomalies = []
    for b in benefits:
        ar = b.get('age_range', [])
        if len(ar) == 2:
            if ar[0] > ar[1] or ar[0] < 0 or ar[1] > 120:
                anomalies.append((b.get('name', '?'), ar))
    if anomalies:
        print(f"  ⚠️  비정상 range 발견: {len(anomalies)}건")
        for name, ar in anomalies:
            print(f"      {name}: {ar}")
    else:
        print(f"  ✅ 비정상 range 없음 (모든 range 유효)")
    print()


if __name__ == '__main__':
    # ── 로드 ──
    print(f"로드: {DATA_PATH}")
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        benefits = json.load(f)

    total = len(benefits)
    print(f"전체 레코드: {total}건")

    # ── 처리 ──
    stats = process_benefits(benefits)

    # ── 저장 ──
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(benefits, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {DATA_PATH}")

    # ── 리포트 ──
    print_report(stats, total)

    # 종료 코드 (성공)
    sys.exit(0)
