# CONTEXT.md — Phase 6: Income Gauge Deep Link & Card Income Integration

> **Phase code**: `income-calculator`  
> **Milestone**: v2.0 Income Insights  
> **Author**: twinsn (2026-07-29)  
> **Status**: Planning Complete (pending execution)

---

## Problem Statement

페르소나 SSG 페이지(`[...slug].astro`)에는 소득 게이지(CSS `<div>` bar)가 렌더링되어 있지만, 이 데이터는 다음과 같은 곳에 **누락**되어 있음:

1. **서버 카드 이미지** (`public/cards/`, `public/cards-mobile/`): 4개 bar(aptP/eduP/marP/uneP)만 있고 `income_employed`/`top_percentile`은 포함되지 않음
2. **클라이언트 캔버스** (`my-persona.astro generateCanvas`): income을 text overlay에 포함하지 않음
3. **소득 비교 섹션** (`my-persona.astro compareWithData`): income 데이터를 추출하지 않음 (3줄 누락)
4. **지원금 페이지 deep link**: "내 소득에 맞는 지원금" 버튼이 있지만 실제 필터링 링크가 없음

이 4개 누락을 채워서 **income 데이터의 ROI를 완결**하는 것이 Phase 6의 목표.

---

## Design Decisions

### D1: 작업 순서 (안전한 증분 수정)
- **B-1 (server JPG) → B-2 (mobile card) → B-3 (client canvas)** — 데이터 의존성 없음, 독립적
- **D (og:image URL v2)** — 완전 독립, B-1 결과가 있으면 이미지 검증 가능
- **A (SSG deep link)** — `[...slug].astro` frontmatter + 수정, D와 독립
- **C (my-persona income)** — `compareWithData()` 3줄 추가, 완전 독립
- 모든 작업이 서로 독립적이므로 **병렬 가능**하나, 빌드 검증은 한 번에

### D2: Income 게이지 재현 (서버 카드)
- `generate-missing-cards.mjs`의 `makeSvgOverlay()`에 income bar 추가
- 기존 4개 bar(aptP/eduP/marP/uneP) 레이아웃과 동일한 스타일 유지
- 데이터: `STATS[key].income.income_employed` (소득액) + `STATS[key].income.top_percentile` (상위 %)
- 기존 4개 bar는 건드리지 않음 (additive 방식)
- 카드 JPG 재생성 필요 (2,244장)

### D3: Income 게이지 재현 (모바일 카드)
- `generate-mobile-cards.js`의 `makeSvg()`에 income bar 추가
- 레이아웃 동일, 모바일 해상도(465x797)에 맞춤
- 데이터 동일

### D4: Income 게이지 재현 (클라이언트 캔버스)
- `my-persona.astro`의 `generateCanvas()`에 income text overlay 추가
- stats 데이터 준비: `s.income`에서 읽어 income_employed + top_percentile 계산
- `compareWithData()`에서 income_employed와 top_percentile 비교 로직 추가 (C 작업)

### D5: SSG benefit deep link
- `[...slug].astro`의 소득 게이지 영역에 "내 소득에 맞는 지원금 보기" 버튼 추가
- 연결 URL 형식: `/benefits?income={incomeVal}&age={age}&region={region}&sex={sex}`
- benefits 페이지가 URL 파라미터를 읽도록 client-side JS 개선 필요
  - `age_range`/`regions` 필드를 기반으로 필터링
  - `target` 필드 텍스트 매칭(income 키워드)으로 보강

### D6: og:image URL v2 마이그레이션
- 현재 `[...slug].astro` og:image URL: `https://cards.persona.aikorea24.kr/{key}.jpg?v=1`
- v=2로 버전 업데이트하여 CDN 캐시 무력화
- 변경 시점: B-1 카드 재생성 직후

### D7: 데이터 확인 — 소득 필드 구조
```json
"income": {
  "income_employed": 4567,    // 만원/월 (또는 연봉)
  "top_percentile": 12.3,     // 상위 %
  "income_estimate": 4500     // 추정치 (폴백)
}
```
- `income_employed`가 **소득액**으로 확인됨
- `top_percentile`이 **퍼센타일**로 확인됨
- 값이 `null`/`undefined`인 경우: 게이지 미표시 또는 "데이터 없음" 처리

