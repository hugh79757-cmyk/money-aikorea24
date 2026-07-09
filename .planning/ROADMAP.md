# Roadmap: money-aikorea24 (persona.aikorea24.kr)

## Milestones

- ✅ **v1.0 Foundation & Monetization** - Phases 1-3 (shipped 2026-07-09)
- 🚧 **v1.1 Community & Cleanup** - Phase 4 (in progress, 2026-07-09 session)

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

### 🚧 v1.1 Community & Cleanup (In Progress)

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

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Security | v1.0 | 5/5 | Complete | 2026-07-01 |
| 2. Content | v1.0 | 11/11 | Complete | 2026-07-09 |
| 3. AdSense | v1.0 | 7/7 | Complete | 2026-07-09 |
| 4. Community | v1.1 | 1/1 | In progress | 2026-07-09 |
