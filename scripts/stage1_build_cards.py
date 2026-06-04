#!/usr/bin/env python3
"""Stage 1 통합: decision-cards.json 생성 (전국 복지 + 지역 특화 복지)"""
import json
from collections import Counter, defaultdict

# ============================================================
# 1. 데이터 로드
# ============================================================
with open('public/benefits-curated.json') as f:
    curated = json.load(f)
with open('public/welfare-local.json') as f:
    welfare_local_raw = json.load(f)
with open('public/persona-stats.json') as f:
    stats = json.load(f)

# ============================================================
# 2. ctpvNm → 페르소나 region 매핑 테이블
# ============================================================
# persona-stats.json 지역 키 → 정규화 지역명 (ctpv→region과 동일하게)
PERSONA_REGION_MAP = {
    '서울': '서울', '경기': '경기', '인천': '인천', '부산': '부산',
    '대구': '대구', '대전': '대전', '광주': '광주', '울산': '울산', '세종': '세종',
    '강원': '강원',
    '충청북': '충북', '충청남': '충남',
    '전라남': '전남', '전북': '전북',
    '경상북': '경북', '경상남': '경남',
    '제주': '제주',
}

CTPV_TO_REGION = {
    '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
    '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
    '울산광역시': '울산', '세종특별자치시': '세종',
    '경기도': '경기',
    '강원특별자치도': '강원', '강원도': '강원',
    '충청북도': '충북', '충청남도': '충남',
    '전북특별자치도': '전북', '전라북도': '전북',
    '전라남도': '전남',
    '경상북도': '경북', '경상남도': '경남',
    '제주특별자치도': '제주',
}

# ============================================================
# 3. welfare-local 정규화
# ============================================================
def safe_str(val):
    if not val:
        return ''
    return str(val).strip()

def normalize_welfare_local(item):
    ctpv = safe_str(item.get('ctpvNm', ''))
    region = CTPV_TO_REGION.get(ctpv, '')
    sgg = safe_str(item.get('sggNm', ''))

    # servDgst 빈값 → servNm fallback
    dgst = safe_str(item.get('servDgst', ''))
    if not dgst:
        dgst = safe_str(item.get('servNm', ''))

    # aplyMtdNm 빈값(21%) → 담당 부서 문의
    aply = safe_str(item.get('aplyMtdNm', ''))
    if not aply:
        dept = safe_str(item.get('bizChrDeptNm', ''))
        aply = f'{dept} 담당 부서 문의' if dept else '담당 부서 문의'

    life_raw = safe_str(item.get('lifeNmArray', ''))
    life_tags = [t.strip() for t in life_raw.split(',') if t.strip()] if life_raw else []

    return {
        'id': safe_str(item.get('servId', '')),
        'name': safe_str(item.get('servNm', '')),
        'summary': dgst,
        'region': region,
        'sgg': sgg,
        'life_tags': life_tags,
        'apply_method': aply,
        'dept': safe_str(item.get('bizChrDeptNm', '')),
        'support_cycle': safe_str(item.get('sprtCycNm', '')),
        'url': safe_str(item.get('servDtlLink', '')),
        'inq_num': int(safe_str(item.get('inqNum', '0')) or '0'),
        'updated': safe_str(item.get('lastModYmd', '')),
    }

local_welfares = [normalize_welfare_local(item) for item in welfare_local_raw]
local_valid = [w for w in local_welfares if w['region']]

# ============================================================
# 4. 생애주기 매핑
# ============================================================
LIFESTAGE_MAP = {
    '20대': ['청년'],
    '30대': ['청년', '중장년'],
    '40대': ['중장년'],
    '50대': ['중장년'],
    '60대': ['중장년', '노년'],
    '70대이상': ['노년'],
}

def get_lifestages(age_str):
    return LIFESTAGE_MAP.get(age_str, ['중장년'])

def persona_age_value(age_str):
    clean = age_str.replace('대', '').replace('이상', '').strip()
    return int(clean) if clean else 75

ADJACENT_LIFE = {'청년': ['중장년'], '중장년': ['청년', '노년'], '노년': ['중장년']}

# 범용 복지 목록 (TOP 3에서 최대 1개 제한)
UNIVERSAL_WELFARES = {
    'K-패스 (대중교통 환급)', 'ISA (개인종합자산관리계좌)',
    '에너지바우처', '문화누리카드', '평생교육바우처',
}

# ============================================================
# 5. 매칭 엔진
# ============================================================
def match_curated(persona_region, age_str, items):
    """benefits-curated.json 매칭"""
    age_val = persona_age_value(age_str)
    results = []
    for item in items:
        ar = item.get('age_range', [])
        if not ar or '전연령' in ar:
            ls_score = 10
        elif len(ar) == 2 and isinstance(ar[0], (int, float)):
            if int(ar[0]) <= age_val <= int(ar[1]):
                span = int(ar[1]) - int(ar[0])
                ls_score = 25 if span <= 20 else (20 if span <= 40 else 15)
            else:
                continue
        else:
            continue
        reg_score = 10
        score = 50 + reg_score + ls_score
        if item.get('amount_annual') and item['amount_annual'] > 0:
            score += 5
        results.append({'item': item, 'score': score, 'type': 'national'})
    return results

