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

## Out of Scope

| Feature | Reason |
|---------|--------|
| 결제/구독 | AdSense 단일 수익원으로 충분 |
| 실시간 채팅/알림 | 커뮤니티 가치에 필수 아님 |
| 모바일 앱 | 웹 우선, 반응형 커버 |
| tax 카테고리 부활 | 0포스트·데이터소스 없음 (삭제 확정) |
| salary 별도 카테고리 | invest에 발행 중, killer 콘텐츠화 불가 (유지 확정) |

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

**Coverage:**
- v1 requirements: 12 total (11 Complete, 1 Partial)
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-09*
*Last updated: 2026-07-09 after community ad placement + tax deletion*
