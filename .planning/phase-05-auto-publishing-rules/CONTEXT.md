# CONTEXT.md — Phase 5: Auto-Publishing Rules Audit & Revision

## Goal
전반적인 자동 발행 콘텐츠 파이프라인(auto-writer, manual-publisher, 기타 launchd 잡)의
**규칙을 점검·정비**하고, 사용자 최우선 요구인 **월급 글 신규 생성 중단**을 실행한다.
규칙을 단일 출처로 정리해 향후 변경을 감사 가능하게 만든다.

## Scope
**IN (포함)**:
- auto-writer 규칙 설정 (`category_map.yaml`, `pipeline.py` `_EXCLUDE_KW`, `seeder_income.py`)
- manual-publisher 규칙 (`classifier.py`, `filter.py`, `config/category-keywords.json`)
- auto-writer DB 펜딩 행 차단 (월급)
- 기타 자동 콘텐츠 launchd 잡 인벤토리 + 규칙 문서화
- 규칙 단일화 문서 작성

**OUT (제외)**:
- 블로그 프론트엔드/UI 변경
- AdSense 슬롯 레이아웃 (Phase 4 영역)
- auto-writer LLM 모델/프롬프트 품질 튜닝
- 이미 발행된 기존 월급 글(14건) 사이트 하단/삭제 — 별도 작업(사용자 확인 필요)

## Success Criteria (반드시 참이어야 할 것)
1. `manual-publisher/classifier.py` 및 `config/category-keywords.json`에 **삭제된 `tax` 카테고리 참조가 없음** (blog 카테고리 = insurance/invest/loan/general 일치).
2. **월급/소득 시리즈 신규 발행 중단** — `seeder_income.py` 가드 + 펜딩 월급 `services` 행 차단. 익일 auto-writer run 이후 `publish_ledger` 신규 invest 월급 = **0건**.
3. `category_quota` 합계 = **1.0** (또는 미할당 의도를 명시적으로 문서화).
4. `manual-publisher/filter.py` 등 **데드코드 정리** 완료.
5. **자동 발행 파이프라인 인벤토리 + 규칙 문서** 단일화 산출물 존재.
6. 변경 후 `npm run build` 0에러.

## Constraints
- 정적 사이트(빌드타임) — 런타임 변경 불가, 설정/스크립트만 수정.
- 기존 발행 콘텐츠(월급 14건 외)는 건드리지 않음.
- 서브에이전트 미사용 — 직접 작업.
- 완료 시 GSD `auto_commit_on_complete` 규칙에 따라 자동 커밋.
