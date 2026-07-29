# Requirements: money-aikorea24

**Defined:** 2026-07-09
**Core Value:** 사용자가 내 또래 기준으로 금융/지원금 정보를 비교하고 비슷한 처지의 사용자와 경험을 나눈다

## v1 Requirements (shipped — Phases 1-3)

### Platform & Build (Phase 1)
- [x] **PLAT-01**: Astro SSG 빌드 → Cloudflare Pages 정적 배포 (2459p, 0에러)
- [x] **SEC-01**: 소스 내 하드코딩 크리덴셜 제거 (R2/Kakao는 env/Secrets만)
- [x] **SEC-02**: 커뮤니티 API D1 에러 핸들링 + rate limiting
- [x] **GIT-01**: .bak/__pycache__/.ssr-backup 정리, git 위생

### Content Pipeline (Phase 2)
- [x] **CONT-01**: Gov24 URL alive 검증 (404/410 영구 제외, status_reason 기록)
- [x] **CONT-02**: Finlife/datagokr 네이버 관심도 검증
- [x] **CONT-03**: 하드코딩 연도 → datetime.now() 동적 교체
- [x] **CONT-04**: 본문/제목 연도 검증 (needs_review) + 리뷰어 연도 체크

### Monetization (Phase 3)
- [x] **ADS-01**: AdSense 파셜 3종 (in-article/leaderboard/mobile-sticky)
- [x] **ADS-02**: BlogPost/페르소나 본문 광고 + IntersectionObserver 레이지로드
- [x] **ADS-03**: global.css 광고 스타일 + 다크모드 대응
- [x] **ADS-04**: consts.ts ADSENSE_CLIENT 상수 (중앙화 부분 완료)

## v2 / Active Requirements

### Community (current focus)
- [ ] **COMM-01**: 커뮤니티 상세/목록 상하단 수동 광고 슬롯 노출 (9747654190)
- [ ] **COMM-02**: 커뮤니티 인라인 목록 광고 처리 결정 (현재 빈 슬롯 = 미노출)
- [ ] **COMM-03**: 자동광고(Auto Ads) 활성 여부 결정 (현재 OFF)

### Content Hygiene
- [ ] **CONT-05**: tax 카테고리 삭제 잔여 참조 정리 (personaMatcher/benefits 라벨 등 의도 보존)
- [ ] **ADS-05**: AdSense 게시자 ID 12곳 하드코딩 → ADSENSE_CLIENT 중앙화 (파셜 예외 허용)

## v3 / Income Insights (Phase 6)

### Phase 6 Requirements

| ID | Description | File(s) | Effort |
|----|-------------|---------|--------|
| INC-01 | 서버 JPG 카드에 income bar 추가 (기존 4개 bar 유지, additive) | `generate-missing-cards.mjs` | 30min |
| INC-02 | 모바일 카드에 income bar 추가 (465x797 해상도) | `generate-mobile-cards.js` | 15min |
| INC-03 | my-persona 캔버스 다운로드에 income overlay 추가 | `my-persona.astro` | 20min |
| INC-04 | my-persona compareWithData()에 income 비교 로직 추가 (3줄) | `my-persona.astro` | 5min |
| INC-05 | SSG persona 페이지 하단에 benefit deep link 버튼 추가 | `[...slug].astro` | 10min |
| INC-06 | benefits 페이지 URL 파라미터(?income=&age=&region=&sex=) 필터링 | `benefits/index.astro` | 20min |
| INC-07 | og:image URL v=2 마이그레이션 (CDN 캐시 무효화) | `[...slug].astro`, `functions/og/index.js` | 5min |
| INC-08 | 카드 재생성 (2,244장, income bar 포함) | CLI run | 30min |
| INC-09 | 빌드 0에러 + 배포 성공 | — | 10min |

## Out of Scope

| Feature | Reason |
|---------|--------|
| 결제/구독 | AdSense 단일 수익원으로 충분 |
| 실시간 채팅/알림 | 커뮤니티 가치에 필수 아님 |
| 모바일 앱 | 웹 우선, 반응형 커버 |
| tax 카테고리 부활 | 0포스트·데이터소스 없음 (삭제 확정) |
| salary 별도 카테고리 | invest에 발행 중, killer 콘텐츠화 불가 (유지 확정) |
| benefits-clean.json 스키마 개선 | 데이터 구조 건드리지 않음 |
| 소득 게이지 UI 리디자인 | 기존 CSS 유지 |
| income 차트/시각화 신규 개발 | 현 Phase에서는 text overlay만 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLAT-01 | 1 | Complete |
| SEC-01 | 1 | Complete |
| SEC-02 | 1 | Complete |
| GIT-01 | 1 | Complete |
| CONT-01 | 2 | Complete |
| CONT-02 | 2 | Complete |
| CONT-03 | 2 | Complete |
| CONT-04 | 2 | Complete |
| ADS-01 | 3 | Complete |
| ADS-02 | 3 | Complete |
| ADS-03 | 3 | Complete |
| ADS-04 | 3 | Partial |
| COMM-01 | 4 | In Progress |
| COMM-02 | 4 | Pending |
| COMM-03 | 4 | Pending |
| CONT-05 | 4 | Pending |
| ADS-05 | 4 | Pending |
| INC-01 | 6 | Planning |
| INC-02 | 6 | Planning |
| INC-03 | 6 | Planning |
| INC-04 | 6 | Planning |
| INC-05 | 6 | Planning |
| INC-06 | 6 | Planning |
| INC-07 | 6 | Planning |
| INC-08 | 6 | Planning |
| INC-09 | 6 | Planning |

**Coverage:**
- v1 requirements: 12 total (11 Complete, 1 Partial)
- v3 (Phase 6) requirements: 9 total (0 Complete, 9 Planning)
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-09*
*Last updated: 2026-07-29 — Phase 6 requirements added (INC-01 ~ INC-09)*
