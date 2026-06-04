#!/usr/bin/env python3
"""Stage 0A: benefits-curated.json에 amount_display 등 금액 컬럼 추가"""
import json

with open('public/benefits-curated.json', 'r') as f:
    data = json.load(f)

# 10개 대상 복지 금액 데이터 (2025년 공식 기준)
amount_data = {
    'curated_eitc': {
        'amount_monthly': None,
        'amount_annual': 1650000,
        'amount_min_annual': 1650000,
        'amount_max_annual': 3300000,
        'amount_display': '연 165만원 ~ 330만원 (가구 유형별)',
        'amount_notes': '단독가구 최대 165만원, 홑벌이 285만원, 맞벌이 330만원',
        'amount_source_url': 'https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml',
        'amount_verified_date': '2025-03-01',
        'amount_year': 2025,
    },
    'curated_child_tax_credit': {
        'amount_monthly': None,
        'amount_annual': 1000000,
        'amount_min_annual': 500000,
        'amount_max_annual': 1000000,
        'amount_display': '자녀 1인당 연 최대 100만원',
        'amount_notes': '부양자녀(만 18세 미만) 1인당 최대 100만원. 소득·재산 기준 충족 시',
        'amount_source_url': 'https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml',
        'amount_verified_date': '2025-03-01',
        'amount_year': 2025,
    },
    'curated_youth_monthly_rent': {
        'amount_monthly': 200000,
        'amount_annual': 2400000,
        'amount_min_monthly': 50000,
        'amount_max_monthly': 200000,
        'amount_display': '월 최대 20만원 (최대 12개월)',
        'amount_notes': '월세 60만원 이하, 월 최대 20만원, 최대 12개월 지원. 소득·재산 기준 있음',
        'amount_source_url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00005590',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_kpass': {
        'amount_monthly': 20000,
        'amount_annual': 240000,
        'amount_min_monthly': 5000,
        'amount_max_monthly': 50000,
        'amount_display': '월 평균 2만원 환급',
        'amount_notes': '월 15회 이상 대중교통 이용 시 지출액의 20~53% 환급. 청년(19~34세) 30% 추가 할인',
        'amount_source_url': 'https://www.kpass.go.kr',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_tomorrow_learning': {
        'amount_monthly': None,
        'amount_annual': 1000000,
        'amount_min_annual': 300000,
        'amount_max_annual': 5000000,
        'amount_display': '연 최대 100만원 (5년 누적 500만원)',
        'amount_notes': '5년간 최대 500만원(직업능력개발훈련). 일부 과정은 최대 300만원',
        'amount_source_url': 'https://www.hrd.go.kr',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_youth_leap': {
        'amount_monthly': None,
        'amount_annual': None,
        'amount_min_monthly': None,
        'amount_max_monthly': None,
        'amount_display': '5년 만기 최대 5,000만원 (저축상품)',
        'amount_notes': '월 70만원 한도 납입 시 정부기여금 월 최대 6만원 + 비과세 혜택. 만기 시 기여금+운용수익 수령',
        'amount_source_url': 'https://www.kinfa.or.kr',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_parenting_pay': {
        'amount_monthly': 1000000,
        'amount_annual': 12000000,
        'amount_min_monthly': 500000,
        'amount_max_monthly': 1000000,
        'amount_display': '0세 월 100만원, 1세 월 50만원',
        'amount_notes': '만 0세 월 100만원, 만 1세 월 50만원 지급',
        'amount_source_url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00007654',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_child_allowance': {
        'amount_monthly': 100000,
        'amount_annual': 1200000,
        'amount_min_monthly': 100000,
        'amount_max_monthly': 100000,
        'amount_display': '월 10만원 (만 8세 미만)',
        'amount_notes': '아동 1인당 월 10만원. 만 8세 미만 아동 대상. 소득·재산 무관',
        'amount_source_url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00007570',
        'amount_verified_date': '2025-01-01',
        'amount_year': 2025,
    },
    'curated_basic_pension': {
        'amount_monthly': 334810,
        'amount_annual': 4017720,
        'amount_min_monthly': 100000,
        'amount_max_monthly': 334810,
        'amount_display': '월 33.48만원 (2026년, 단독가구 기준)',
        'amount_notes': '만 65세 이상, 소득인정액 하위 70% 이하. 단독가구 최대 월 334,810원(2026년 기준). 소득·재산에 따라 차등',
        'amount_source_url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00005593',
        'amount_verified_date': '2026-01-01',
        'amount_year': 2026,
    },
}

# 주거급여 신규 항목
housing_entry = {
    'id': 'curated_housing_support',
    'name': '주거급여',
    'purpose': '저소득 가구의 주거비 부담 완화 및 주거 수준 향상',
    'target': '소득인정액 기준 중위소득 48% 이하 가구',
    'content': '임차가구: 지역·가구원수별 기준임대료 상한 내 월세 지원. 자가가구: 수선유지급여(경보수 457만원, 중보수 849만원, 대보수 1,241만원)',
    'type': '현금',
    'method': '주민센터 방문 또는 복지로(bokjiro.go.kr)',
    'deadline': '상시신청',
    'url': 'https://www.bokjiro.go.kr',
    'org': '국토교통부',
    'updated': '2025-01-01',
    'category': 'housing',
    'age_range': ['전연령'],
    'regions': ['전국'],
    'amount_monthly': 391000,
    'amount_annual': 4692000,
    'amount_min_monthly': 150000,
    'amount_max_monthly': 650000,
    'amount_display': '월 35~54만원 (가구·지역별, 2025년 기준)',
    'amount_notes': '서울 1인가구 기준임대료 월 391,000원. 지역·가구원수·소득에 따라 차등 지급',
    'amount_source_url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00003201',
    'amount_verified_date': '2025-01-01',
    'amount_year': 2025,
}

# --- 실행 ---
target_ids = set(amount_data.keys())
target_names = []

for item in data:
    if item['id'] in target_ids:
        amt = amount_data[item['id']]
        item.update(amt)
        target_names.append(item['name'])
        print(f'  ✅ {item["name"]:20s} → {amt.get("amount_display","null")}')

# 주거급여 추가 (중복 방지)
if not any('주거급여' in item.get('name', '') for item in data):
    data.append(housing_entry)
    target_names.append('주거급여')
    print(f'  ✅ 주거급여(신규)            → {housing_entry["amount_display"]}')
else:
    print('  ⏭️  주거급여 이미 존재')

# 저장
with open('public/benefits-curated.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\n📊 결과: {len(target_names)}/10개 대상 업데이트 완료')
print(f'📦 최종 파일: {len(data)}개 항목')

# JSON 유효성 검증
with open('public/benefits-curated.json', 'r') as f:
    json.load(f)
print('✅ JSON 유효성 검증 통과')
