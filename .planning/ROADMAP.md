# Roadmap: money-aikorea24 (persona.aikorea24.kr)

## Milestones

- ✅ **v1.0 Foundation & Monetization** - Phases 1-3 (shipped 2026-07-09)
- ✅ **v1.1 Community & Cleanup** - Phases 4-5 (shipped 2026-07-09)
- 🔄 **v2.0 Income Insights** - Phase 6 (planning 2026-07-29)
- 🔄 **v2.1 Marketing Personas** - Phase 7 (planning 2026-08-23)

## Phases

<details>
<summary>✅ v1.0 Foundation & Monetization (Phases 1-3) - SHIPPED 2026-07-09</summary>

### Phase 1: Security & Portability
**Goal**: 크리덴셜 노출 제거, XSS/인가 정비, 이식성(하드코딩 경로/폰트), git 위생
**Plans**: 5 plans (3 waves, multi-subsystem)
**Status**: Complete (2026-07-01, a97ef0a..d8a5565, ab9c05b)

### Phase 2: Content Freshness & Data Validation
**Goal**: 수집 서비스 실존 검증 + 하드코딩 연도 제거 + 검증 실패 영구 제외
**Plans**: 11 tasks (T1-T11)
**Status**: Complete (2026-07-09, verified against code)

### Phase 3: AdSense Revenue Optimization
**Goal**: in-article/leaderboard/mobile-sticky 파셜 + 레이지로드 + RPM 최적화
**Plans**: T1-T7 + 별도 funnel-overhaul
**Status**: Complete with divergences (2026-07-09)

</details>

### ✅ v1.1 Community & Cleanup (Complete)

**Milestone Goal:** 커뮤니티 게시판 수익화 + tax 카테고리 정리 + GSD 문서 실태 정합

#### Phase 4: Community Monetization & Content Cleanup
**Goal**: 커뮤니티 상하단 수동 광고 고정 + tax 카테고리 제거 정리
**Depends on**: Phase 3
**Requirements**: COMM-01, COMM-02, COMM-03, CONT-05, ADS-05
**Success Criteria** (what must be TRUE):
  1. 커뮤니티 상세/목록 페이지 상단·하단에 AdSense 슬롯(9747654190)이 렌더됨
  2. tax 카테고리가 COLLECTIONS/라우팅/내비에서 제거되고 빌드가 0에러
  3. GSD planning 문서(PHASE 2/3 SUMMARY)가 실제 코드 상태와 일치
**Plans**: 1 plan (session-scoped, 2026-07-09)

Plans:
- [x] 04-01: 커뮤니티 상하단 고정 슬롯 추가 + tax 삭제 + GSD 문서 동기화 (빌드 2459p 0에러 확인)

#### Phase 5: Auto-Publishing Rules Audit & Revision
**Goal**: 전반적인 자동 발행 콘텐츠 파이프라인 규칙 점검·정비 + 월급 글 신규 생성 중단
**Depends on**: Phase 4
**Requirements**: AUTO-01..AUTO-07 (see phase-05/CONTEXT.md)
**Status**: Complete (2026-07-09, T1-T7 all verified)
**Success Criteria**:
  1. manual-publisher가 삭제된 `tax` 카테고리를 참조하지 않음
  2. 월급/소득 시리즈 신규 발행 중단 (seeder 가드 + 펜딩 행 차단, 익일 run 이후 신규 invest 월급 0건)
  3. category_quota 합계 = 1.0 (또는 의도 문서화)
  4. filter.py 등 데드코드 정리
  5. 자동 발행 파이프라인 인벤토리 + 규칙 문서 단일화
  6. 빌드 0에러
**Plans**: 7 tasks (T1-T7, see phase-05/PLAN.md)

### ✅ v2.0 Income Insights (Planning)

#### Phase 6: Income Gauge Deep Link & Card Income Integration
**Goal**: persona SSG / my-persona / card images 전반에 income 데이터 연동 완료 + SSG benefit deep link + og:image v2
**Depends on**: Phase 5 (infrastructure)
**Requirements**: INC-01..INC-09 (see phase-06/CONTEXT.md)
**Plans**: 4 work items (A-D, A-1/A-2, B-1/B-2/B-3/C, D)
**Status**: Planning (2026-07-29), see CONTEXT.md + PLAN.md in phase-06/

**Work Items**:
- [ ] A: SSG benefit deep link (`[...slug].astro` + `benefits/index.astro` URL param filter)
- [ ] B-1: Server JPG card income bar (`generate-missing-cards.mjs`)
- [ ] B-2: Mobile card income bar (`generate-mobile-cards.js`)
- [ ] B-3 + C: my-persona canvas overlay + compareWithData income
- [ ] D: og:image URL v2 migration

### 🔄 v2.1 Marketing Personas (Planning)

#### Phase 7: Marketing Persona Studio
**Goal**: 마케팅용 가상 페르소나 생성 — 제품 입력→타깃 페르소나 매칭 시나리오 + 페르소나 선택→소비 프로파일·다음 장면 스토리 (양방향), 공개 페이지 + 가벼운 게이트(카카오 로그인), LLM 실시간 생성
**Depends on**: Phase 6 (benefits URL param filter 등 인프라 재사용)
**Requirements**: MKT-01..MKT-03 + 가정 (see phase-07-marketing-personas/CONTEXT.md)
**Status**: Planning (2026-08-23)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Security | v1.0 | 5/5 | Complete | 2026-07-01 |
| 2. Content | v1.0 | 11/11 | Complete | 2026-07-09 |
| 3. AdSense | v1.0 | 7/7 | Complete | 2026-07-09 |
| 4. Community | v1.1 | 1/1 | Complete | 2026-07-09 |
| 5. Auto-Pub | v1.1 | 7/7 | Complete | 2026-07-09 |
| 6. Income Calc | v2.0 | 0/4 | Planning | — |
| 7. Marketing Personas | v2.1 | 0/? | Planning | — |
