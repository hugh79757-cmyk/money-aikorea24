# money-aikorea24 (persona.aikorea24.kr)

## What This Is

한국인 페르소나(지역·성별·연령) 기반 금융·지원금·통계 가이드 플랫폼. Astro SSG로 빌드해 Cloudflare Pages에 정적 배포하고, D1 + Kakao OAuth로 커뮤니티(게시판)를 운영한다. AdSense 수익화가 핵심.

## Core Value

사용자가 "내 또래" 기준으로 지원금·대출·보험·투자 정보를 한눈에 비교하고, 비슷한 처지의 실제 사용자들과 경험을 나눌 수 있어야 한다.

## Business Context

- **Customer**: 한국 2030/4050 금융·복지 관심 층 (유입은 SEO/오가닉)
- **Revenue model**: Google AdSense (수동 고정 슬롯 + 자동광고 로더)
- **Success metric**: 페이지뷰 × RPM (AdSense 수익), 유기적 검색 순위
- **Strategy notes**: 콘텐츠는 auto-writer(LLM 자동) + manual-publisher(수동 인박스) 2개 파이프라인으로 매일 발행

## Requirements

### Validated

- ✓ Astro SSG 빌드 → Cloudflare Pages 배포 (2459 pages, 0 errors) — Phase 1+
- ✓ 페르소나 통계 페이지 2,244개 (지역-성별-연령) 정적 생성 — core
- ✓ 블로그 (보험/투자/대출/일반) + 카테고리 라우팅 — core
- ✓ 지원금 검색 (benefits) + 페르소나 매칭 — core
- ✓ 커뮤니티 게시판: 글 CRUD·댓글·좋아요 (D1 + Kakao OAuth 세션) — core
- ✓ AdSense 수동 슬롯(블로그/페르소나/마이페르소나/혜택) + 자동광고 로더 — Phase 3
- ✓ 콘텐츠 신선도 파이프라인 (URL alive·관심도·연도 검증) — Phase 2
- ✓ 보안/이식성 정리 (크리덴셜 노출 제거, git 위생) — Phase 1

### Active

- [ ] 커뮤니티 게시판 상하단 수동 광고 슬롯 안정화 (슬롯 9747654190)
- [ ] tax 카테고리 삭제 후 잔여 참조/데이터소스 정리
- [ ] AdSense 게시자 ID 중앙화 (consts.ts ADSENSE_CLIENT로 12곳 하드코딩 수렴) — Phase 3 잔여

### Out of Scope

- 결제/구독 모델 — AdSense 단일 수익원으로 충분
- 실시간 채팅/알림 — 커뮤니티 가치에 필수 아님
- 모바일 앱 — 웹 우선, 반응형으로 커버
- tax 카테고리 부활 — 0포스트·데이터소스 매핑 없음 (사용자 확정 삭제)
- salary 별도 카테고리 — invest에 발행 중, killer 콘텐츠화 불가 (유지 확정)

## Context

- SSG(static) 모드: 모든 Astro frontmatter는 빌드 타임 실행. 새 글/글로벌 변경은 재배포 필요.
- 콘텐츠 2 파이프라인(auto-writer LLM / manual-publisher 인박스)이 launchd로 매일/30분 실행, 발행 시 자동 build+deploy.
- auto-writer는 Gov24/finlife/datagokr 소스; 부적합 키워드 42개 필터; 카테고리 가중치(loan .40 / insurance .25 / invest .10 / general .05, tax 삭제됨).
- 14건의 "월급/소득" 포스트는 invest 카테고리에 발행(별도 salary 카테고리 없음, 사용자 확정).
- 배포: deploy.sh → build → git push → wrangler pages deploy. Cloudflare Secrets(KAKAO_*, SESSION_SECRET) 필수.
- 25MiB persona-stats.json은 Cloudflare 제한으로 dist에서 제거 후 배포(decade 서브셋 4MiB만 런타임 사용).

## Constraints

- **Tech stack**: Astro 6.1.8 SSG + Tailwind v4 + Cloudflare Pages Functions + D1 + Kakao OAuth. 변경 시 빌드/배포 체인 재검증 필요.
- **빌드 시간**: 2459페이지 ≈ 80s. 대규모 변경 시 사전 빌드 검증 필수.
- **AdSense 정책**: 페이지당 광고 밀도 과다 금지. 상하단 고정 + 자동광고 혼용 주의(현재 자동광고는 enable_page_level_ads 미활성으로 사실상 수동만 동작).
- **보안**: 크리덴셜은 Cloudflare Pages Secrets / env만. 소스 하드코딩 금지(Phase 1로 정리).
- **콘텐츠 필터**: manual-publisher에는 컨텐츠 필터 추가 금지(사용자 의도 발행 존중).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| tax 카테고리 삭제 | 0포스트·데이터소스 매핑 없음 | ✓ Good (빌드 2460→2459, 정리됨) |
| salary 포스트는 invest 카테고리 유지 | 별도 killer 콘텐츠화 불가, 발행 집중 | ✓ Good (사용자 확정) |
| 커뮤니티 광고 수동 고정(자동광고 OFF) | 광고 밀도 제어·정책 안전 | — Pending (검증 필요) |
| 동일 슬롯 9747654190 상하단 재사용 | 빠른 배포, 추후 별도 단위 발급 가능 | ⚠️ Revisit (같은 크리에이티브 반복) |

---
*Last updated: 2026-07-09 after community ad placement + tax deletion + GSD doc reconciliation*
