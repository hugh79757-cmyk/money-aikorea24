#!/usr/bin/env python3
import json, os, re, time, urllib.request, urllib.parse
from collections import Counter
from pathlib import Path

# .env → .env.common 폴백 로드
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_env import env

API_KEY = env('DATA_GO_KR_API_KEY', '')
BASE_URL = 'https://api.odcloud.kr/api/gov24/v3/serviceDetail'
OUT_FILE = 'public/benefits.json'
PER_PAGE = 100

def fetch_page(page, retries=3):
    params = urllib.parse.urlencode({
        'page': page,
        'perPage': PER_PAGE,
        'serviceKey': API_KEY,
    })
    url = f'{BASE_URL}?{params}'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read().decode('utf-8')
                data = json.loads(raw)
                if data.get('data') is not None:
                    return data
                # data 키가 없으면 잠시 대기 후 재시도
                time.sleep(1 + attempt)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 + attempt * 2)
    return None

def extract_age_range(text):
    patterns = [
        (r'만\s*(\d+)\s*세\s*[~\-～]\s*만?\s*(\d+)\s*세', 'range'),
        (r'(\d+)\s*세\s*[~\-～]\s*(\d+)\s*세', 'range'),
        (r'만\s*(\d+)\s*세\s*이상', 'above'),
        (r'만\s*(\d+)\s*세\s*이하', 'below'),
        (r'만\s*(\d+)\s*세\s*미만', 'below'),
    ]
    for p, t in patterns:
        m = re.search(p, text)
        if m:
            if t == 'range': return [int(m.group(1)), int(m.group(2))]
            elif t == 'above': return [int(m.group(1)), 100]
            elif t == 'below': return [0, int(m.group(1))]
    return []

def extract_category(item):
    text = item.get('서비스명','') + item.get('지원대상','')
    if any(k in text for k in ['청년','취업준비','대학생','졸업','구직','청소년']): return 'youth'
    if any(k in text for k in ['노인','어르신','경로','65세','70세','기초연금','노후']): return 'senior'
    if any(k in text for k in ['아동','유아','영아','임산부','출산','육아','보육','어린이','영유아']): return 'child'
    if any(k in text for k in ['장애','한부모','다문화','저소득','기초생활','수급']): return 'welfare'
    if any(k in text for k in ['중소기업','창업','자영업','소상공인','사업자']): return 'business'
    return 'general'

def extract_regions(text):
    all_regions = ['서울','경기','인천','부산','대구','광주','대전','울산','세종',
                   '강원','충북','충남','충청','전북','전남','경북','경남','제주']
    found = [r for r in all_regions if r in text]
    return found if found else ['전국']

def process_item(item):
    target = item.get('지원대상', '') or ''
    org = item.get('소관기관명', '') or ''
    return {
        'id': item.get('서비스ID', ''),
        'name': item.get('서비스명', ''),
        'purpose': (item.get('서비스목적요약') or item.get('서비스목적') or '')[:150],
        'target': target[:300],
        'content': (item.get('지원내용') or '')[:300],
        'type': item.get('지원유형', ''),
        'method': (item.get('신청방법') or '')[:200],
        'deadline': item.get('신청기한', ''),
        'url': item.get('온라인신청사이트URL', ''),
        'org': org,
        'updated': item.get('수정일시', ''),
        'category': extract_category(item),
        'age_range': extract_age_range(target),
        'regions': extract_regions(target + org),
    }

def main():
    if not API_KEY:
        print('❌ DATA_GO_KR_API_KEY 없음')
        return

    print('📡 gov24 혜택 데이터 수집 시작...')
    first = fetch_page(1)
    if not first:
        print('❌ 첫 페이지 실패')
        return

    total = first.get('totalCount', 0)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    print(f'총 {total}건 / {total_pages}페이지')

    results = [process_item(i) for i in first.get('data', [])]
    failed = []

    for page in range(2, total_pages + 1):
        try:
            data = fetch_page(page)
            if data and data.get('data'):
                results.extend(process_item(i) for i in data['data'])
            else:
                failed.append(page)
            if page % 20 == 0:
                print(f'  {page}/{total_pages} 완료 ({len(results)}건, 실패:{len(failed)})')
            time.sleep(0.15)
        except Exception as e:
            failed.append(page)
            print(f'  ❌ {page}페이지: {e}')
            time.sleep(2)

    # 실패 페이지 재시도
    if failed:
        print(f'\n🔄 실패 {len(failed)}페이지 재시도...')
        for page in failed[:]:
            try:
                time.sleep(1)
                data = fetch_page(page, retries=5)
                if data and data.get('data'):
                    results.extend(process_item(i) for i in data['data'])
                    failed.remove(page)
            except Exception as e:
                print(f'  ❌ {page}페이지 재시도 실패: {e}')

    os.makedirs('public', exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 완료! {len(results)}건 → {OUT_FILE}')
    if failed:
        print(f'⚠️  최종 실패 페이지: {failed}')

    cats = Counter(r['category'] for r in results)
    print('\n카테고리별:')
    for cat, cnt in cats.most_common():
        print(f'  {cat}: {cnt}건')

if __name__ == '__main__':
    main()
