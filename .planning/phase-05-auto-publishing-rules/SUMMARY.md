# SUMMARY.md — Phase 5: Auto-Publishing Rules Audit & Revision

## 한 줄 요약
자동 발행 콘텐츠 파이프라인의 규칙을 점검·정비하고, 월급 글 신규 생성을 중단한다.

## 발견된 핵심 문제 (조사 결과)
- `manual-publisher/classifier.py`가 **삭제된 `tax` 카테고리**를 분류 대상에 잔존 (버그).
- `seeder_income.py`가 월급 글을 무제한 `invest`로 시딩 → auto-writer가 매일 발행 (사용자 중단 요구).
- `category_quota` 합계 0.80 (tax 삭제 후 미정산) → 균형 알고리즘 드리프트.
- `manual-publisher/filter.py` 데드코드.
- 자동 발행 규칙 단일 출처 부재.

## 작업 범위 (7 Task)
1. 자동 발행 파이프라인 12개 인벤토리
2. manual-publisher tax 잔존 제거
3. **월급 신규 생성 중단** (seeder 가드 + DB 펜딩 차단) — 최우선
4. category_quota 정규화(합계 1.0)
5. 데드코드 정리
6. 규칙 단일화 문서
7. 빌드/중단 검증

## 성공 기준 (6개)
- SC-1: tax 분류 참조 0건
- SC-2: 익일 auto-writer run 이후 신규 invest 월급 0건
- SC-3: quota 합계 1.0 또는 의도 문서화
- SC-4: 데드코드 제거
- SC-5: 규칙 문서 단일화 산출물
- SC-6: 빌드 0에러

## 범위 외
- 기존 발행 월급 글(14건) 삭제/하단 — 별도 확인 필요
- AdSense 레이아웃, LLM 프롬프트 품질 — Phase 4 / 별도
