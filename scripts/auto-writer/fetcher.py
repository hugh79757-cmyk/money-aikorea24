import os, requests, yaml, json
from datetime import datetime
from dotenv import load_dotenv
from shared.db_utils import get_conn, get_last_fetched, update_fetch_meta

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

API_KEY  = os.getenv("DATA_GO_KR_API_KEY")
BASE_URL = "https://api.odcloud.kr/api/gov24/v3/serviceList"

with open(os.path.join(os.path.dirname(__file__), "config/category_map.yaml"),
          encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

FIELD_MAP   = CONFIG["gov24_category_map"]
PERSONA_KW  = CONFIG["persona_keywords"]

def classify_category(item):
    field = item.get("서비스분야", "")
    return FIELD_MAP.get(field)

def classify_persona(item):
    """지원대상 + 서비스명 기반 2차 필터링으로 페르소나 분류"""
    target = item.get("지원대상", "") + item.get("서비스명", "")
    matched = []
    for persona, kws in PERSONA_KW.items():
        include_hit = any(kw in target for kw in kws["include"])
        exclude_hit = any(kw in target for kw in kws["exclude"])
        if include_hit and not exclude_hit:
            matched.append(persona)
    return matched[0] if matched else "general"

def extract_persona_hint(item):
    """지원대상에서 연령·소득·지역 힌트 추출"""
    target = item.get("지원대상", "")
    hint = {}
    import re
    age = re.search(r"만\s*(\d+)세?\s*[~∼-]\s*만?\s*(\d+)세", target)
    if age:
        hint["age_range"] = f"{age.group(1)}~{age.group(2)}세"
    income = re.search(r"(연\s*소득|소득)\s*(\d[\d,]+)\s*만?\s*원\s*이하", target)
    if income:
        hint["income_limit"] = income.group(2) + "만원 이하"
    if "무주택" in target:
        hint["housing"] = "무주택자"
    if "신혼부부" in target or "혼인" in target:
        hint["marriage"] = "신혼부부"
    return json.dumps(hint, ensure_ascii=False)

def fetch_all(dry_run=False):
    last = get_last_fetched()
    print(f"[fetcher] 마지막 수집 시각: {last}")

    r = requests.get(BASE_URL,
        params={"page":1,"perPage":1,"serviceKey":API_KEY}, timeout=10)
    total = r.json().get("totalCount", 0)
    print(f"[fetcher] 총 서비스 수: {total:,}건")

    conn = get_conn()
    inserted = updated = skipped = excluded = 0

    for page in range(1, (total // 100) + 2):
        resp = requests.get(BASE_URL,
            params={"page":page,"perPage":100,"serviceKey":API_KEY}, timeout=30)
        items = resp.json().get("data", [])
        if not items:
            break

        for item in items:
            service_id  = item.get("서비스ID", "")
            modified_at = item.get("수정일시", "")
            category    = classify_category(item)

            if category is None:
                excluded += 1
                continue

            persona      = classify_persona(item)
            persona_hint = extract_persona_hint(item)
            title        = item.get("서비스명", "")
            summary      = item.get("서비스목적요약", "")
            detail       = item.get("지원내용", "")
            target       = item.get("지원대상", "")
            apply_method = item.get("신청방법", "")
            contact      = item.get("전화문의", "")
            org_name     = item.get("소관기관명", "")
            detail_url   = item.get("상세조회URL", "")

            if dry_run:
                print(f"  [DRY] {service_id} | {title[:30]} | {category} | {persona}")
                continue

            exists = conn.execute(
                "SELECT id, modified_at FROM services WHERE service_id=?",
                (service_id,)
            ).fetchone()

            now = datetime.now().isoformat()
            if not exists:
                conn.execute("""
                    INSERT INTO services
                    (service_id,title,category,field,summary,detail,target,
                     apply_method,contact,org_name,detail_url,persona,
                     persona_hint,status,collected_at,modified_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?)
                """, (service_id,title,category,
                      item.get("서비스분야",""),
                      summary,detail,target,apply_method,contact,
                      org_name,detail_url,persona,persona_hint,now,modified_at))
                inserted += 1
            elif exists["modified_at"] != modified_at:
                conn.execute("""
                    UPDATE services SET
                        title=?,summary=?,detail=?,target=?,apply_method=?,
                        persona_hint=?,modified_at=?,
                        status=CASE WHEN status='published' THEN 'updated'
                                    ELSE status END
                    WHERE service_id=?
                """, (title,summary,detail,target,apply_method,
                      persona_hint,modified_at,service_id))
                updated += 1
            else:
                skipped += 1

        conn.commit()
        print(f"  페이지 {page} 완료 | 신규:{inserted} 수정:{updated} 스킵:{skipped} 제외:{excluded}", end="\r")

    conn.close()
    update_fetch_meta(inserted + updated)
    print(f"\n[fetcher 완료] 신규:{inserted} 수정:{updated} 스킵:{skipped} 제외:{excluded}")

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    fetch_all(dry_run=dry_run)
