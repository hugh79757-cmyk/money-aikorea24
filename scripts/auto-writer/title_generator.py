"""
타이틀 생성기 (Title Generator)
────────────────────────────────
자동 발행 블로그의 '마무리 어미'를 카테고리별로 다양화하여
'총정리' 반복 패턴을 제거한다.

사용법:
  from title_generator import refinish_title, generate_title

  # 기존 제목의 마무리 어미만 다양화 (발행글 일괄 정비용)
  new_title = refinish_title(old_title)

  # 구조형 신규 생성 (미래 파이프라인용)
  title = generate_title(target="무주택 직장인", benefit="전세자금 이자지원",
                         number="1,500만 원", question="", category="loan")
"""
import random
from collections import deque
from typing import Optional


# ── 카테고리별 마무리 어미 사전 ──────────────────────────────
# "총정리"는 별도 캡 규칙(pick_ending_capped)으로만 허용된다.
ENDINGS: dict[str, list[str]] = {
    "정리형": ["완벽 가이드", "한눈에 정리", "핵심 요약", "총집합", "A to Z",
              "클리어하게 정리", "요점만 쏙쏙", "깔끔하게 정리", "끝판왕 가이드"],
    "행동형": ["받는 법", "신청 방법", "챙기는 법", "놓치지 마세요", "꼭 챙기세요",
              "서둘러 신청하세요", "미리 알아두세요", "미리 챙기는 법"],
    "질문형": ["알고 계셨나요?", "진짜일까?", "제대로 챙기려면?", "얼마나 받을까?",
              "누가 받을 수 있을까?", "놓친 적 있으신가요?"],
    "숫자형": ["5분 만에 정리", "딱 3가지만 기억하세요", "3단계로 끝내기",
              "한 번에 정리", "100% 활용법"],
    "긴급형": ["서둘러야 하는 이유", "마지막 기회", "지금 아니면 놓칩니다",
              "올해 안에 꼭", "신청 기한 다가오는데"],
    "비교형": ["비교해 봤습니다", "정리해 드립니다", "확인해 보세요",
              "한 번에 비교", "조건 비교 정리", "실제 혜택 비교"],
    "결과형": ["받을 수 있습니다", "혜택 보는 법", "지원받는 방법",
              "돌려받는 법", "아낄 수 있는 법", "덜어주는 법"],
    "밀착형": ["놓치면 손해", "꼭 알아두세요", "미리 챙겨두면 좋은",
              "손해 보지 않으려면", "놓치면 아까운"],
    "후기형": ["신청 후기", "받아본 후기", "실제 사례", "적용 후기",
              "체험해 본 결과", "신청해 보니"],
    "시의성형": ["2025년 버전", "올해 바뀐 점", "새로운 기준", "변경된 조건",
                "최신 기준 정리", "이번 달 바뀐 점"],
}

# 추천 가중치 (총합 100%)
# 행동형(CTR↑)·결과형(검색의도 부합) 중심, 총정리 대체용 정리형 15%
WEIGHTS: dict[str, int] = {
    "정리형": 15, "행동형": 25, "질문형": 8, "숫자형": 10,
    "긴급형": 7, "비교형": 4, "결과형": 20, "밀착형": 6,
    "후기형": 2, "시의성형": 3,
}

# '총정리' 허용 비율 — 기존 100% → 10% 이하 (최근 10개 중 1회만)
TOTALJEONGRI_CAP = 0.10

# 제거 대상 마무리 어미 풀 (구버전 + 신버전 모두)
_STRIP_POOL: set[str] = set()
for _v in ENDINGS.values():
    _STRIP_POOL.update(_v)
_STRIP_POOL.update(["총정리", "완벽정리", "한눈에", "필독", "가이드", "총집합"])

# 최근 사용 추적 (프로세스 내 재사용 방지)
_recent_endings: deque[str] = deque(maxlen=10)
_recent_categories: deque[str] = deque(maxlen=3)


