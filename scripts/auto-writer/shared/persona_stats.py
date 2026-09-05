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

# 시군 → 광역 매핑 (persona 통계 지리적 불일치 해소)
# 서비스 title/field에 "무주군"처럼 도명 없이 시군만 있을 때 사용
COUNTY_TO_REGION = {
    # 전북 (128건 최다)
    "무주": "전북", "김제": "전북", "진안": "전북", "남원": "전북", "익산": "전북",
    "전주": "전북", "군산": "전북", "정읍": "전북", "완주": "전북", "장수": "전북",
    "임실": "전북", "순창": "전북", "고창": "전북", "부안": "전북",
    # 전남
    "목포": "전남", "여수": "전남", "순천": "전남", "나주": "전남", "광양": "전남",
    "담양": "전남", "곡성": "전남", "구례": "전남", "고흥": "전남", "보성": "전남",
    "화순": "전남", "장흥": "전남", "강진": "전남", "해남": "전남", "영암": "전남",
    "무안": "전남", "함평": "전남", "영광": "전남", "장성": "전남", "완도": "전남",
    "진도": "전남", "신안": "전남",
    # 충남
    "천안": "충남", "공주": "충남", "보령": "충남", "아산": "충남", "서산": "충남",
    "논산": "충남", "계룡": "충남", "당진": "충남", "금산": "충남", "부여": "충남",
    "서천": "충남", "청양": "충남", "홍성": "충남", "예산": "충남", "태안": "충남",
    # 충북
    "청주": "충북", "충주": "충북", "제천": "충북", "보은": "충북", "옥천": "충북",
    "영동": "충북", "증평": "충북", "진천": "충북", "괴산": "충북", "음성": "충북", "단양": "충북",
    # 경북
    "포항": "경북", "경주": "경북", "김천": "경북", "안동": "경북", "구미": "경북",
    "영주": "경북", "영천": "경북", "상주": "경북", "문경": "경북", "경산": "경북",
    "의성": "경북", "청송": "경북", "영양": "경북", "영덕": "경북", "청도": "경북",
    "고령": "경북", "성주": "경북", "칠곡": "경북", "예천": "경북", "봉화": "경북", "울진": "경북", "울릉": "경북",
    # 경남
    "창원": "경남", "진주": "경남", "통영": "경남", "사천": "경남", "김해": "경남",
    "밀양": "경남", "거제": "경남", "양산": "경남", "의령": "경남", "함안": "경남",
    "창녕": "경남", "고성": "경남", "남해": "경남", "하동": "경남", "산청": "경남",
    "함양": "경남", "거창": "경남", "합천": "경남",
    # 강원
    "춘천": "강원", "원주": "강원", "강릉": "강원", "동해": "강원", "태백": "강원",
    "속초": "강원", "삼척": "강원", "홍천": "강원", "횡성": "강원", "영월": "강원",
    "평창": "강원", "정선": "강원", "철원": "강원", "화천": "강원", "양구": "강원",
    "인제": "강원", "양양": "강원",
    # 경기
    "수원": "경기", "성남": "경기", "의정부": "경기", "안양": "경기", "부천": "경기",
    "광명": "경기", "평택": "경기", "동두천": "경기", "안산": "경기", "고양": "경기",
    "과천": "경기", "구리": "경기", "남양주": "경기", "오산": "경기", "시흥": "경기",
    "군포": "경기", "의왕": "경기", "하남": "경기", "용인": "경기", "파주": "경기",
    "이천": "경기", "안성": "경기", "김포": "경기", "화성": "경기",
    "양주": "경기", "포천": "경기", "여주": "경기", "연천": "경기", "가평": "경기", "양평": "경기",
    # 서울 구
    "종로": "서울", "중구": "서울", "용산": "서울", "성동": "서울", "광진": "서울",
    "동대문": "서울", "중랑": "서울", "성북": "서울", "강북": "서울", "도봉": "서울",
    "노원": "서울", "은평": "서울", "서대문": "서울", "마포": "서울", "양천": "서울",
    "강서": "서울", "구로": "서울", "금천": "서울", "영등포": "서울", "동작": "서울",
    "관악": "서울", "서초": "서울", "강남": "서울", "송파": "서울", "강동": "서울",
}

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
    # 1) 시군 → 광역 매핑 우선 (무주군 → 전북 등)
    for county, region in COUNTY_TO_REGION.items():
        if county in text:
            return region
    # 2) 광역 직접 언급
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
