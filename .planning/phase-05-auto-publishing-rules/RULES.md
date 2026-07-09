# 자동 발행 규칙 (AUTO-PUBLISHING RULES) — 단일 진실 원본 (SSoT)

> Phase 5 (2026-07-09) 산출물. 이 문서는 자동 발행 관련 규칙의 유일한 진실 원본이다.
> 다른 문서(AGENTS.md 등)와 충돌하면 이 문서가 우선한다.

## 0. 핵심 원칙

1. **월급/소득 시리즈 신규 생성 중단** (2026-07-09 결정)
   - `seeder_income.py`는 `AUTO_WRITER_INCOME_SEEDS=on` 환경변수가 있어야만 시드 생성.
   - 기본값 `off` → 신규 월급 글 생성되지 않음.
   - DB `services` 테이블의 `source='income_series'` 펜딩 행은 `status='blocked'` 처리됨
     (`status_reason='salary-freeze-phase5'`). auto-writer는 `pending`만 픽업하므로 발행 안 됨.
   - 이미 발행된 14건(`published`)은 그대로 유지.

2. **tax 카테고리 없음**
   - 블로그 카테고리는 `insurance` | `invest` | `loan` | `general` 4종. `tax`는 삭제됨.
   - `classifier.py`의 `CATEGORIES` 및 `category-keywords.json`에 `tax` 섹션 없음.
   - 과거 tax로 분류되던 글(근로장려금/자녀장려금/건강보험료/K-패스/지원금 등)은
     다른 키워드 매칭 또는 `general`(동점/0점)로 분류됨.

## 1. 카테고리 비중 (category_quota)

소유: `scripts/auto-writer/config/category_map.yaml`
사용: `db_utils.pick_next_service()` — `deficit = quota - (published/total_pub)`

```yaml
category_quota:
  loan:      0.40
  insurance: 0.25
  invest:    0.20
  general:   0.15   # 합계 1.00 (반드시 1.0)
```

⚠️ 합계는 **반드시 1.0**이어야 목표 비중이 정확히 반영됨. 미달 시 발행 비중 왜곡.

## 2. 부적합 키워드 필터

소유: `scripts/auto-writer/pipeline.py` (`_EXCLUDE_KW`, 42개 / 6그룹)
대상: **auto-writer(정적 블로그) 전용**. 매칭 시 `mark_error()` + skip.
manual-publisher에는 적용하지 않음(사용자 의도 존중).

## 3. 카테고리 분류 (수동 발행)

소유: `scripts/manual-publisher/classifier.py` + `config/category-keywords.json`
방식: 키워드 점수 기반. 동점/0점 → `general` + `needs_review`.
`filter.py`는 **데드코드**(삭제됨, 2026-07-09). 분류 로직 아님.

## 4. 상태 머신 (services 테이블)

`pending` → `published` / `error` / `updated` / `blocked`(월급 동결용)
- `pick_next_service`: `WHERE status='pending'`
- `get_pending_count`: `WHERE status='pending'`
- `error`는 재시도 대상 아님 (pending만 처리).

## 5. 발행 파이프라인 (12개 활성)

상세 인벤토리: `INVENTORY.md` 참조.
핵심 2개:
- `com.aikorea24.auto-writer` — 매일 09:00, LLM 자동 생성 (DAILY_QUOTA=5)
- `com.aikorea24.manual-publisher` — 30분 polling, inbox/ 수동 발행
