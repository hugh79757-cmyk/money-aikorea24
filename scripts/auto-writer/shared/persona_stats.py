import os, json, re
from datetime import datetime
from functools import lru_cache

# 2026-09-03: persona-stats.json moved data/ (25MiB Pages limit) — fallback chain
_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "../../../data/persona-stats.json"),
    os.path.join(os.path.dirname(__file__), "../../../public/persona-stats.json"),
    os.path.join(os.path.dirname(__file__), "../../../public/persona-stats-decade.json"),
]
STATS_PATH = next((x for x in _CANDIDATES if os.path.exists(x)), _CANDIDATES[0])

# 페르소나 → 대표 연령 (통계청 exact-age 키, income 데이터 포함)
PERSONA_AGE_MAP = {
    "youth":     "25",
    "worker":    "35",
    "newlywed":  "33",
    "midlife":   "45",
    "lowincome": "40",
    "unhoused":  "40",
    "general":   "35",
}

GENDERS = ("남자", "여자")
DEFAULT_REGION = "서울"
REGIONS = ["서울", "부산", "대구", "인천", "광주", "대전",
           "울산", "세종", "경기", "강원", "충북", "충남",
           "전북", "전남", "경북", "경남", "제주"]

# ── 로더 ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load() -> dict:
    for cand in _CANDIDATES:
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                return json.load(f)
    # ponytail: no stats file — return empty so build_user_prompt still works without stats
    return {}

# ── 키 리졸버 ─────────────────────────────────────────────────

def resolve_region(service: dict) -> str:
    text = " ".join(str(v) for v in service.values())
    for r in REGIONS:
        if r in text:
            return r
    return DEFAULT_REGION

def resolve_keys(service: dict) -> list[str]:
    """서비스 레코드 → persona-stats.json 조회용 키 리스트"""
    persona = service.get("persona", "general")
    age = PERSONA_AGE_MAP.get(persona, "35")
    region = resolve_region(service)
    return [f"{region}_{g}_{age}" for g in GENDERS]


# ── 통계 요약 ─────────────────────────────────────────────────

SAMPLE_FIELDS = ("income", "marital", "housing", "total")


def _summarize(data: dict) -> dict | None:
    if not data:
        return None
    inc = data.get("income") or {}

    m = data.get("marital") or {}
    tm = sum(m.values()) or 1

    h = data.get("housing") or {}
    th = sum(h.values()) or 1

    # 대표 직업 top 3 (jobs)
    jobs = data.get("jobs") or {}
    top_jobs = sorted(jobs.items(), key=lambda x: -x[1])[:3]

    return {
        "income_est":  inc.get("income_estimate", 0),
        "income_nat":  inc.get("income_national_avg", 0),
        "income_src":  inc.get("income_source", ""),
        "income_year": inc.get("income_year", ""),
        "total":       data.get("total", 0),
        "married_pct": round(m.get("배우자있음", 0) / tm * 100, 1),
        "single_pct":  round(m.get("미혼", 0) / tm * 100, 1),
        "divorce_pct": round(m.get("이혼", 0) / tm * 100, 1),
        "top_housing": [(k, round(v / th * 100, 1))
                        for k, v in sorted(h.items(), key=lambda x: -x[1])[:3]],
        "top_jobs": top_jobs,
    }


def get_stats(keys: list[str]) -> dict[str, dict]:
    all_stats = _load()
    return {k: _summarize(all_stats[k])
            for k in keys if k in all_stats and _summarize(all_stats[k])}


# ── 프롬프트 포매터 ──────────────────────────────────────────

def format_for_prompt(stats: dict[str, dict]) -> str:
    """LLM 프롬프트 주입용 3~6줄 통계 요약"""
    lines = []
    for key, d in stats.items():
        label = key.replace("_", " ")
        parts = [f"[{label}]"]

        inc = d.get("income_est", 0)
        inc_nat = d.get("income_nat", 0)
        if inc:
            s = f"월평균소득 {inc}만원"
            if inc_nat and inc_nat != inc:
                s += f" (vs 전국평균 {inc_nat}만원)"
            parts.append(s)

        single = d.get("single_pct", 0)
        married = d.get("married_pct", 0)
        if single:
            parts.append(f"미혼율 {single}%")
        if married:
            parts.append(f"기혼율 {married}%")

        housing = d.get("top_housing", [])
        if housing:
            parts.append(f"주거1순위: {housing[0][0]} {housing[0][1]}%")

        tot = d.get("total", 0)
        if tot:
            parts.append(f"표본 {tot}명")

        lines.append(" · ".join(parts))

    return "\n".join(lines)


# ── FOMO 훅 생성기 ────────────────────────────────────────────

def make_fomo_hook(stats: dict[str, dict]) -> str:
    """통계 기반 도입부 FOMO 훅 문장 (LLM이 프롬프트에서 참조)"""
    if not stats:
        return ""
    key = next(iter(stats))
    d = stats[key]
    label = key.replace("_", " ")

    parts = []
    inc = d.get("income_est", 0)
    if inc:
        parts.append(f"월 평균 소득 **{inc}만원**")

    single = d.get("single_pct", 0)
    married = d.get("married_pct", 0)
    if single and single > 30:
        parts.append(f"**{single}%**가 미혼")
    elif married and married > 30:
        parts.append(f"**{married}%**는 기혼")

    housing = d.get("top_housing", [])
    if housing:
        name, pct = housing[0]
        if pct > 25:
            parts.append(f"**{pct}%**는 {name}에 거주")

    tot = d.get("total", 0)
    income_year = d.get("income_year", str(datetime.now().year - 1))
    suffix = f" (표본 {tot}명 • 통계청 {income_year})" if tot else ""

    if parts:
        return f"📊 {label}의 " + ", ".join(parts) + f"입니다.{suffix}"
    return ""
