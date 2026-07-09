# PLAN.md — Phase 5: Auto-Publishing Rules Audit & Revision

> 검증 루프: 각 Task 완료 후 성공기준(SC) 체크. 전체 완료 시 자동 커밋.

## Task 1 — 자동 발행 파이프라인 인벤토리 (T1)
- **What**: 모든 launchd 콘텐츠 잡(auto-writer, manual-publisher, blog-draft, news-unified,
  outline-generator, thread-topic-finder, threads-publisher, keyword-updater, wiki-ingest,
  tools-collector, naver-publish, persona-publisher)의 스케줄/출력/활성여부(.bak 구분) 문서화.
- **Why**: "전반적인 자동 발행글 규칙" 범위 파악 선행.
- **How**: `~/Library/LaunchAgents/*.plist` + `scripts/**` 대조 → `.planning/phase-05-auto-publishing-rules/INVENTORY.md` 산출.
- **Verify**: INVENTORY.md에 12개 잡 전부 기재 + 활성/비활성 표시.

## Task 2 — manual-publisher tax 카테고리 잔존 제거 (T2)  [INC-1]
- **What**: `classifier.py` `CATEGORIES`에서 `"tax"` 제거 + `config/category-keywords.json`의 `tax` 섹션 제거.
- **Why**: 이번 세션 tax 카테고리 삭제 후 blog 카테고리는 insurance/invest/loan/general. 분류기가 삭제된 카테고리로 분류 시도 → 오류.
- **How**: 리스트에서 `tax` 항목 삭제, keywords json에서 `tax` 키 삭제. `consts.ts` 카테고리와 일치 확인.
- **Verify**: SC-1 — 코드/설정에 `tax` 분류 참조 0건 (`grep -rn "tax" scripts/manual-publisher/`에서 분류 로직 제외).

## Task 3 — 월급 신규 생성 중단 (T3)  [INC-2, 최우선]
- **What**:
  3a. `seeder_income.py` 가드 — 신규 시드 삽입 차단 (예: `ENABLE_INCOME_SEED` env 플래그 기본 false, 또는 `--allow-income` 명시 필요).
  3b. `auto-writer.db`의 펜딩(`status="pending"`) 월급/income_series `services` 행을 비-pending(예: `blocked`)으로 변경해 auto-writer가 픽업 못 하게.
- **Why**: 사용자 "월급 글만 멈춘다 / 신규생성중단" 요구.
- **How**: 3a는 `generate_seeds()` 초입에 가드 추가. 3b는 `UPDATE services SET status='blocked' WHERE source='income_series' AND status='pending'`.
- **Verify**: SC-2 — 익일 auto-writer run 이후 `publish_ledger` 신규 invest 월급 = 0건 (DB 조회). 가드 후 seeder dry-run 시 0 insert.

## Task 4 — category_quota 정산 (T4)  [INC-3]
- **What**: `category_map.yaml` `category_quota` 합계를 1.0으로 정규화(loan/insurance/invest/general 비중 재조정) 또는 미할당 0.20 의도 명시 문서화.
- **Why**: 합계 0.80 → `pick_next_service` 결핍 균형 드리프트.
- **How**: 비중 재계산 후 yaml 반영. 기존 발행 비중(loan/insurance 우세) 보존 방향.
- **Verify**: SC-3 — quota 합계 = 1.0 또는 문서화 주석. pipeline 동작 회귀 없음.

## Task 5 — 데드코드 정리 (T5)  [INC-4]
- **What**: `manual-publisher/filter.py` 제거 (AGENTS.md 확인 데드코드).
- **Why**: 유지보수 노이즈.
- **How**: 파일 삭제 + import 참조 0건 확인.
- **Verify**: SC-4 — `filter` import 참조 0건, 빌드/발행 정상.

## Task 6 — 규칙 단일화 문서 (T6)  [INC-5]
- **What**: 자동 발행 규칙 요약 문서 1장 작성 (파이프라인별 카테고리/필터/스케줄/가드 현황).
- **Why**: 규칙 산재로 인한 변경 감사 불가 해소.
- **How**: T1/T2/T4 결과 취합 → `docs/auto-publishing-rules.md` 또는 phase-05 산출물.
- **Verify**: SC-5 — 단일 문서 존재, 12개 잡 + 규칙 맵핑 수록.

## Task 7 — 검증 (T7)
- **What**: 전체 변경 후 빌드 + 월급 중단 재확인.
- **Why**: 회귀 방지.
- **How**: `npm run build` (0에러), `publish_ledger` 신규 월급 0건, `grep tax` 분류 참조 0건.
- **Verify**: SC-6 — 빌드 0에러.

## 요구사항 매핑
- AUTO-01 (인벤토리) ← T1
- AUTO-02 (tax 잔존 제거) ← T2 (SC-1)
- AUTO-03 (월급 중단) ← T3 (SC-2)
- AUTO-04 (quota 정산) ← T4 (SC-3)
- AUTO-05 (데드코드) ← T5 (SC-4)
- AUTO-06 (규칙 문서화) ← T6 (SC-5)
- AUTO-07 (빌드 검증) ← T7 (SC-6)
