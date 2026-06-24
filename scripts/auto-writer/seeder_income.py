"""
내 또래 연봉 시리즈 — persona-stats 기반 시드 레코드 생성
실행: python3 seeder_income.py [--dry-run]
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from datetime import datetime
from shared.db_utils import get_conn
from shared.persona_stats import _load as load_stats, PERSONA_AGE_MAP

# ── 발행할 주제 ───────────────────────────────────────────────
TOPICS = [
    # (region, title_prefix, gender, age_key, persona)
    ("서울", "서울 20대 직장인",  "남자", "25", "youth"),
    ("서울", "서울 20대 여성",   "여자", "25", "youth"),
    ("서울", "서울 30대 직장인",  "남자", "35", "worker"),
    ("서울", "서울 30대 여성",   "여자", "35", "worker"),
    ("서울", "서울 40대 가장",   "남자", "45", "midlife"),
    ("서울", "서울 40대 직장인",  "여자", "45", "midlife"),
    ("부산", "부산 30대 직장인",  "남자", "35", "worker"),
    ("부산", "부산 30대 여성",   "여자", "35", "worker"),
    ("경기", "경기 30대 직장인",  "남자", "35", "worker"),
    ("경기", "경기 30대 여성",   "여자", "35", "worker"),
    ("인천", "인천 30대 직장인",  "남자", "35", "worker"),
    ("대구", "대구 30대 직장인",  "남자", "35", "worker"),
    ("대전", "대전 30대 직장인",  "남자", "35", "worker"),
    ("광주", "광주 30대 직장인",  "남자", "35", "worker"),
    ("서울", "서울 신혼부부",     "남자", "33", "newlywed"),
    ("서울", "서울 20대 후반",   "남자", "29", "youth"),
    ("경기", "경기 20대 직장인",  "남자", "25", "youth"),
    ("부산", "부산 20대 여성",   "여자", "25", "youth"),
    ("인천", "인천 30대 여성",   "여자", "35", "worker"),
    ("대구", "대구 30대 여성",   "여자", "35", "worker"),
]


def _build_stat_summary(stat: dict) -> str:
    inc = stat.get("income_est", 0)
    nat = stat.get("income_nat", 0)
    inc_src = stat.get("income_src", "통계청")
    inc_yr = stat.get("income_year", "2024")
    married = stat.get("married_pct", 0)
    single = stat.get("single_pct", 0)
    top_h = stat.get("top_housing", [])
    total = stat.get("total", 0)

    parts = [f"월평균소득 {inc}만원"]
    if nat and nat != inc:
        parts.append(f"(전국평균 {nat}만원)")
    parts.append(f"기혼율 {married}%")
    if top_h:
        parts.append(f"주거1순위 {top_h[0][0]} {top_h[0][1]}%")
    parts.append(f"표본 {total}명")
    return " · ".join(parts)


def generate_seeds(dry_run=False):
    conn = get_conn()
    all_stats = load_stats()
    now = datetime.now().isoformat()
    count = 0

    for region, prefix, gender, age, persona in TOPICS:
        key = f"{region}_{gender}_{age}"
        stat = all_stats.get(key)
        if not stat:
            print(f"  [SKIP] 키 없음: {key}")
            continue

        inc = stat.get("income", {}).get("income_estimate", 0)
        title = f"[2026] {prefix} 평균 월급 {inc}만원… 나는 어디쯤?"
        summary_text = _build_stat_summary({
            "income_est": inc,
            "income_nat": stat.get("income", {}).get("income_national_avg", 0),
            "married_pct": round(stat.get("marital", {}).get("배우자있음", 0) / max(sum(stat.get("marital", {}).values()), 1) * 100, 1),
            "single_pct": round(stat.get("marital", {}).get("미혼", 0) / max(sum(stat.get("marital", {}).values()), 1) * 100, 1),
            "top_housing": sorted(stat.get("housing", {}).items(), key=lambda x: -x[1])[:3],
            "total": stat.get("total", 0),
        })

        detail = (
            f"기준: {key.replace('_', ' ')}\n"
            f"월평균소득: {inc}만원\n"
            f"전국평균: {stat.get('income', {}).get('income_national_avg', 0)}만원\n"
            f"상위백분위: {stat.get('income', {}).get('top_percentile', 0)}%\n"
            f"출처: {stat.get('income', {}).get('income_source', '통계청')} {stat.get('income', {}).get('income_year', '2024')}\n"
            f"표본: {stat.get('total', 0)}명\n"
        )

        gender_kr = "전체"
        if gender == "남자": gender_kr = "남성"
        elif gender == "여자": gender_kr = "여성"
        target = f"{region} 거주 {age}세 {gender_kr} 연봉·소득이 궁금한 직장인"

        service_id = f"INCOME_{region}_{gender}_{age}_{now[:8]}"

        if dry_run:
            print(f"  [DRY] {service_id} | {title[:50]}")
            continue

        # 기존 시드가 있으면 스킵
        exists = conn.execute(
            "SELECT id FROM services WHERE service_id=?", (service_id,)
        ).fetchone()
        if exists:
            print(f"  [SKIP] 이미 존재: {service_id}")
            continue

        conn.execute("""
            INSERT INTO services
            (service_id, title, category, summary, detail, target, org_name,
             persona, source, status, collected_at, modified_at)
            VALUES (?,?,?,?,?,?,?,?,'income_series','pending',?,?)
        """, (
            service_id, title, "invest", summary_text, detail, target,
            region, persona, now, now
        ))
        count += 1
        print(f"  [INSERT] {title[:50]}")

    conn.commit()
    conn.close()
    print(f"\n✅ 시드 {count}건 생성")
    return count


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN 모드 ===")
    generate_seeds(dry_run=dry_run)
