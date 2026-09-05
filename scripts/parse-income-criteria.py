#!/usr/bin/env python3
"""
benefits-clean.json의 target/content 텍스트에서 소득 기준을 파싱하여
income_criteria 필드를 추가한다.

파싱 가능한 패턴:
  - 중위소득 N% 이하/미만 → { "type": "median_pct_max", "value": N }
  - 중위소득 N% 이상/초과 → { "type": "median_pct_min", "value": N }
  - 월 소득 N만원 이상    → { "type": "monthly_min", "value": N }
  - 연소득 N만원 이상      → { "type": "annual_min", "value": N }
  - 연소득 N천만원 이상    → { "type": "annual_min", "value": N*1000 }
  - 연소득 N억원 이상      → { "type": "annual_min", "value": N*10000 }
"""

import json
import re
import sys
from pathlib import Path

INPUT = Path(__file__).resolve().parent.parent / "public" / "benefits-clean.json"
OUTPUT = INPUT  # overwrite in-place

# ── 파싱 규칙 ──────────────────────────────────────────────

# 중위소득 N% 이하/미만
RE_MEDIAN_MAX = re.compile(r"중위소득\s*(\d{1,3})%\s*(이하|미만)")
# 중위소득 N% 이상/초과
RE_MEDIAN_MIN = re.compile(r"중위소득\s*(\d{1,3})%\s*(이상|초과)")
# 월 소득 N만원 이상/이하
RE_MONTHLY = re.compile(r"월\s*소득\s*(\d[\d,]*)\s*만원")
# 연소득 N만원/천만원/억원
RE_ANNUAL = re.compile(r"연\s*소득\s*(\d[\d,]*)\s*(만원|천만원|억원)")


def parse_income(text: str) -> list[dict]:
    """텍스트에서 소득 기준을 파싱하여 list[dict] 반환."""
    criteria = []
    seen = set()

    for m in RE_MEDIAN_MAX.finditer(text):
        pct = int(m.group(1))
        if 10 <= pct <= 500 and pct not in seen:
            criteria.append({"type": "median_pct_max", "value": pct})
            seen.add(pct)

    for m in RE_MEDIAN_MIN.finditer(text):
        pct = int(m.group(1))
        if 10 <= pct <= 500 and pct not in seen:
            criteria.append({"type": "median_pct_min", "value": pct})
            seen.add(pct)

    for m in RE_MONTHLY.finditer(text):
        amt = int(m.group(1).replace(",", ""))
        if amt > 0:
            criteria.append({"type": "monthly_min", "value": amt})

    for m in RE_ANNUAL.finditer(text):
        amt = int(m.group(1).replace(",", ""))
        unit = m.group(2)
        if unit == "천만원":
            amt *= 1000
        elif unit == "억원":
            amt *= 10000
        if amt > 0:
            criteria.append({"type": "annual_min", "value": amt})

    return criteria


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    parsed = 0
    total_criteria = 0

    for b in data:
        target = b.get("target", "") or ""
        content = b.get("content", "") or ""
        combined = target + " " + content

        criteria = parse_income(combined)
        if criteria:
            b["income_criteria"] = criteria
            parsed += 1
            total_criteria += len(criteria)
        else:
            b["income_criteria"] = []

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Done: {len(data)} benefits processed")
    print(f"  with income_criteria: {parsed}")
    print(f"  total criteria entries: {total_criteria}")


if __name__ == "__main__":
    main()
