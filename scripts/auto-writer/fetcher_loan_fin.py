import os, requests, yaml, json
from datetime import datetime
from dotenv import load_dotenv
from shared.db_utils import get_conn

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

API_KEY = os.getenv("FINLIFE_API_KEY")
BASE_URL = "https://finlife.fss.or.kr/finlifeapi"

with open(os.path.join(os.path.dirname(__file__), "config/category_map.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
CATEGORY_MAP = CONFIG["finlife_category_map"]
PERSONA_KW = CONFIG["persona_keywords"]

PRODUCTS = [
    {"endpoint": "savingProductsSearch.json",      "type": "정기예금"},
    {"endpoint": "savingProductsSearch.json",      "type": "적금"},
    {"endpoint": "mortgageLoanProductsSearch.json", "type": "주택담보대출"},
    {"endpoint": "rentHouseLoanProductsSearch.json", "type": "전세자금대출"},
]

TOP_GROUPS = {"020000": "은행", "030200": "저축은행"}

def _classify_persona(title, desc=""):
    text = title + desc
    for persona, kws in PERSONA_KW.items():
        include_hit = any(kw in text for kw in kws["include"])
        exclude_hit = any(kw in text for kw in kws["exclude"])
        if include_hit and not exclude_hit:
            return persona
    return "general"

def _build_service_record(product_type, item):
    kor_co_nm = item.get("kor_co_nm", "")
    fin_prdt_nm = item.get("fin_prdt_nm", "")
    title = f"[{product_type}] {kor_co_nm} - {fin_prdt_nm}"

    if product_type in ("정기예금", "적금"):
        join_way = item.get("join_way", "")
        etc_desc = item.get("etc_note", "")
        max_rate = item.get("spcl_cnd", "")
        desc_parts = []
        if join_way: desc_parts.append(f"가입방법: {join_way}")
        if etc_desc: desc_parts.append(etc_desc)
        if max_rate: desc_parts.append(f"우대조건: {max_rate}")
        detail = "\n".join(desc_parts) if desc_parts else ""
        summary = f"{kor_co_nm}의 {fin_prdt_nm} 금리/조건 안내"
        target = f"{kor_co_nm} {fin_prdt_nm} 가입 대상"
    else:
        join_way = item.get("join_way", "")
        loan_inci = item.get("loan_inci_expn", "")
        erly_fee = item.get("erly_rpay_fee", "")
        dly_rate = item.get("dly_rate", "")
        loan_lmt = item.get("loan_lmt", "")
        desc_parts = []
        if join_way: desc_parts.append(f"가입방법: {join_way}")
        if loan_lmt: desc_parts.append(f"대출한도: {loan_lmt}")
        if loan_inci: desc_parts.append(f"부대비용: {loan_inci}")
        if erly_fee: desc_parts.append(f"중도상환수수료: {erly_fee}")
        if dly_rate: desc_parts.append(f"연체이자율: {dly_rate}")
        detail = "\n".join(desc_parts) if desc_parts else ""
        summary = f"{kor_co_nm}의 {fin_prdt_nm} 대출 조건 안내"
        target = f"{kor_co_nm} {fin_prdt_nm} 대출 대상"

    return {
        "title": title,
        "category": CATEGORY_MAP.get(product_type, "loan"),
        "summary": summary,
        "detail": detail,
        "target": target,
        "persona": _classify_persona(title, detail),
        "org_name": kor_co_nm,
    }

def fetch_all(dry_run=False):
    conn = get_conn()

    for prod in PRODUCTS:
        endpoint = prod["endpoint"]
        prod_type = prod["type"]
        print(f"\n[finlife] {prod_type} 수집 시작...")

        for top_grp, top_name in TOP_GROUPS.items():
            params = {
                "auth": API_KEY,
                "topFinGrpNo": top_grp,
                "pageNo": "1",
            }
            url = f"{BASE_URL}/{endpoint}"
            data = None
            for attempt in range(2):
                try:
                    resp = requests.get(url, params=params, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception as e:
                    if attempt == 0:
                        print(f"  [RETRY] {prod_type}/{top_name} {e}")
                        continue
                    print(f"  [ERROR] {prod_type}/{top_name} API 호출 실패: {e}")
            if data is None:
                continue

            result = data.get("result", {})
            base_list = result.get("baseList", [])
            if not base_list:
                print(f"  {prod_type}/{top_name}: 데이터 없음")
                continue

            print(f"  {prod_type}/{top_name}: {len(base_list)}개 상품")

            for item in base_list:
                fin_co_no   = item.get("fin_co_no", "")
                fin_prdt_cd = item.get("fin_prdt_cd", "")
                service_id = f"FINLIFE_{prod_type}_{fin_co_no}_{fin_prdt_cd}"

                record = _build_service_record(prod_type, item)

                if dry_run:
                    print(f"  [DRY] {service_id} | {record['title'][:40]} | {record['category']} | {record['persona']}")
                    continue

                exists = conn.execute(
                    "SELECT id FROM services WHERE service_id=?", (service_id,)
                ).fetchone()

                now = datetime.now().isoformat()
                if not exists:
                    conn.execute("""
                        INSERT INTO services
                        (service_id,title,category,summary,detail,target,org_name,
                         persona,source,status,collected_at,modified_at)
                        VALUES (?,?,?,?,?,?,?,?,'finlife','pending',?,?)
                    """, (
                        service_id, record["title"], record["category"],
                        record["summary"], record["detail"], record["target"],
                        record["org_name"], record["persona"], now, now
                    ))

            conn.commit()

    conn.close()
    print("\n[finlife fetcher 완료]")

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    fetch_all(dry_run=dry_run)