def match_local(persona_region, age_str, items):
    """welfare-local.json 매칭"""
    lifestages = get_lifestages(age_str)
    results = []
    for w in items:
        if w['region'] != persona_region:
            continue
        sgg_bonus = 10 if w['sgg'] else 0
        if not w['life_tags']:
            ls_score = 10
        else:
            tag_set, persona_set = set(w['life_tags']), set(lifestages)
            if persona_set & tag_set:
                ls_score = 30
            else:
                found = False
                for ls in lifestages:
                    adj = ADJACENT_LIFE.get(ls, [])
                    if adj and tag_set & set(adj):
                        ls_score, found = 15, True
                        break
                if not found:
                    continue
        aply_bonus = 5 if (w['apply_method'] and '문의' not in w['apply_method']) else 0
        inq_score = min(10, w['inq_num'] / 1000)
        score = 40 + sgg_bonus + ls_score + aply_bonus + inq_score
        if score >= 50:
            results.append({'item': w, 'score': score, 'type': 'local'})
    return results

# ============================================================
# 6. 실행: 204개 페르소나
# ============================================================
VALID_AGE_GROUPS = {'20대', '30대', '40대', '50대', '60대', '70대이상'}
decade_keys = sorted([k for k in stats if k.split('_')[2] in VALID_AGE_GROUPS])

all_results = {}
persona_match_counts = Counter()
welfare_freq = Counter()
persona_local_counts = {}
variety_set = set()

for key in decade_keys:
    region, gender, age_str = key.split('_')

    region_norm = PERSONA_REGION_MAP.get(region, region)
    curated_matches = match_curated(region_norm, age_str, curated)
    local_matches = match_local(region_norm, age_str, local_valid)

    all_matches = curated_matches + local_matches
    all_matches.sort(key=lambda x: -x['score'])

    # TOP 3 선정: 지역 1 + 금액 1 + 나머지 1 (다양성 최대화)
    best_local = None
    best_national_with_amount = None
    best_national_other = None

    for m in all_matches:
        if m['type'] == 'local' and not best_local:
            best_local = m
        elif m['type'] == 'national':
            has_amt = m['item'].get('amount_annual') and m['item']['amount_annual'] > 0
            is_universal = m['item'].get('name', '') in UNIVERSAL_WELFARES
            if has_amt and not is_universal and not best_national_with_amount:
                best_national_with_amount = m
            elif not best_national_other:
                best_national_other = m
        if best_local and best_national_with_amount and best_national_other:
            break

    top_three = []
    if best_local:
        top_three.append(best_local)
    if best_national_with_amount:
        top_three.append(best_national_with_amount)
    elif best_national_other:
        top_three.append(best_national_other)
    if best_local and best_national_with_amount:
        # 3번째: 남은 것 중 최고 점수
        remaining = [m for m in all_matches if m not in top_three]
        if remaining:
            top_three.append(remaining[0])
    elif best_national_other and best_national_other not in top_three:
        top_three.append(best_national_other)

    top_three = top_three[:3]

    # Local Highlights TOP 20
    local_sorted = sorted(local_matches, key=lambda x: (
        1 if x['item']['sgg'] else 0,
        x['score'],
        x['item']['inq_num'],
        x['item']['updated'],
    ), reverse=True)
    local_highlights = local_sorted[:20]

    matched_curated_with_amount = [m for m in curated_matches
                                   if m['item'].get('amount_annual') and m['item']['amount_annual'] > 0]
    total_annual = sum(m['item']['amount_annual'] for m in matched_curated_with_amount)

    top_three_out = []
    for m in top_three:
        item = m['item']
        top_three_out.append({
            'welfare_name': item.get('name', ''),
            'agency': item.get('org', '') or item.get('dept', ''),
            'welfare_id': item.get('id', '') or item.get('servId', ''),
            'type': m['type'],
            'amount_monthly': item.get('amount_monthly'),
            'amount_annual': item.get('amount_annual'),
            'amount_display': item.get('amount_display', ''),
            'amount_notes': item.get('amount_notes', ''),
            'eligibility_summary': item.get('target', '') or item.get('summary', '')[:100],
            'application_method': item.get('method', '') or item.get('apply_method', ''),
            'source_url': item.get('url', '') or item.get('source_url', ''),
            'score': m['score'],
        })

    local_highlights_out = []
    for m in local_highlights:
        w = m['item']
        summary = w['summary'][:100]
        while len(summary.encode('utf-8')) > 100:
            summary = summary[:-1]
        local_highlights_out.append({
            'name': w['name'],
            'sgg': w['sgg'],
            'summary': summary + ('...' if len(w['summary']) > 100 else ''),
            'apply_method': w['apply_method'],
            'dept': w['dept'],
            'support_cycle': w['support_cycle'],
            'url': w['url'],
            'score': m['score'],
        })

    all_results[key] = {
        'personaKey': key,
        'totalMatchedCount': len(all_matches),
        'localMatchedCount': len(local_matches),
        'nationalMatchedCount': len(curated_matches),
        'withAmountCount': len(matched_curated_with_amount),
        'totalEligibleAnnual': total_annual,
        'topThree': top_three_out,
        'localHighlights': local_highlights_out,
        'generatedAt': '2026-06-04T12:00:00Z',
    }

    persona_match_counts[len(all_matches)] += 1
    for m in all_matches:
        if m['type'] == 'national':
            welfare_freq[m['item'].get('name', '')] += 1
    persona_local_counts[key] = len(local_matches)
    combo = '|'.join(f'{c["welfare_name"]}({c["type"]})' for c in top_three_out)
    variety_set.add(combo)

