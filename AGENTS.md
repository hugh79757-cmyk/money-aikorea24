# AGENTS.md — 프로젝트 에이전트 가이드

> persona.aikorea24.kr · 한국인 페르소나 통계·지원금·금융 가이드 플랫폼
> 마지막 갱신: 2026-06-23

---

## 기술 스택

| 계층 | 기술 |
|------|------|
| 프레임워크 | Astro 6.1.8 (`output: 'static'`, SSG) |
| 스타일링 | Tailwind CSS v4 |
| 런타임 | Cloudflare Pages Functions |
| DB | Cloudflare D1 (`persona-db`) |
| 인증 | 카카오 OAuth 2.0 + HMAC-SHA256 세션 |
| 빌드 | Vite (Astro 내장) |
| Node | >=22.12.0 |

**중요**: `output: 'static'` — 모든 Astro frontmatter는 **빌드 타임**에 실행됩니다. SSR이 아닙니다.

---

## 핵심 경로

```
src/
  pages/
    index.astro                    # 홈 (블로그 + 지원금 + 페르소나 인덱스 허브)
    my-persona.astro               # 다단계 입력 → 결과 (SPA)
    persona/[...slug].astro        # 페르소나 결과 페이지 (2,891개)
    benefits/index.astro           # 지원금 검색
    blog/index.astro               # 블로그 목록
    blog/[...slug].astro           # 블로그 상세
    blog/category/[category]/      # 카테고리별 블로그
    community/index.astro          # 커뮤니티 목록 (클라이언트 렌더링)
    community/[id].astro           # 게시글 상세
    community/write.astro          # 글쓰기
    auth/login.astro               # 카카오 로그인
    nomad/                         # 디지털 노마드
    about.astro, terms.astro, privacy.astro, ...
  components/
    BaseHead.astro                 # <head> 메타 (OG, GA4, AdSense)
    Header.astro                   # 네비 + session_ui 쿠키 파싱
    Footer.astro
    BenefitCards.astro             # 지원금 매칭 카드
    WelfareCards.astro             # 복지 카드
    DecisionCards.astro            # 적합 지원금 TOP 3
    PersonaBlogRecommend.astro     # 페르소나별 블로그 추천
    FloatingFab.astro, SearchBar.astro, ThemeToggle.astro, ...
  lib/
    benefitMatcher.ts              # 점수 기반 지원금 매칭
    deadlineExtractor.ts           # 마감일 추출
    welfareMatcher.ts              # 페르소나 ↔ 복지 매칭
  data/
    wage-table.json                # 직종별 임금 + 성별·연령 보정계수
    job-category-map.json          # 직업명 → 10개 카테고리 매핑
    decision-cards.json            # 페르소나별 결정 카드 데이터
  content.config.ts                # Zod 스키마 + glob loader
  consts.ts                        # SITE_URL, COLLECTIONS
functions/
  api/_shared/session.js           # HMAC-SHA256 세션 헬퍼
  api/auth/callback/kakao.js       # OAuth 콜백
  api/auth/logout.js               # 로그아웃
  api/community/posts.js           # 게시글 CRUD
  api/community/posts/[id].js      # 게시글 상세
  api/community/comments.js        # 댓글 CRUD
  api/community/like.js            # 좋아요 토글
  api/benefit-click.js             # 혜택 클릭 집계
  community/[id].js                # 커뮤니티 라우트 패스스루
  og/index.js                      # OG → /cards/ 리다이렉트
public/
  persona-stats.json               # 페르소나 통계 (2,891키, ~19MB)
  benefits-clean.json              # 지원금 정제 데이터
  benefits-curated.json            # 큐레이션 혜택 (24건)
  welfare-central.json             # 중앙부처 복지
  welfare-local.json               # 지방 복지
  blog-match.json                  # 블로그-페르소나 매칭
  bg_img/                          # 배경 이미지 (38장)
  cards/                           # 페르소나 카드 JPG
  cards-mobile/                    # 모바일 카드 JPG
  blog-thumbnails/                 # 블로그 OG 이미지
```

---

## 페르소나 페이지

- **URL 형식**: `/persona/{지역}-{성별}-{연령}/`
  - 10년 단위: `/persona/서울-남자-30대/` (색인 대상, 204개)
  - 1년 단위: `/persona/서울-남자-35/` (noindex)
