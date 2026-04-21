#!/usr/bin/env python3
"""
money.aikorea24.kr 자동 글 생성기
사용법:
  python3 scripts/generate_post.py --category insurance --topic "실손보험 5세대"
  python3 scripts/generate_post.py --category nomad --topic "AI 부업 2026"
  python3 scripts/generate_post.py --list   # 수집된 소스 목록 확인
  python3 scripts/generate_post.py --fetch  # 공공 API 데이터 수집
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_DIR  = PROJECT_ROOT / "src" / "content"
DATA_DIR     = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── 카테고리 → 컬렉션 매핑 ─────────────────────────────────
CATEGORIES = {
    "insurance": "보험",
    "invest":    "투자·절세",
    "loan":      "대출·부동산",
    "tax":       "세금·절약",
    "nomad":     "디지털노마드",
}

KST = timezone(timedelta(hours=9))

# ── 공공 API 수집기 ────────────────────────────────────────
def fetch_bok_rate():
    """한국은행 ECOS API - 기준금리 최신값"""
    api_key = os.environ.get("BOK_API_KEY", "")
    if not api_key:
        return {"source": "한국은행", "data": None, "note": "BOK_API_KEY 환경변수 필요"}
    try:
        url = (
            "https://ecos.bok.or.kr/api/StatisticSearch/"
            + api_key
            + "/json/kr/1/5/722Y001/D/20250101/20261231/0101000"
        )
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read())
        rows = data.get("StatisticSearch", {}).get("row", [])
        if rows:
            latest = rows[-1]
            return {
                "source": "한국은행 ECOS",
                "item": "기준금리",
                "value": latest.get("DATA_VALUE"),
                "date": latest.get("TIME"),
            }
    except Exception as e:
        return {"source": "한국은행", "error": str(e)}
    return {"source": "한국은행", "data": None}

def fetch_data_go(service_key, endpoint, params):
    """data.go.kr 공공 API 공통 호출"""
    base = "https://apis.data.go.kr/" + endpoint
    params["serviceKey"] = service_key
    params["_type"] = "json"
    qs = urllib.parse.urlencode(params)
    url = base + "?" + qs
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def fetch_all_and_save():
    """모든 공공 API 수집 후 data/ 저장"""
    result = {}

    # 1. 한국은행 기준금리
    result["bok_rate"] = fetch_bok_rate()

    # 2. 아파트 실거래가 (data.go.kr) - 키 필요
    data_key = os.environ.get("DATA_GO_KEY", "")
    if data_key:
        today = datetime.now(KST)
        ym = today.strftime("%Y%m")
        apt_data = fetch_data_go(
            data_key,
            "1613000/RTMSDataSvcAptTradeDev",
            {"LAWD_CD": "11110", "DEAL_YMD": ym, "numOfRows": "10"},
        )
        result["apt_trade"] = apt_data
    else:
        result["apt_trade"] = {"note": "DATA_GO_KEY 환경변수 필요"}

    out_path = DATA_DIR / "fetched.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[fetch] 저장 완료: {out_path}")
    for k, v in result.items():
        print(f"  {k}: {v}")

# ── 슬러그 생성 ────────────────────────────────────────────
def to_slug(text):
    text = re.sub(r"[^\w\s가-힣]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text.lower()

# ── 프론트매터 생성 ────────────────────────────────────────
def make_frontmatter(category, topic, tags=None):
    now = datetime.now(KST).strftime("%Y-%m-%d")
    cat_label = CATEGORIES.get(category, category)
    default_tags = [topic.replace(" ", ""), cat_label, "2026", category]
    if tags:
        default_tags = tags + default_tags
    # 중복 제거
    seen = []
    for t in default_tags:
        if t not in seen:
            seen.append(t)
    tags_str = json.dumps(seen[:8], ensure_ascii=False)
    return f"""---
title: "{topic} 2026년 완벽 가이드"
description: "{topic}에 대해 2026년 최신 기준으로 정리합니다. 조건별 분석과 AI 활용 팁까지 포함합니다."
draft: true
tags: {tags_str}
categories: ["{cat_label}"]
pubDate: {now}
---"""

# ── 본문 템플릿 생성 ───────────────────────────────────────
def make_body(category, topic):
    cat_label = CATEGORIES.get(category, category)
    return f"""
