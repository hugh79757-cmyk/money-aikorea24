import os, requests, yaml
from datetime import datetime
from dotenv import load_dotenv
from shared.db_utils import get_conn

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

API_KEY = os.getenv("DATA_GO_KR_API_KEY")
BASE_URL = "http://apis.data.go.kr/1160100/service/GetMarketIndexInfoService"

with open(os.path.join(os.path.dirname(__file__), "config/category_map.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
CATEGORY_MAP = CONFIG["datagokr_category_map"]

INDEX_SERVICE = "getStockMarketIndex"

MAJOR_INDICES = {
    "코스피": "KOSPI",
    "코스닥": "KOSDAQ",
    "코스피 200": "KOSPI 200",
    "코스닥 150": "KOSDAQ 150",
    "KRX 100": "KRX 100",
    "KRX 300": "KRX 300",
    "코스피 100": "KOSPI 100",
    "코스피 50": "KOSPI 50",
    "코스피 대형주": "KOSPI Large",
    "코스피 중형주": "KOSPI Mid",
    "코스피 소형주": "KOSPI Small",
    "코스닥 대형주": "KOSDAQ Large",
    "코스닥 중형주": "KOSDAQ Mid",
    "코스닥 소형주": "KOSDAQ Small",
}

def _build_index_record(item):
    idx_nm = item.get("idxNm", "")
    bas_dt = item.get("basDt", "")
    clpr = item.get("clpr", "")
    vs = item.get("vs", "")
    flt_rt = item.get("fltRt", "")
    mkp = item.get("mkp", "")
    hipr = item.get("hipr", "")
    lopr = item.get("lopr", "")
    idx_csf = item.get("idxCsf", "")

    title = f"{idx_nm} 지수 시세 ({bas_dt})"
    detail = (
        f"기준일: {bas_dt}\n"
        f"분류: {idx_csf}\n"
        f"종가: {clpr}\n"
        f"전일대비: {vs}\n"
        f"등락률: {flt_rt}%\n"
        f"시가: {mkp} / 고가: {hipr} / 저가: {lopr}"
    )

    return {
        "title": title,
        "service_id": f"IDX_{idx_nm}_{bas_dt}",
        "category": CATEGORY_MAP.get("지수시세", "invest"),
        "summary": f"{idx_nm} {bas_dt} 기준 지수: {clpr}, 등락률 {flt_rt}%",
        "detail": detail,
        "target": f"주식 투자자, {idx_nm} 추종 펀드 보유자",
        "persona": "general",
        "org_name": idx_nm,
    }

def fetch_all(dry_run=False):
    print("\n[invest] 지수 시세 수집 시작...")
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "1000",
        "pageNo": "1",
        "resultType": "json",
    }
    url = f"{BASE_URL}/{INDEX_SERVICE}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [ERROR] API 호출 실패: {e}")
        return 0

    body = data.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    if not items:
        print("  지수 데이터 없음")
        return 0

    major_items = [it for it in items if it.get("idxNm", "") in MAJOR_INDICES]
    print(f"  페이지1 {len(items)}개 (주요 {len(major_items)}개)")

    conn = get_conn()
    count = 0
    now = datetime.now().isoformat()

    latest_only = {}
    for item in major_items:
        idx_nm = item.get("idxNm", "")
        bas_dt = item.get("basDt", "")
        if idx_nm not in latest_only or bas_dt > latest_only[idx_nm][0]:
            latest_only[idx_nm] = (bas_dt, item)

    for idx_nm, (bas_dt, item) in sorted(latest_only.items()):
        record = _build_index_record(item)
        service_id = record["service_id"]

        if dry_run:
            print(f"  [DRY] {service_id} | {record['title'][:40]}")
            continue

        conn.execute("""
            INSERT OR REPLACE INTO services
            (service_id,title,category,summary,detail,target,org_name,
             persona,source,status,collected_at,modified_at)
            VALUES (?,?,?,?,?,?,?,?,'datagokr','pending',?,?)
        """, (
            service_id, record["title"], record["category"],
            record["summary"], record["detail"], record["target"],
            record["org_name"], record["persona"], now, now
        ))
        count += 1

    conn.commit()
    conn.close()
    print(f"  지수 {count}건 저장")
    return count

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    fetch_all(dry_run=dry_run)
