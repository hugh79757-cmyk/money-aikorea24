# PLAN.md — Phase 02: Content Freshness & Data Validation
**Status:** Complete ✅ — all 11 tasks verified against code (2026-07-09). See SUMMARY.md.

## Goal
1. 데이터 소스에서 받아온 서비스/상품이 실제 alive인지 URL 확인
2. 검증 실패한 서비스는 기록하여 다시 선택되지 않도록 방지
3. 과거 연도 하드코딩 교체 + 본문 연도 검증
4. 네이버 검색으로 Finlife/datagokr 등 URL 없는 소스의 관심도 확인

## Tasks

### Task 1: DB 스키마 변경 — `status_reason` 컬럼 추가
**파일**: `scripts/auto-writer/shared/db_utils.py`
**작업**:
- `services` 테이블에 `status_reason TEXT` 컬럼 추가 (ALTER TABLE)
- `mark_error(service_id, reason)` — reason을 `status_reason`에 저장
- `get_conn()`에서 마이그레이션 체크 (컬럼 없으면 ALTER TABLE)

**검증**: DB 연결 시 `status_reason` 컬럼 존재 확인

### Task 2: url_checker.py 신규 생성 — URL Alive 검증
**파일**: `scripts/auto-writer/shared/url_checker.py`
**작업**:
- `check_url_alive(url, timeout=10)` — HTTP HEAD 요청으로 alive 확인
  - 200 OK → `{"alive": True}`
  - 404/410 → `{"alive": False, "reason": "not_found"}`
  - 3xx 리다이렉트 → 최종 URL 확인 후 alive 판단
  - timeout/연결 실패 → `{"alive": None, "reason": "timeout"}`
  - SSL 에러 → `{"alive": None, "reason": "ssl_error"}`
- `check_gov24_alive(service_id, detail_url)` — Gov24 URL 검증 + mark_error 처리
  -_alive=False → `mark_error(service_id, "url_dead")` + return False
  - alive=None → `mark_error(service_id, "url_unstable")` + return False (스킵)
  - alive=True → return True

**검증**: 실제 gov.kr URL로 alive 테스트

### Task 3: naver_validator.py 신규 생성 — 관심도 검증
**파일**: `scripts/auto-writer/shared/naver_validator.py`
**작업**:
- `search_naver_blog(query)` — 네이버 블로그 검색 API (최신순 5건)
- `check_topic_relevance(title, summary)` — 키워드 추출 → 검색 → 결과 분석
  - 결과 0건 → `{"relevance": "none"}`
  - 결과 있지만 최신 글 1년 이상 → `{"relevance": "stale"}`
  - 최신 글 있음 → `{"relevance": "fresh"}`
- `extract_keywords(title, summary)` — 불용어 제거 후 핵심 키워드 3개
- 환경변수: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`

**검증**: 단위 테스트

### Task 4: year_validator.py 신규 생성 — 연도 검증
**파일**: `scripts/auto-writer/shared/year_validator.py`
**작업**:
- `extract_years(text)` — 정규식 `r'(20\d{2})년'`으로 연도 추출
- `check_year_freshness(pub_date, body, title="")` — pubDate vs 본문 연도 (±1년)
- `get_current_year()` — `datetime.now().year`

**검증**: 단위 테스트

### Task 5: writer.py 하드코딩 연도 동적 교체
**파일**: `scripts/auto-writer/writer.py`
**작업**:
- Line 83: `"현재(2026년 6월)"` → `f"�제({datetime.now().year}년 {datetime.now().month}월)"`
- Line 148: `"2026년 6월 기준, 국세청"` → 동적
- 상단에 `from datetime import datetime` 추가

### Task 6: seeder_income.py 하드코딩 연도 교체
**파일**: `scripts/auto-writer/seeder_income.py`
**작업**:
- Line 71: `f"[2026]"` → `f"[{datetime.now().year}]"`
- Line 86: 폴백 `"2024"` → `str(datetime.now().year - 1)`

### Task 7: persona_stats.py FOMO hook 동적 교체
**파일**: `scripts/auto-writer/shared/persona_stats.py`
**작업**:
- Line 154: `"통계청 2024"` → 동적 연도

### Task 8: pipeline.py에 alive 검증 + 관심도 검증 단계 추가
**파일**: `scripts/auto-writer/pipeline.py`
**작업**:
- `pick_next_service()` 후 `generate_article()` 전에 2단계 검증 삽입

```
pick_next_service()
  │
  ├─ Step A: URL Alive 검증 (Gov24만)
  │   ├─ detail_url 없음 → Step B로 이동
  │   ├─ alive=True → Step B로 이동
  │   └─ alive=False/None → mark_error("url_dead"/"url_unstable") + skip
  │
  ├─ Step B: 관심도 검증 (Finlife, datagokr, income_series)
  │   ├─ relevance=none → mark_error("no_search_results") + skip
  │   ├─ relevance=stale → needs_review=True + 계속
  │   └─ relevance=fresh → 통과
  │
  └─ Step C: generate_article()
