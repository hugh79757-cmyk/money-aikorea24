#!/usr/bin/env python3
"""
Nemotron-Personas-Korea 데이터셋 → public/persona-stats.json 집계
"""
import json
import re
from collections import defaultdict, Counter
from datasets import load_dataset

# ── 매핑 ──────────────────────────────────────────────────────────
PROVINCE_MAP = {
    '경상남': '경남', '경상북': '경북',
    '전라남': '전남', '전라북': '전북',
    '충청남': '충남', '충청북': '충북',
}

VALID_REGIONS = {
    '서울', '경기', '인천', '부산', '대구', '광주', '대전',
    '울산', '세종', '강원', '충북', '충남', '전북', '전남',
    '경북', '경남', '제주',
}

def normalize_province(p):
    return PROVINCE_MAP.get(p, p)

def decade_key(age):
    if age < 20:
        return None
    if age < 30:
        return '20대'
    if age < 40:
        return '30대'
    if age < 50:
        return '40대'
    if age < 60:
        return '50대'
    if age < 70:
        return '60대'
    if age <= 79:
        return '70대이상'
    return None

def extract_name(persona_text):
    """persona 텍스트에서 이름 추출 (예: '전기태 씨는...' → '전기태')"""
    m = re.match(r'^([가-힣]{2,4})\s*(씨|님|군|양|어르신)', persona_text or '')
    if m:
        return m.group(1)
    # fallback: 첫 띄어쓰기 전 토큰
    parts = (persona_text or '').split()
    return parts[0] if parts else ''

def first_paragraph(text):
    """첫 번째 문장 또는 첫 단락 반환"""
    if not text:
        return ''
    # 개행으로 분리
    para = text.strip().split('\n')[0].strip()
    # 200자 제한
    return para[:200]

# ── 집계 구조 ──────────────────────────────────────────────────────
# nested dict: stats[region_gender_age] = {...}
stats = defaultdict(lambda: {
    'total': 0,
    'housing': Counter(),
    'education': Counter(),
    'family': Counter(),
    'jobs': Counter(),
    'marital': Counter(),
    'personas': [],
})

def get_key(region, sex, age):
    """1년 단위 키"""
    return f'{region}_{sex}_{age}'

def get_decade_key(region, sex, age):
    """10년 단위 키"""
    dk = decade_key(age)
    if not dk:
        return None
    return f'{region}_{sex}_{dk}'

# ── 메인 ───────────────────────────────────────────────────────────
print('📡 Nemotron-Personas-Korea 로딩 중...')
ds = load_dataset('nvidia/Nemotron-Personas-Korea', split='train', streaming=True)

total_rows = 0
filtered_rows = 0
region_counts = Counter()

for i, row in enumerate(ds):
    total_rows += 1

    # 조건 필터: 대한민국, province 유효, 나이 20~79
    if row.get('country') != '대한민국':
        continue
    province = normalize_province(row.get('province', ''))
    if province not in VALID_REGIONS:
        continue
    age = row.get('age', 0)
    if not (20 <= age <= 79):
        continue
    sex = row.get('sex', '')
    if sex not in ('남자', '여자'):
        continue

    filtered_rows += 1
    region_counts[province] += 1

    # 1년 단위 키
    year_key = get_key(province, sex, age)
    # 10년 단위 키
    dk = get_decade_key(province, sex, age)
    keys = [year_key]
    if dk:
        keys.append(dk)

    for key in keys:
        s = stats[key]
        s['total'] += 1
        s['housing'][row.get('housing_type', '기타')] += 1
        s['education'][row.get('education_level', '기타')] += 1
        s['family'][row.get('family_type', '기타')] += 1
        s['jobs'][row.get('occupation', '기타')] += 1
        s['marital'][row.get('marital_status', '기타')] += 1

        # personas: 최대 20명 샘플
        if len(s['personas']) < 20:
            persona_text = row.get('persona', '') or ''
            name = extract_name(persona_text)
            story = first_paragraph(persona_text)
            s['personas'].append({
                'name': name,
                'job': row.get('occupation', ''),
                'story': story,
            })

    if (i + 1) % 50000 == 0:
        print(f'  {i+1}행 처리 중... (필터 통과: {filtered_rows})')

print(f'\n📊 처리 완료: 총 {total_rows}행, 필터 통과 {filtered_rows}행')
print(f'지역별 분포: {dict(region_counts.most_common())}')

# ── Counter → dict 및 income 초기화 ───────────────────────────────
output = {}
for key, s in stats.items():
    output[key] = {
        'total': s['total'],
        'housing': dict(s['housing']),
        'education': dict(s['education']),
        'family': dict(s['family']),
        'jobs': dict(s['jobs']),
        'marital': dict(s['marital']),
        'personas': s['personas'],
        'income': {
            'income_sex': '남' if '여자' not in key.split('_')[1] else '여',
            'income_age_bracket': '',
            'income_employed': 0,
            'income_national_avg': 0,
            'income_region_avg': 0,
            'top_percentile': 0,
            'income_estimate': 0,
            'income_source': '',
        },
    }

# ── 저장 ──────────────────────────────────────────────────────────
out_path = 'public/persona-stats.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\n✅ 저장 완료: {out_path}')
print(f'📦 총 키 수: {len(output)}')
print(f'  - 1년 단위 키: {len([k for k in output if not ("대" in k.split("_")[2] or "이상" in k.split("_")[2])])}')
print(f'  - 10년 단위 키: {len([k for k in output if "대" in k.split("_")[2] or "이상" in k.split("_")[2]])}')

# 샘플 출력
print('\n--- 샘플: 서울_남자_30대 ---')
sample = output.get('서울_남자_30대', {})
if sample:
    print(f'  total: {sample["total"]}')
    print(f'  housing: {dict(list(sample["housing"].items())[:5])}')
    print(f'  personas 샘플: {sample["personas"][:2]}')
