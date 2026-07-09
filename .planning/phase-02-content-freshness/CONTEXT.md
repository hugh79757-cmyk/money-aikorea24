# CONTEXT.md — Phase 02: Content Freshness & Data Validation

## Problem Statement
1. 수집된 서비스/상품이 2026년에도 실제 존재하는지 검증 없음 (5,266개 pending 중)
2. 하드코딩된 연도로 outdated 콘텐츠 생성 위험
3. 검증 실패한 서비스가 기록되지 않아 다시 선택될 수 있음

## Scope

### In Scope
1. **URL Alive 검증** — Gov24 `detail_url`로 서비스 존재 여부 직접 확인
2. **관심도 검증** — Finlife/datagokr 등 URL 없는 소스는 네이버 검색으로 확인
3. **검증 실패 기록** — `status_reason` 컬럼 추가로 영구 제외
4. **동적 연도 교체** — 하드코딩 연도 → `datetime.now()` 기반
5. **콘텐츠 연도 검증** — 본문/제목 연도 vs pubDate 비교
6. **리뷰어 연도 체크** — Mimo 리뷰어에게 연도 정확성 검증 지시

### Out of Scope
- 기존 발행된 글 일괄 수정
- 네이버 외 검색 API
- 뉴스/시사 글의 과거 연도 허용 로직

## Decisions

### D1: 검증 2단계 구조
```
pick_next_service()
  ├─ Step A: URL Alive (Gov24) — detail_url HTTP HEAD
  │   ├─ 404/410 → mark_error("url_dead") + skip
  │   ├─ timeout → mark_error("url_unstable") + skip
  │   └─ 200 OK → Step B
  ├─ Step B: 관심도 (Finlife, datagokr, income_series) — 네이버 검색
  │   ├─ 결과 0건 → mark_error("no_search_results") + skip
  │   ├─ stale (1년+) → needs_review=True + 계속
  │   └─ fresh → 통과
  └─ generate_article()
```

### D2: 검증 실패 기록
- `services` 테이블에 `status_reason TEXT` 컬럼 추가
- `mark_error(service_id, reason)`이 reason을 저장
- `status='error'` + `status_reason` 조합으로 영구 제외
- `pick_next_service()`는 `status='pending'`만 선택 → 재선택 없음

### D3: 소스별 검증 방법
| 소스 | 검증 | 근거 |
|------|------|------|
| Gov24 (5,250건) | HTTP HEAD `detail_url` | 공식 서비스 페이지 존재 여부 |
| Finlife (193건) | Finlife API 재조회 | 상품 판매 여부 |
| datagokr (14건) | 네이버 검색 | 주제 관심도 |
| income_series (20건) | 네이버 검색 | 주제 관심도 |

### D4: 연도 검증 기준
- pubDate 연도 ± 1년 허용
- 위반 시 `needs_review=True` (발행은 허용)

### D5: 네이버 API 사용 규칙
- `display=5`, `sort=date`
- 일일 100건 제한
- 키워드: 제목에서 불용어 제거 후 핵심 명사 3개

## Technical Context

### DB 변경
```sql
ALTER TABLE services ADD COLUMN status_reason TEXT;
```

### 신규 모듈
| 파일 | 역할 |
|------|------|
| `shared/url_checker.py` | HTTP HEAD alive 검증 |
| `shared/naver_validator.py` | 네이버 검색 관심도 검증 |
| `shared/year_validator.py` | 본문 연도 검증 |

### 수정 모듈
| 파일 | 변경 |
|------|------|
| `shared/db_utils.py` | status_reason 컬럼 + 마이그레이션 |
| `pipeline.py` | alive 검증 + 관심도 검증 단계 삽입 |
| `writer.py` | 하드코딩 연도 → 동적 |
| `seeder_income.py` | 하드코딩 연도 → 동적 |
| `shared/persona_stats.py` | FOMO hook 동적 |
| `validator.py` | 연도 검증 추가 |
| `manual-publisher/validator.py` | 연도 검증 추가 |
| `shared/reviewer.py` | 프롬프트에 연도 체크 |

## Success Criteria
- [x] Gov24 URL alive 검증 — 404/410 서비스 자동 제외 (`shared/url_checker.py` → `check_gov24_alive`, pipeline.py:48 import)
- [x] 검증 실패 서비스 status_reason에 원인 기록, 재선택 방지 (`db_utils.py` status_reason 컬럼 + mark_error)
- [x] Finlife/datagokr는 네이버 검색으로 관심도 확인 (`shared/naver_validator.py` search_naver_blog/check_topic_relevance)
- [x] 하드코딩 연도 전부 동적 교체 (writer.py / seeder_income.py / persona_stats.py → datetime.now().year)
- [x] 본문 연도 검증 (needs_review=True) (auto-writer + manual-publisher validator year_validator 호출)
- [x] 리뷰어 연도 체크 (reviewer.py 프롬프트 L108)
- [x] Regression 없음 (빌드 통과, 모듈 존재 확인)