```

**API 한도**: 네이버 일일 100건 제한 (env `NAVER_DAILY_LIMIT=100`)

### Task 9: auto-writer validator.py에 연도 검증 추가
**파일**: `scripts/auto-writer/validator.py`
**작업**:
- `validate_and_fix()`에 `year_validator.check_year_freshness()` 호출
- 과거 연도 감지 시 `issues` 리스트에 `"STALE_YEAR:{year}"` 추가 + `needs_review=True`

### Task 10: manual-publisher validator.py에 연도 검증 추가
**파일**: `scripts/manual-publisher/validator.py`
**작업**:
- `validate_and_fix_content()`에 year_validator import + 호출
- 과거 연도 감지 시 `needs_review=True`

### Task 11: reviewer.py 리뷰어 프롬프트에 연도 체크 추가
**파일**: `scripts/auto-writer/shared/reviewer.py`
**작업**:
- 리뷰어 시스템 프롬프트에 연도 정확성 검증 항목 추가

## Dependencies
- Task 1 → Task 2, 8 (DB 스키마 먼저)
- Task 2, 3, 4 → Task 8 (모듈 먼저)
- Task 5~7는 독립적

## Estimated Effort
- Task 1: 10분 (DB 마이그레이션)
- Task 2: 20분 (URL alive 검증)
- Task 3: 20분 (네이버 검색 검증)
- Task 4: 10분 (연도 검증)
- Task 5~7: 각 5분 (하드코딩 교체)
- Task 8: 20분 (파이프라인 통합)
- Task 9~11: 각 5분 (검증 로직)
- **총: ~115분**

## 검증 실패 시 기록 규칙
| 소스 | 검증 방법 | 실패 시 처리 |
|------|-----------|-------------|
| Gov24 | HTTP HEAD `detail_url` | `mark_error("url_dead")` — 영구 제외 |
| Finlife | Finlife API 재조회 | `mark_error("product_discontinued")` — 영구 제외 |
| datagokr | Naver 검색 | `mark_error("no_search_results")` — 영구 제외 |
| income_series | Naver 검색 | `mark_error("no_search_results")` — 영구 제외 |

**영구 제외**: `status='error'` + `status_reason`에 원인 기록. `pick_next_service()`는 `status='pending'`만 선택하므로 재선택 없음.

## Verification
1. DB: `status_reason` 컬럼 존재 확인
2. URL 검증: `python3 -c "from shared.url_checker import check_url_alive; print(check_url_alive('https://www.gov.kr'))"` → alive=True
3. 연도 검증: `python3 -c "from shared.year_validator import check_year_freshness; print(check_year_freshness('2026-07-04', '2025년 정보'))"` → (False, [2025])
4. pipeline dry-run: alive 검증 + 관심도 검증 동작 확인
5. manual-publisher: 연도 검증 동작 확인
