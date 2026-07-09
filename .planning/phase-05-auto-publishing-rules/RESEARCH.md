# RESEARCH.md — Phase 5: Auto-Publishing Rules Audit & Revision

> 조사 방식: 코드/설정 직독 (서브에이전트 미사용 — 사용자 "직접 작업" 지시).
> 조사일: 2026-07-09

## 1. 현재 자동 발행 생태계

### A. auto-writer (완전 자동)
- **스케줄**: launchd `com.aikorea24.auto-writer.plist` + `kr.aikorea24.auto-writer.plist` → **매일 09:00**.
- **진입점**: `scripts/auto-writer/scheduler.py` → `pipeline.py:run()`.
- **규칙 설정**: `scripts/auto-writer/config/category_map.yaml`
  - `category_quota`: loan .40 / insurance .25 / invest .10 / general .05 → **합계 0.80** (tax 삭제 후 미정산)
  - `gov24_category_map` / `finlife_category_map` / `datagokr_category_map`
  - `persona_keywords`, `fomo_hooks`, `cta_variants`
- **콘텐츠 필터**: `pipeline.py` `_EXCLUDE_KW` (42개 키워드, 6그룹: 농림/의료/특수직군/중독·법률/고위험/의료비). **월급·연봉·소득 키워드 없음**.
- **시더**: `seeder_income.py:generate_seeds()` — `TOPICS`(region,gender,age) 순회, `services` 테이블에
  `category="invest"`, `source="income_series"`, `status="pending"` 삽입.
  - 중복가드: `service_id = INCOME_{region}_{gender}_{age}` (동일 콤보 1회).
  - launchd **미등록** → 수동 실행. 실행 시마다 새 콤보가 auto-writer에 의해 다음날 발행됨.
  - **= 월급 글의 실제 발행 경로**.
- **DB**: `scripts/auto-writer/db/auto-writer.db` (`services`, `publish_ledger`).
- **검증**: `publish_ledger` 월급/연봉 행 **14건 전부 `category=invest`**, 발행일 2026-06-24~07-09.

### B. manual-publisher (inbox 수동)
- **스케줄**: launchd `com.aikorea24.manual-publisher.plist` → **1800s(30분) polling, RunAtLoad true**.
- **진입점**: `watcher.py` → `publisher.py:run()`.
- **분류기**: `scripts/manual-publisher/classifier.py`
  - `CATEGORIES = ["insurance", "invest", "loan", "tax"]` ⚠️ **삭제된 `tax` 카테고리 잔존**.
  - `config/category-keywords.json` 도 `tax` 섹션 포함 추정.
- **`filter.py`**: AGENTS.md 명시대로 **데드코드** (import만, 호출 안 됨).
- **기록**: `done.json`.

### C. 기타 자동 콘텐츠 launchd 잡 (인벤토리 필요)
`blog-draft`, `news-unified`, `outline-generator`, `thread-topic-finder`, `threads-publisher`,
`keyword-updater`, `wiki-ingest`, `tools-collector`, `naver-publish`, `persona-publisher`
(+ 일부 `.bak` 비활성). 각각 고유 규칙/출력 보유.

## 2. 발견된 불일치 / 이슈

| # | 이슈 | 근거 | 영향 |
|---|------|------|------|
| INC-1 | `manual-publisher/classifier.py`가 삭제된 `tax` 카테고리 참조 | `CATEGORIES` 리스트 + 이번 세션 tax 삭제 | inbox 글을 `tax`로 분류 시도 → 빌드/라우팅 오류 |
| INC-2 | `seeder_income.py`가 월급 글을 무제한 `invest`로 시딩 | `generate_seeds()` 소스, 펜딩 행 확인 | 사용자가 중단 요청한 월급 신규 발행 지속 |
| INC-3 | `category_quota` 합계 0.80 | category_map.yaml | `pick_next_service` 결핍 균형 알고리즘 드리프트 |
| INC-4 | `manual-publisher/filter.py` 데드코드 | AGENTS.md | 유지보수 노이즈 |
| INC-5 | 자동 발행 규칙 단일 출처 부재 | 설정 분산 (yaml/pipeline/classifier/plists) | 변경 감사 불가 |

## 3. 월급 신규 생성 중단 메커니즘 (사용자 최우선 요구)
- 차단 지점 2개:
  1. `seeder_income.py` 가드 (신규 시드 삽입 불가) — 플래그/`ENABLE_INCOME_SEED=false` 또는 스케줄 제거.
  2. 이미 시드됐으나 미발행(`status="pending"`) 월급 `services` 행 차단 (비-pending 상태로 변경).
- 검증: 다음 auto-writer run(익일 09:00) 이후 `publish_ledger` 신규 invest 월급 = 0건.
