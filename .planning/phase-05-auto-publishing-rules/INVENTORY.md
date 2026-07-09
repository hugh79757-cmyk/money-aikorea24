# Phase 5 — 자동 발행 파이프라인 인벤토리 (INVENTORY)

> 생성: 2026-07-09 · Phase 5.execute T1
> 목적: 자동 발행을 담당하는 launchd 파이프라인 전수 조사 → 규칙 소유권(SSoT) 확정

## 1. 발행 파이프라인 (12개 활성 + 1개 비활성)

| # | LaunchAgent Label | 트리거 | 역할 | 발행 여부 | 비고 |
|---|---|---|---|---|---|
| 1 | `com.aikorea24.auto-writer` | 매일 09:00 | Gov24/finlife/invest → LLM 자동 글생성 | ✅ 자동 | DAILY_QUOTA=5, 월급 시리즈 포함(차단됨) |
| 2 | `com.aikorea24.auto-writer-fetch` | 매일 (수집) | 원천 데이터 수집 | ❌(수집만) | fetch 전용 |
| 3 | `com.aikorea24.manual-publisher` | 30분 polling | inbox/ 수동 글 발행 | ✅ 자동 | 사용자 의도 존중, 필터 없음 |
| 4 | `kr.aikorea24.blog-draft` | 매일 | 블로그 초안 | ✅ | — |
| 5 | `kr.aikorea24.news-unified` | 매일 2회 | 뉴스 통합 | ✅ | — |
| 6 | `kr.aikorea24.outline-generator` | 매일 | 아웃라인 생성 | ✅ | — |
| 7 | `kr.aikorea24.thread-topic-finder` | 매일 | 쓰레드 주제 탐색 | ❌(탐색) | — |
| 8 | `kr.aikorea24.threads-publisher` | interval polling | 쓰레드 발행 | ✅ | — |
| 9 | `kr.aikorea24.keyword-updater` | 매일 | 키워드 갱신 | ❌(갱신) | — |
| 10 | `kr.aikorea24.wiki-ingest` | 매일 | 위키 수집 | ❌(수집) | — |
| 11 | `kr.aikorea24.tools-collector` | 매일 06:00 | 도구 수집 | ❌(수집) | — |
| 12 | `com.aikorea24.naver-publish` | 09:30/14:00/19:30 | 네이버 발행 | ✅ | — |
| — | `kr.aikorea24.persona-publisher.plist.bak.telegram` | — | (비활성) | — | `.bak` 확장 → 비활성 |

## 2. 자동 발행 규칙 소유권 (SSoT)

| 규칙 | 소유 파일 | 비고 |
|---|---|---|
| 카테고리 비중 | `scripts/auto-writer/config/category_map.yaml` (category_quota) | Phase5 T4 정규화 완료 (합계 1.0) |
| 부적합 키워드 | `scripts/auto-writer/pipeline.py` (_EXCLUDE_KW, 42개) | 정적 블로그만 적용 |
| 카테고리 분류(수동) | `scripts/manual-publisher/classifier.py` + `config/category-keywords.json` | Phase5 T2: tax 제거 |
| 월급 시리즈 시드 | `scripts/auto-writer/seeder_income.py` | Phase5 T3: `AUTO_WRITER_INCOME_SEEDS=on` 시에만 |
| 상태머신 | `scripts/auto-writer/shared/db_utils.py` | pending→published/error/updated |

## 3. 발견된 불일치 (Phase 5 해결 대상)

- **INC-1** classifier.py `tax` 카테고리 잔존 → **T2 해결** (category-keywords.json tax 섹션도 제거)
- **INC-2** seeder_income.py가 매월 월급 시리즈 신규 시드 → **T3 해결** (env 게이트 + DB pending 6건 blocked)
- **INC-3** category_quota 합계 0.80 → **T4 해결** (1.0 정규화)
- **INC-4** manual-publisher/filter.py 데드코드 → **T5 해결** (삭제)
- **INC-5** 규칙 산재(문서화 부재) → **T6 해결** (AUTO-PUBLISHING-RULES.md)