---

## Current State

### SSG Income Gauge (`[...slug].astro:602-633`)
- 이미 동작 중: `s.income.income_employed` + `s.top_percentile` 사용
- 순수 CSS `<div>` 게이지 (`style="width:X%"`)
- SSG 전용 (빌드 타임), Chart.js/canvas/SVG 미사용

### my-persona.astro State
- `INPUTS` 객체: 메모리 내 상태, URL `?age=&sex=&province=&marital=` 파라미터로 초기화
- 분석 후 `/persona/{slug}/?marital=`로 redirect (SSG 페이지)
- `compareWithData()` (line 536-561): `d.income.income_employed`와 `d.top_percentile` 접근 **누락**
- `generateCanvas()` (line 861-909): income text overlay **누락**

### Card Generation Scripts
- `scripts/generate-missing-cards.mjs`: `sharp`로 2,244장 JPG 생성
  - `makeSvgOverlay()` (line 95-100): 4개 bar만 렌더링
  - 데스크탑 카드 (800x1200)
- `scripts/generate-mobile-cards.js`: 모바일용 (465x797)
  - `makeSvg()` (line 38-43): 4개 bar만 렌더링
- 두 스크립트 모두 `s.income` 접근 없음

### Benefits Page (`src/pages/benefits/index.astro`)
- 현재 URL 쿼리 파라미터 미지원
- `benefits-clean.json`에 `age_range`, `regions`, `target` 필드 존재
- 510건이 target에서 "소득" 언급
- **필요**: URL 파라미터(`?income=&age=&region=&sex=`)를 읽어 클라이언트 필터링하는 로직 추가

---

## Scope

### In Scope
1. `[...slug].astro`: benefit deep link 버튼 + og:image v2
2. `generate-missing-cards.mjs`: server JPG income bar 추가
3. `generate-mobile-cards.js`: mobile card income bar 추가
4. `my-persona.astro`: `compareWithData()` income 추출 + `generateCanvas()` income overlay
5. `benefits/index.astro`: URL 파라미터 기반 필터링 로직
6. 모든 관련 빌드 + 배포 검증

### Out of Scope
- `benefits-clean.json` 데이터 자체 개선 (income/age 필드 추가 등)
- 소득 게이지 디자인 변경 (기존 CSS 유지)
- my-persona에서 income 차트/시각화 신규 추가
- AdSense 게시자 ID 중앙화 (ADS-05, deferred)
- auto-writer/income 시리즈 복원 (Phase 5에서 중단 확정)

---

## Files to Modify

| File | Type | Change Summary |
|------|------|----------------|
| `src/pages/persona/[...slug].astro` | [PRODUCTION] | Benefit deep link button + og:image v=2 |
| `scripts/generate-missing-cards.mjs` | [PRODUCTION] | Server JPG income bar (makeSvgOverlay) |
| `scripts/generate-mobile-cards.js` | [PRODUCTION] | Mobile card income bar (makeSvg) |
| `src/pages/my-persona.astro` | [PRODUCTION] | compareWithData income + generateCanvas overlay |
| `src/pages/benefits/index.astro` | [PRODUCTION] | URL param client-side filtering |
| `functions/og/index.js` | [PRODUCTION] | og:image URL v2 (cache bust) |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Card regeneration (2,244장) 실패 | Low | High | `--dry-run` 모드로 1장만 먼저 테스트 |
| 카드 JPG에 income bar가 기존 4개와 시각적 불일치 | Medium | Medium | 기존 bar SVG 템플릿 동일하게 복제 |
| benefits 필터가 age_range/regions와 정확히 매칭 안 됨 | Medium | Low | fallback으로 target 텍스트 매칭 |
| 빌드 실패 (2460→error) | Low | High | 작업별 `npm run build` 중간 검증 |
| `s.income` 필드가 일부 persona에 없음 | Medium | Low | null 체크로 방어 |
