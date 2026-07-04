"""
네이버 검색 API 관심도 검증 모듈
"""
import os
import re
import requests
from datetime import datetime


NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
DAILY_LIMIT = int(os.getenv("NAVER_DAILY_LIMIT", "100"))

_call_count = 0


def _check_quota():
    global _call_count
    if _call_count >= DAILY_LIMIT:
        return False
    _call_count += 1
    return True


def extract_keywords(title: str, summary: str) -> list[str]:
    """제목+요약에서 핵심 키워드 추출 (불용어 제거, 최대 3개)"""
    stopwords = {
        "지원", "대상", "방법", "안내", "신청", "조회", "정보", "제공",
        "관련", "사항", "해당", "법률", "지원금", "제도", "정책", "사업",
        "총정리", "완벽정리", "한눈에", "필독", "가이드",
    }
    text = f"{title} {summary}"
    # 명사 추출 (간단한 정규식: 2자 이상 한글 명사)
    words = re.findall(r'[가-힣]{2,}', text)
    filtered = [w for w in words if w not in stopwords and len(w) >= 2]
    # 빈도 기반 상위 3개
    from collections import Counter
    return [w for w, _ in Counter(filtered).most_common(3)]


def search_naver_blog(query: str) -> list[dict]:
    """네이버 블로그 검색 API 호출 (최신순 5건)"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("  [naver] API 키 없음 — 검증 스킵")
        return []

    if not _check_quota():
        print("  [naver] 일일 한도 초과 — 검증 스킵")
        return []

    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": 5,
        "sort": "date",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"  [naver] API 에러: {resp.status_code}")
            return []
        items = resp.json().get("items", [])
        return items
    except Exception as e:
        print(f"  [naver] 요청 실패: {e}")
        return []


def check_topic_relevance(title: str, summary: str) -> dict:
    """
    서비스/주제가 2026년에도 관심 있는지 네이버 검색으로 확인.
    Returns: {"relevance": "fresh"|"stale"|"none", "latest_date": str, "result_count": int}
    """
    keywords = extract_keywords(title, summary)
    if not keywords:
        return {"relevance": "none", "latest_date": "", "result_count": 0}

    query = " ".join(keywords[:2])
    items = search_naver_blog(query)

    if not items:
        return {"relevance": "none", "latest_date": "", "result_count": 0}

    # 최신 글 날짜 확인 (네이버 블로그 결과의 pubDate 필드)
    latest_date = ""
    for item in items:
        pub_date = item.get("postdate", "")
        if pub_date and (not latest_date or pub_date > latest_date):
            latest_date = pub_date

    # 최신 글이 1년 이상 오래된지 확인
    if latest_date:
        try:
            latest = datetime.strptime(latest_date, "%Y%m%d")
            age_days = (datetime.now() - latest).days
            if age_days > 365:
                return {"relevance": "stale", "latest_date": latest_date, "result_count": len(items)}
        except ValueError:
            pass

    return {"relevance": "fresh", "latest_date": latest_date, "result_count": len(items)}