# ============================================================
# 7. 저장
# ============================================================
with open('src/data/decision-cards.json', 'w') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)
print(f'✅ src/data/decision-cards.json 저장 완료 ({len(all_results)}개 페르소나)')

# ============================================================
# 8. 보고
# ============================================================
print('\n' + '='*65)
print('📊 매칭 결과 보고 (welfare-local 통합)')
print('='*65)

valid_local_count = len(local_valid)
has_sgg = sum(1 for w in local_valid if w['sgg'])

print(f'\n1. 정규화 후 매칭 가능 welfare-local 항목: {valid_local_count}건')
print(f'   - sgg(시군구) 정보 보유: {has_sgg}건 ({has_sgg/valid_local_count*100:.0f}%)')

ctpv_dist = Counter(w['region'] for w in local_valid)
print(f'   - 지역별 분포:')
for r, c in sorted(ctpv_dist.most_common()):
    print(f'     {r}: {c}건')

print(f'\n2. 페르소나별 평균 매칭 수:')
avg_total = sum(n * c for n, c in persona_match_counts.items()) / len(decade_keys)
avg_local = sum(persona_local_counts.values()) / len(decade_keys)
print(f'   전체 평균: {avg_total:.1f}건 (전국 {avg_total-avg_local:.1f} + 지역 {avg_local:.1f})')

print(f'\n3. 변별력 측정:')
print(f'   고유 TOP 3 조합 수: {len(variety_set)}개 / {len(decade_keys)}개 페르소나')
print(f'   변별력: {len(variety_set)/len(decade_keys)*100:.1f}%')

print(f'\n4. 매칭 0건 페르소나: {sum(1 for k in decade_keys if persona_local_counts[k] == 0)}개')
low_local = [(k, v) for k, v in persona_local_counts.items() if v <= 2]
print(f'   지역 특화 0~2건: {len(low_local)}개')

print(f'\n5. localHighlights 평균: {sum(persona_local_counts.values())/len(decade_keys):.1f}건')
lt20 = sum(1 for v in persona_local_counts.values() if v < 20)
print(f'   20개 미만 페르소나: {lt20}개')

print(f'\n6. 강원/전남/제주 30대 남자 TOP 3 비교:')
for sk in ['강원_남자_30대', '전남_남자_30대', '제주_남자_30대']:
    d = all_results.get(sk)
    if d:
        print(f'\n   === {sk.split("_")[0]} 30대 남자 ===')
        print(f'   매칭: 전국 {d["nationalMatchedCount"]}건 + 지역 {d["localMatchedCount"]}건')
        for i, c in enumerate(d['topThree']):
            tag = '🏛️' if c['type'] == 'local' else '💰'
            amt = c.get('amount_display', '') or ''
            print(f'   {tag} #{i+1}: {c["welfare_name"]} | {amt}')

print(f'\n7. localHighlights 샘플:')
for sk in ['서울_남자_30대', '제주_여자_70대이상', '강원_여자_60대']:
    d = all_results.get(sk)
    if d:
        print(f'\n   === {sk} (지역 {d["localMatchedCount"]}건) ===')
        for i, h in enumerate(d['localHighlights'][:3]):
            sgg_tag = f' [{h["sgg"]}]' if h['sgg'] else ''
            print(f'   #{i+1}: {h["name"]}{sgg_tag}')
            print(f'       신청: {h["apply_method"]} | 주기: {h["support_cycle"]}')

print(f'\n8. amount_annual 있는 복지 매칭 비율:')
with_amt = sum(1 for k in decade_keys if all_results[k]['withAmountCount'] > 0)
print(f'   {with_amt}/{len(decade_keys)} ({with_amt/len(decade_keys)*100:.0f}%)')
avg_annual = sum(all_results[k]['totalEligibleAnnual'] for k in all_results) / len(decade_keys)
print(f'   평균 연 수령 가능액: {avg_annual/10000:.0f}만원')

print(f'\n{"="*65}')
print('보고 완료')