def _strip_ending(title: str) -> str:
    """제목 뒷부분의 마무리 어미를 제거하고 베이스만 반환."""
    t = (title or "").strip()
    for ending in sorted(_STRIP_POOL, key=len, reverse=True):
        if t.endswith(ending):
            t = t[: -len(ending)].rstrip(" ,!?~").strip()
            break
    return t


def pick_ending() -> tuple[str, str]:
    """가중치 + 최근 사용 추적 기반으로 (어미, 카테고리) 선택."""
    available = [c for c in WEIGHTS if c not in _recent_categories]
    cats = available if available else list(WEIGHTS.keys())
    cat = random.choices(cats, weights=[WEIGHTS[c] for c in cats])[0]
    candidates = [e for e in ENDINGS[cat] if e not in _recent_endings]
    if not candidates:
        candidates = ENDINGS[cat]
    ending = random.choice(candidates)
    _recent_endings.append(ending)
    _recent_categories.append(cat)
    return ending, cat


def pick_ending_capped() -> tuple[str, str]:
    """'총정리'는 최근 10개 중 1번만 허용."""
    if "총정리" in _recent_endings:
        return pick_ending()
    if random.random() < TOTALJEONGRI_CAP:
        _recent_endings.append("총정리")
        _recent_categories.append("정리형")
        return "총정리", "정리형"
    return pick_ending()


def refinish_title(raw_title: str) -> str:
    """기존 제목의 마무리 어미를 다양화된 어미로 교체 (발행글 정비용)."""
    base = _strip_ending(raw_title)
    if not base:
        return raw_title
    ending, _ = pick_ending_capped()
    return f"{base} {ending}"


# ── 신규 생성용 조립 공식 (미래 파이프라인 연동) ──────────────
# 어미 카테고리 → 잘 어울리는 조립 공식 (A/B/C/D)
_FORMULA_FOR_CAT: dict[str, tuple[str, ...]] = {
    "행동형": ("A", "D"), "결과형": ("B", "A"), "질문형": ("C",),
    "숫자형": ("A", "D"), "긴급형": ("A",), "비교형": ("C",),
    "정리형": ("A",), "후기형": ("A",), "시의성형": ("A", "C"),
    "밀착형": ("A",),
}
_formula_idx = 0


def _choose_formula(cat: str) -> str:
    global _formula_idx
    opts = _FORMULA_FOR_CAT.get(cat, ("A",))
    f = opts[_formula_idx % len(opts)]
    _formula_idx += 1
    return f


def generate_title(*, target: str = "", benefit: str = "", number: str = "",
                   question: str = "", category: str = "loan") -> str:
    """구조형 신규 타이틀 생성 (미래 파이프라인용).

    공식 A: [타겟], [혜택] [어미]
    공식 B: [혜택], [타겟] [어미]
    공식 C: [타겟], [질문] [어미]
    공식 D: [숫자], [타겟] [어미]
    """
    ending, cat = pick_ending_capped()
    formula = _choose_formula(cat)
    if formula == "B" and benefit:
        return f"{benefit}, {target} {ending}"
    if formula == "C" and question:
        return f"{target}, {question} {ending}"
    if formula == "D" and number:
        return f"{number}, {target} {ending}"
    # 공식 A (기본)
    return f"{target}, {benefit} {ending}".rstrip(" ,")


def seed_recent(titles: list[str]) -> None:
    """최근 발행 타이틀에서 어미를 추출해 추적 데크를 시드 (cross-run 다양성)."""
    for t in titles[-10:]:
        base = _strip_ending(t)
        tail = t[len(base):].strip()
        if tail:
            _recent_endings.append(tail)


if __name__ == "__main__":
    samples = [
        "광주 35세 직장인, 내 월급은 평균보다 높을까? 소득 현황 총정리",
        "무주택 직장인, 장애인 운전면허 취득 지원 최대 70만 원 받는 법 총정리",
    ]
    print("== refinish_title 데모 ==")
    for s in samples:
        print(f"  {s}\n    → {refinish_title(s)}")
    print("\n== generate_title 20건 ==")
    for _ in range(20):
        print(" ", generate_title(
            target="무주택 직장인", benefit="전세자금 이자지원",
            number="1,500만 원", question="놓친 적 있으신가요?",
            category="loan"))