- **슬러그 키**: `서울_남자_32` (언더스코어) → URL은 하이픈
- **라우트 파일**: `src/pages/persona/[...slug].astro`
- **getStaticPaths()**: persona-stats.json의 모든 키에 대해 HTML 생성

---

## 인증 흐름

1. `login.astro`: `crypto.getRandomValues`로 state 생성 → `oauth_state` 쿠키 (Max-Age=600)
2. Kakao OAuth → `callback/kakao.js`: state ↔ 쿠키 검증 (CSRF)
3. HMAC-SHA256 세션 토큰 생성 → `session` 쿠키 (**HttpOnly**, Secure, SameSite=Lax, 7일)
4. UI용 `session_ui` 쿠키 (HttpOnly 아님) — Header.astro에서 닉네임·아바타 표시

---

## 빌드·배포

```bash
npm run dev          # 로컬 개발 (localhost:4321)
npm run build        # ./dist 빌드
npm run deploy       # scripts/deploy.sh (M1 Mac 전용)
```

**Cloudflare Pages 배포**:
```bash
npx wrangler pages deploy dist --project-name money-aikorea24
```
> `--branch` 미지정 시 Production. `--branch production`은 Preview.

---

## 환경변수 (통합 관리)

**폴백 체계**: `.env`(프로젝트 고유) → `~/.env.common`(전역 공통)

```
.env.common (~/)          .env (프로젝트)
  CLOUDFLARE_ACCOUNT_ID     AI_BACKEND=nvidia
  TELEGRAM_BOT_TOKEN        KOSIS_API_KEY=...
  DATA_GO_KR_API_KEY        CF_DNS_TOKEN=...
  R2_ACCESS_KEY_ID          PUBLIC_KAKAO_REST_KEY=...
  ...전역 공통...           ...프로젝트 고유만...
```

- **Python**: `scripts/load_env.py` — `.env` → `.env.common` 순서로 `os.environ`에 주입
  ```python
  from load_env import env
  API_KEY = env("DATA_GO_KR_API_KEY")
  ```
- **Node.js**: `lib/env-loader.ts` — `.env` → `.env.common` 순서로 `process.env`에 주입
  ```typescript
  import './lib/env-loader.js';
  const key = process.env.DATA_GO_KR_API_KEY;
  ```
- **Cloudflare Pages Functions**: 대시보드 Secrets에서 관리 (`.env` 무시)

`.env`에 값이 있으면 `.env.common`보다 **우선 적용**됩니다.

---

## 콘텐츠 시스템

- **컬렉션**: `blog` (보험/투자/대출/세금/일반), `nomad`
- **카테고리**: `insurance` | `invest` | `loan` | `tax` | `general` (consts.ts)
- **스키마**: `title`, `description`, `draft` (기본 true), `pubDate`, `updatedDate`, `heroImage`, `tags`, `category`, `needs_review`
- **자동 발행**: `scripts/persona-publisher/publisher.py` (Python 배치)

---

## 데이터 출처

| 데이터 | 위치 | 출처 |
|--------|------|------|
| 페르소나 통계 | `public/persona-stats.json` | Nemotron + KOSIS |
| 소득 추정 | `income` 객체 + `patch-income.mjs` | 통계청·국세청 |
| 직종 임금 | `src/data/wage-table.json` | 고용노동부 |
| 지원금 | `public/benefits-clean.json` | 공공데이터포털 |
| 복지 | `public/welfare-central.json`, `welfare-local.json` | 보건복지부 등 |

---

## 주의사항

- **static 모드**: frontmatter에서의 fetch는 빌드 타임에만 실행. 새 글 반영은 재배포 필요.
- **세션 쿠키**: `session`은 HttpOnly라 JS에서 읽을 수 없음. UI 상태는 `session_ui` 쿠키 사용.
- **PERSONA_STATS**: `public/`에 있음. `src/data/`가 아님.
- **카드 이미지**: `public/cards/`의 JPG는 Astro가 변환하지 않고 `dist/`로 복사.
- **`.bak` 파일**: `src/pages`, `functions` 등에 백업본 다수 존재.
- **데이터 파일**: `benefits-clean.json`, `persona-stats.json` 등은 git에 없을 수 있음.