이 글에서는 **{topic}**에 대해 2026년 최신 기준으로 상세히 정리합니다.
복잡한 내용을 조건별로 나눠 설명하므로, 목차를 먼저 확인하고 필요한 섹션만 읽어도 됩니다.

## {topic} 기본 개념 정리

{topic}을 처음 접하는 분도 이해할 수 있도록 핵심 개념부터 설명합니다.

**TODO: 기본 개념 내용 작성**

2026년 기준으로 적용되는 주요 변경 사항도 함께 확인합니다.

## 조건별 상세 분석

### 조건 1: 일반적인 경우

**TODO: 일반 조건 분석 내용 작성**

### 조건 2: 특수한 경우

**TODO: 특수 조건 분석 내용 작성**

## {topic} 신청 방법 및 절차

**TODO: 신청 절차 단계별 작성**

공식 사이트에서 직접 확인하는 것을 권장합니다.

## AI로 {topic} 직접 해결하는 방법

ChatGPT 또는 Claude에 아래와 같이 요청하면 내 상황에 맞는 분석을 받을 수 있습니다.

프롬프트 예시:

"나는 [나이/직업/조건]이고 {topic}을 알아보고 있습니다. 내 상황에서 가장 유리한 선택지를 분석해주세요."

[AI 도구 추천 보기](https://aikorea24.kr/tools/)에서 금융 분석에 활용할 수 있는 도구를 확인해보세요.

## 결론

**TODO: 핵심 요약 및 독자가 지금 당장 취할 행동 1가지 작성**

오늘 할 수 있는 첫 번째 행동은 TODO 입니다.

## 참고 자료

- [금융감독원 금융소비자정보포털](https://fine.fss.or.kr)
- [국세청 홈택스](https://www.hometax.go.kr)
- [주택금융공사](https://www.nhuf.molit.go.kr)

##{topic} #{cat_label} #2026 #AI활용
"""

# ── 파일 저장 ─────────────────────────────────────────────
def save_post(category, topic, slug=None):
    if slug is None:
        slug = to_slug(topic)
    out_dir = CONTENT_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"

    if out_path.exists():
        print(f"[skip] 이미 존재: {out_path}")
        return

    content = make_frontmatter(category, topic) + "\n" + make_body(category, topic)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[생성] {out_path}")

# ── 수집 소스 목록 출력 ────────────────────────────────────
def list_sources():
    fetched = DATA_DIR / "fetched.json"
    if fetched.exists():
        with open(fetched, encoding="utf-8") as f:
            data = json.load(f)
        print("[수집된 데이터]")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("[안내] 수집된 데이터 없음. --fetch 로 수집 먼저 실행하세요.")

    print("\n[현재 글 목록]")
    for cat in CATEGORIES:
        cat_dir = CONTENT_DIR / cat
        if cat_dir.exists():
            files = list(cat_dir.glob("*.md"))
            print(f"  {cat}: {len(files)}개")
            for f in files:
                print(f"    - {f.stem}")

# ── 배치 생성: topics.json 에서 읽어서 일괄 생성 ──────────
def batch_from_json(json_path):
    with open(json_path, encoding="utf-8") as f:
        topics = json.load(f)
    for item in topics:
        save_post(item["category"], item["topic"], item.get("slug"))

# ── CLI ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="money.aikorea24.kr 자동 글 생성기")
    parser.add_argument("--category", choices=list(CATEGORIES.keys()), help="카테고리")
    parser.add_argument("--topic",    help="글 주제")
    parser.add_argument("--slug",     help="파일명 슬러그 (선택)")
    parser.add_argument("--fetch",    action="store_true", help="공공 API 데이터 수집")
    parser.add_argument("--list",     action="store_true", help="수집 소스 및 글 목록 확인")
    parser.add_argument("--batch",    help="topics.json 경로로 일괄 생성")
    args = parser.parse_args()

    if args.fetch:
        fetch_all_and_save()
    elif args.list:
        list_sources()
    elif args.batch:
        batch_from_json(args.batch)
    elif args.category and args.topic:
        save_post(args.category, args.topic, args.slug)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
