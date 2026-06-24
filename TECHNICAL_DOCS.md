# 페르소나 (persona.aikorea24.kr) — 기술 문서

> 최종 업데이트: 2026-06-23

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [아키텍처](#3-아키텍처)
4. [디렉토리 구조](#4-디렉토리-구조)
5. [핵심 데이터 파이프라인](#5-핵심-데이터-파이프라인)
6. [페르소나 통계 및 소득 추정 로직](#6-페르소나-통계-및-소득-추정-로직)
7. [인증 시스템 (카카오 OAuth)](#7-인증-시스템-카카오-oauth)
8. [커뮤니티 API](#8-커뮤니티-api)
9. [지원금 페이지](#9-지원금-페이지)
10. [보안 구조](#10-보안-구조)
11. [환경변수 및 배포](#11-환경변수-및-배포)
12. [주요 스크립트](#12-주요-스크립트)
13. [오늘 작업 내역 (2026-05-26)](#13-오늘-작업-내역-2026-05-26)
14. [보안 감사 결과 (2026-06-23)](#14-보안-감사-결과-2026-06-23)
15. [블로그 콘텐츠 분석 (2026-06-23)](#15-블로그-콘텐츠-분석-2026-06-23)
16. [Gov24 공공데이터 API 분석 (2026-06-23)](#16-gov24-공공데이터-api-분석-2026-06-23)
17. [페르소나 진단 페이지 구조 (2026-06-23)](#17-페르소나-진단-페이지-구조-2026-06-23)
18. [썸네일 생성 로직 (2026-06-23)](#18-썸네일-생성-로직-2026-06-23)
19. [자동 글쓰기 파이프라인 준비도 (2026-06-23)](#19-자동-글쓰기-파이프라인-준비도-2026-06-23)

---

## 1. 프로젝트 개요

**페르소나**는 통계청 인구·주거 데이터를 기반으로 "내 또래 한국인은 어떻게 사는가"를 시각화하는 서비스입니다.

- **도메인**: `persona.aikorea24.kr`
- **주요 기능**:
  - 지역·성별·나이 기반 페르소나 페이지 (~2,891개 조합)
  - 정부 지원금·복지 혜택 검색 (2,590건+)
  - 카카오 로그인 기반 커뮤니티 게시판
  - 금융 블로그 (보험·투자·대출·세금·노마드)
- **데이터 출처**: 통계청 인구총조사, 고용노동부 고용형태별근로실태조사, 국세청 근로소득 분포

---

## 2. 기술 스택

| 레이어 | 기술 | 역할 |
|--------|------|------|
| **프론트엔드** | Astro 6.x (static output) | SSG, MDX 블로그, 페르소나 페이지 |
| **스타일** | Tailwind CSS 4 + 인라인 CSS | 글로벌/컴포넌트 스타일 |
| **런타임 API** | Cloudflare Pages Functions | OAuth 콜백, 커뮤니티 CRUD |
| **데이터베이스** | Cloudflare D1 (SQLite) | 사용자, 게시글, 댓글, 좋아요 |
| **호스팅** | Cloudflare Pages | 정적 파일 + Function 라우팅 |
| **인증** | 카카오 OAuth 2.0 + HMAC-SHA256 세션 | 소셜 로그인 |
| **빌드 도구** | Vite (Astro 내장) | 번들링 |
| **Node** | >=22.12.0 | 빌드 환경 |

```
package.json 주요 의존성:
- astro ^6.1.8
- @astrojs/cloudflare ^13.5.2  (Cloudflare Pages 어댑터)
- @astrojs/mdx ^5.0.3          (MDX 블로그)
- @astrojs/sitemap ^3.7.2      (사이트맵 자동 생성)
- @astrojs/rss ^4.0.18         (RSS 피드)
- @tailwindcss/vite ^4.3.0     (Tailwind CSS)
- sharp ^0.34.3                 (이미지 최적화)
```

---

## 3. 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    브라우저 (사용자)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│               Cloudflare Pages (CDN + Edge)                  │
│                                                              │
│  ┌─────────────────────┐   ┌─────────────────────────────┐  │
│  │  정적 파일 (dist/)   │   │  Pages Functions (/api/*)   │  │
│  │  - 페르소나 페이지   │   │  - /api/auth/callback/kakao │  │
│  │  - 블로그 MDX        │   │  - /api/auth/logout         │  │
│  │  - 지원금 페이지     │   │  - /api/community/posts     │  │
│  │  - 커뮤니티 셸       │   │  - /api/community/comments  │  │
│  └─────────────────────┘   │  - /api/community/like      │  │
│                             └──────────────┬────────────────┘  │
│                                            │                  │
│                             ┌──────────────▼────────────────┐  │
│                             │   Cloudflare D1 (SQLite)      │  │
│                             │   - users                     │  │
│                             │   - persona_posts             │  │
│                             │   - persona_comments          │  │
│                             │   - persona_likes             │  │
│                             └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

외부 API:
- kauth.kakao.com  → OAuth 토큰 교환
- kapi.kakao.com   → 카카오 사용자 정보
```

### 라우팅 방식

- **정적 페이지** (`output: 'static'`): 빌드 시 HTML 생성
  - `/persona/[region]-[sex]-[age]/` → `getStaticPaths()` 로 2,891개 생성
  - `/community/[id]/` → 셸 1개 생성 후 클라이언트 JS로 데이터 로드
- **동적 API**: `functions/api/**/*.js` → Cloudflare Pages Functions (Workers 런타임)

---

## 4. 디렉토리 구조

```
money-aikorea24/
├── src/
│   ├── pages/                 # Astro 페이지 (SSG)
│   │   ├── index.astro        # 홈 (블로그 최신 + 마감임박 지원금)
│   │   ├── persona/
│   │   │   └── [...slug].astro  # 페르소나 상세 페이지 (지역-성별-나이)
│   │   ├── community/
│   │   │   ├── index.astro    # 커뮤니티 목록 (클라이언트 렌더링)
│   │   │   ├── [id].astro     # 게시글 상세 (클라이언트 렌더링)
│   │   │   └── write.astro    # 글쓰기
│   │   ├── benefits/
│   │   │   └── index.astro    # 정부 지원금 검색 (2,590건)
│   │   ├── auth/
│   │   │   └── login.astro    # 카카오 로그인 페이지
│   │   ├── blog/              # 금융 블로그
│   │   │   ├── index.astro
│   │   │   ├── [...slug].astro
│   │   │   └── category/[category]/index.astro
│   │   ├── nomad/             # 디지털 노마드
│   │   │   ├── index.astro
│   │   │   └── [...slug].astro
│   │   ├── data.astro         # 데이터 소개 페이지
│   │   ├── data/
│   │   │   └── nemotron-korea.astro  # Nemotron 데이터 페이지
│   │   ├── contact.astro      # 문의
│   │   ├── about.astro        # 소개
│   │   ├── disclaimer.astro   # 면책 조항
│   │   ├── privacy.astro      # 개인정보처리방침
│   │   ├── terms.astro        # 이용약관
│   │   └── rss.xml.js         # RSS 피드
│   │
│   ├── content/               # MDX 블로그 콘텐츠
│   │   ├── blog/              # 금융 일반 (보험·투자 등)
│   │   └── nomad/             # 노마드·해외 콘텐츠
│   │
│   ├── components/            # Astro 컴포넌트
│   │   ├── BaseHead.astro     # <head> 메타 (OG, 구조화 데이터)
│   │   ├── Header.astro       # 사이트 헤더
│   │   ├── Footer.astro       # 사이트 푸터
│   │   ├── BenefitCards.astro # 지원금 카드 컴포넌트
│   │   ├── WelfareCards.astro # 복지 카드 컴포넌트
│   │   ├── DecisionCards.astro    # 적합 지원금 결정 카드
│   │   ├── PersonaBlogRecommend.astro # 페르소나별 블로그 추천
│   │   ├── FloatingFab.astro  # 플로팅 FAB 버튼
│   │   ├── SearchBar.astro    # 검색 바
│   │   ├── ThemeToggle.astro  # 다크모드 토글
│   │   ├── AiTip.astro        # AI 팁 컴포넌트
│   │   ├── JsonLd.astro       # JSON-LD 구조화 데이터
│   │   ├── Disclaimer.astro   # 면책 조항
│   │   ├── HeaderLink.astro   # 헤더 링크
│   │   ├── FormattedDate.astro # 날짜 포맷
│   │   └── ui/                # 공용 UI 컴포넌트
│   │       ├── Badge.astro
│   │       ├── Card.astro
│   │       └── Button.astro
│   │
│   └── data/
│       ├── wage-table.json       # 임금 기준표 (직종·성별·연령·지역)
│       ├── job-category-map.json # 직업명 → 카테고리 매핑
│       └── decision-cards.json   # 페르소나별 결정 카드 데이터
│
├── functions/                 # Cloudflare Pages Functions
│   ├── api/
│   │   ├── _shared/
│   │   │   └── session.js     # HMAC-SHA256 세션 헬퍼 ★
│   │   ├── auth/
│   │   │   ├── callback/
│   │   │   │   └── kakao.js   # OAuth 콜백 처리 ★
│   │   │   └── logout.js      # 로그아웃 (쿠키 삭제)
│   │   ├── community/
│   │   │   ├── posts.js       # 게시글 CRUD (목록/작성/삭제) ★
│   │   │   ├── posts/
│   │   │   │   └── [id].js    # 게시글 상세 + 조회수
│   │   │   ├── comments.js    # 댓글 CRUD ★
│   │   │   └── like.js        # 좋아요 토글 ★
│   │   └── benefit-click.js   # 혜택 클릭 집계
│   ├── community/
│   │   └── [id].js            # 커뮤니티 라우트 패스스루 핸들러
│   └── og/
│       └── index.js           # OG → /cards/ 302 리다이렉트
│
├── public/
│   ├── persona-stats.json     # 페르소나 통계 데이터 (2,891개 조합)
│   ├── benefits-clean.json    # 지원금 데이터
│   ├── benefits-curated.json  # 큐레이션 지원금
│   ├── welfare-central.json   # 중앙부처 복지 데이터
│   ├── welfare-local.json     # 지방 복지 데이터
│   ├── blog-match.json        # 블로그-페르소나 매칭
│   ├── bg_img/                # 배경 이미지 (38장)
│   ├── blog-thumbnails/       # 블로그 OG 이미지
│   ├── cards/                 # 페르소나 카드 이미지 (데스크탑)
│   └── cards-mobile/          # 페르소나 카드 이미지 (모바일)
│
├── scripts/                   # 데이터 생성·관리 스크립트
│   ├── patch-income.mjs       # 소득 데이터 재계산
│   ├── deploy.sh              # 배포 스크립트 (M1 전용)
│   ├── generate-seed-posts.mjs # 커뮤니티 시드 게시글
│   ├── generate-missing-cards.mjs # 누락 카드 생성
│   ├── generate-mobile-cards.js   # 모바일 카드 생성
│   ├── card-prompts.mjs       # 카드 AI 프롬프트 출력
│   ├── curate-card-prompts.mjs # 큐레이션 카드 프롬프트
│   ├── vs-card-prompts.mjs    # VS 비교 카드 프롬프트
│   ├── vs-compare.mjs         # VS 비교 스크립트
│   ├── fetch_benefits.py      # 정부 지원금 데이터 수집
│   ├── fetch_welfare.mjs      # 복지 데이터 수집
│   ├── build_persona_stats.py # 페르소나 통계 빌드
│   ├── stage0a_add_amounts.py # 결정 카드 Stage 0A
│   ├── stage1_build_cards.py  # 결정 카드 Stage 1
│   ├── gen_thumbnails.py      # 썸네일 생성
│   ├── generate_post.py       # 포스트 생성
│   ├── topics.json            # 토픽 데이터
│   └── persona-publisher/     # 블로그 자동 발행 파이프라인 (Python)
│
├── wrangler.toml              # Cloudflare D1 바인딩 설정
├── astro.config.mjs           # Astro 설정
└── package.json
```

★ = 오늘(2026-05-26) 신규 생성 또는 주요 변경

---

## 5. 핵심 데이터 파이프라인

### 5-1. 페르소나 통계 (persona-stats.json)

**출처**: 통계청 인구주택총조사 마이크로데이터  
**조합**: 지역(16) × 성별(2) × 연령(~90세) = 최대 2,880+ 개  
**키 형식**: `"서울_남자_32"`, `"경기_여자_30대"` (1년 단위 + 10년 단위)

```json
"서울_남자_32": {
  "total": 128420,
  "housing": { "아파트": 89000, ... },
  "education": { "4년제 대학교": 55000, ... },
  "family": { "배우자·자녀와 거주": 40000, ... },
  "jobs": { "소프트웨어 개발자": 3200, ... },
  "marital": { "배우자있음": 65000, "미혼": 50000, ... },
  "personas": ["홍길동 씨는 서울...", ...],  // AI 생성 페르소나 텍스트 20개
  "income": {
    "income_employed":    362,   // 취업자 중위 월소득 (만원)
    "income_estimate":    362,   // income_employed와 동일
    "income_age_bracket": "30대초",
    "income_sex":         "남",
    "income_region_avg":  362,
    "income_national_avg": 315,  // 전국 동 성별·연령 중위값
    "income_source": "통계청·국세청 근로소득 분포 2024 성별×연령 중위값 × 지역보정",
    "income_year": 2024,
    "top_percentile": 37.5       // 전체 취업자 중 상위 %
  }
}
```

### 5-2. 지원금 데이터 (benefits-clean.json)

**수집 스크립트**: `scripts/fetch_benefits.py`  
**처리 결과**: 2,590건 (만료 제외)  
**필드**: `name`, `org`, `deadline`, `url`

---

## 6. 페르소나 통계 및 소득 추정 로직

### 6-1. 소득 추정 공식

**참조 파일**: `src/data/wage-table.json`, `scripts/patch-income.mjs`

#### income_employed (취업자 추정 월소득)

```
income_employed = medianBase[성별][연령대] × regionFactor[지역]
```

| 구성 요소 | 설명 | 출처 |
|-----------|------|------|
| `medianBase` | 성별×연령별 전국 취업자 중위 월소득 (만원) | 통계청·국세청 2022-2024 추정 |
| `regionFactor` | 지역별 임금 보정계수 (서울=1.15, 전남=0.88 등) | 고용노동부 2024 |

**예시** — 서울 남자 32세:
```
medianBase["남"]["30대초"] = 315만원
regionFactor["서울"]       = 1.15
income_employed            = 315 × 1.15 = 362만원
```

**medianBase 기준값 (만원)**

| 연령대 | 남 | 여 |
|--------|-----|-----|
| 10대 | 95 | 78 |
| 20대초 | 190 | 162 |
| 20대후 | 255 | 218 |
| 30대초 | 315 | 218 |
| 30대후 | 351 | 232 |
| 40대초 | 370 | 212 |
| 40대후 | 385 | 198 |
| 50대초 | 360 | 178 |
| 50대후 | 328 | 158 |
| 60대이상 | 218 | 128 |

**regionFactor**

| 지역 | 계수 | 지역 | 계수 |
|------|------|------|------|
| 서울 | 1.15 | 울산 | 1.08 |
| 경기 | 1.05 | 부산 | 1.00 |
| 인천 | 1.02 | 대전 | 0.98 |
| 세종 | 1.02 | 대구 | 0.97 |
| 광주 | 0.95 | 강원 | 0.92 |
| 전남·제주 | 0.88 | 충북 | 0.93 |

#### top_percentile (전체 취업자 상위 %)

로그정규분포 가정 (2024년 전국 취업자 기준):

```
GLOBAL_MED = 288만원  (전국 취업자 중위 월소득, 2024 국세청)
SIG        = 0.72     (로그 표준편차)

z = (ln(income) - ln(288)) / 0.72
top_percentile = (1 - Φ(z)) × 100
```

**예시** — 서울 남자 32세 (362만원):
```
z = (ln(362) - ln(288)) / 0.72 = 0.316
Φ(0.316) ≈ 0.624
top_percentile = (1 - 0.624) × 100 = 37.5%
→ "전체 취업자 중 상위 37.5%"
```

> **설계 의도**: 기존에는 지역보정계수를 직접 percentile로 사용해 서울 거주자가 모두 동일한 percentile이 나오는 버그가 있었음. 로그정규분포 기반으로 전환해 소득 수준별 차별화된 percentile 산출.

### 6-2. 직종별 임금 추정 (페르소나 페이지 내)

**참조 파일**: `src/pages/persona/[...slug].astro` → `getJobWage()` 함수

```
직종 임금 = jobCategory[직종대분류] × ageSexFactor[성별][연령대] × regionFactor[지역]
```

**jobCategory 기준값 (만원, 고용노동부 2025 고용형태별근로실태조사)**

| 직종 | 평균 월급 |
|------|-----------|
| 관리자 | 1,090 |
| 전문가 | 457 |
| 사무종사자 | 436 |
| 판매종사자 | 372 |
| 기능원 | 371 |
| 장치기계조작 | 366 |
| 농림어업숙련 | 297 |
| 단순노무 | 251 |
| 서비스종사자 | 218 |
| 무직 | 0 |

---

## 7. 인증 시스템 (카카오 OAuth)

### 7-1. 전체 흐름

```
[사용자] → /auth/login
  1. 약관 동의 체크 (필수 3개 + 선택 1개)
  2. 랜덤 state 생성 (crypto.getRandomValues, 16 bytes)
  3. oauth_state 쿠키 저장 (Max-Age=600, Secure, SameSite=Lax)
  4. oauth_next 쿠키 저장 (돌아갈 URL, 상대경로 검증)
  5. pending_marketing 쿠키 저장
  6. Kakao OAuth 페이지로 리다이렉트 (state 포함)

[카카오 서버] → /api/auth/callback/kakao
  1. state 파라미터 검증 (oauth_state 쿠키와 비교)
  2. code → 토큰 교환 (kauth.kakao.com)
  3. 사용자 정보 조회 (kapi.kakao.com)
  4. D1 users 테이블 조회 또는 생성
     - 신규: 랜덤 닉네임 부여 (지역+동물+숫자 4자리)
  5. HMAC-SHA256 세션 토큰 생성
  6. HttpOnly 세션 쿠키 설정 (Max-Age=7일)
  7. 임시 쿠키 3개 삭제
  8. oauth_next 경로로 리다이렉트
```

### 7-2. 세션 토큰 구조

**파일**: `functions/api/_shared/session.js`

```
토큰 = base64url(payload) + "." + base64url(HMAC-SHA256(data, SESSION_SECRET))

payload = {
  id:     <D1 user.id>,
  name:   <닉네임>,
  email:  <이메일>,
  avatar: <카카오 프로필 이미지 URL>
}
```

**특징**:
- Web Crypto API (`crypto.subtle`) — Cloudflare Workers 환경 네이티브
- 타이밍 공격 방어: `timingSafeEqual()` XOR 비교
- 서버에 세션 저장 없음 (stateless, HMAC 서명으로 위조 방지)
- 쿠키: `HttpOnly; Secure; SameSite=Lax; Max-Age=604800`

### 7-3. 주요 보안 설계

| 위협 | 방어 방법 |
|------|-----------|
| CSRF (OAuth state 위조) | 서버에서 state 파라미터 ↔ oauth_state 쿠키 일치 확인 |
| 세션 위조 | HMAC-SHA256 서명 + 타이밍 안전 비교 |
| Open Redirect | next URL을 상대경로 `(/로 시작, //로 미시작)`만 허용 |
| XSS로 세션 탈취 | HttpOnly 쿠키 → JS 접근 불가 |
| 클라이언트 세션 파싱 | payload 부분만 추출 (UI 전용), 실제 인증은 서버에서 |

### 7-4. 닉네임 자동 생성 로직

```javascript
regions = ['서울','부산','대구','인천','광주','대전','울산','경기','강원',...,'제주']
animals = ['냥이','멍이','토끼','사슴','여우','곰돌','판다','너구리','다람쥐','햄찌','펭귄']
nickname = `${랜덤지역}${랜덤동물}${1000-9999}`
// 중복 시 최대 5회 재시도
```

---

## 8. 커뮤니티 API

### 8-1. 엔드포인트 일람

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/community/posts?page=&board=&slug=&q=` | 게시글 목록 | 불필요 |
| GET | `/api/community/posts/{id}` | 게시글 단건 조회 | 불필요 |
| POST | `/api/community/posts` | 게시글 작성 | 필요 |
| DELETE | `/api/community/posts?id=` | 게시글 삭제 | 필요 (본인/관리자) |
| GET | `/api/community/comments?post_id=` | 댓글 목록 | 불필요 |
| POST | `/api/community/comments` | 댓글 작성 | 필요 |
| DELETE | `/api/community/comments?id=` | 댓글 삭제 | 필요 (본인/관리자) |
| POST | `/api/community/like` | 좋아요 토글 | 필요 |

### 8-2. 입력 제한

| 필드 | 최대 길이 |
|------|-----------|
| 게시글 제목 | 100자 |
| 게시글 본문 | 5,000자 |
| 댓글 | 2,000자 |

### 8-3. D1 스키마 (주요 테이블)

```sql
-- 사용자
CREATE TABLE users (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  kakao_id         TEXT UNIQUE,
  email            TEXT,
  name             TEXT,        -- 카카오 실명
  nickname         TEXT UNIQUE, -- 서비스 닉네임 (자동생성)
  avatar           TEXT,        -- 카카오 프로필 이미지 URL
  provider         TEXT DEFAULT 'kakao',
  marketing_consent INTEGER DEFAULT 0,
  agreed_at        TEXT,        -- 약관 동의 시각 (ISO 8601)
  created_at       TEXT DEFAULT (datetime('now'))
);

-- 게시글
CREATE TABLE persona_posts (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id      INTEGER NOT NULL,
  persona_slug TEXT,            -- 연결 페르소나 (서울-남자-32 등)
  persona_type TEXT,            -- 페르소나 유형
  region       TEXT,
  sex          TEXT,
  age          TEXT,
  title        TEXT NOT NULL,
  content      TEXT NOT NULL,
  board_type   TEXT DEFAULT 'persona',  -- 'persona' | 'benefit'
  views        INTEGER DEFAULT 0,
  likes        INTEGER DEFAULT 0,
  created_at   TEXT DEFAULT (datetime('now'))
);

-- 댓글
CREATE TABLE persona_comments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id    INTEGER NOT NULL,
  user_id    INTEGER NOT NULL,
  content    TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- 좋아요
CREATE TABLE persona_likes (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  UNIQUE(post_id, user_id)
);
```

### 8-4. 관리자 설정

`env.ADMIN_USER_IDS` 환경변수 (콤마 구분): 해당 ID의 사용자는 모든 게시글·댓글 삭제 가능.

```bash
# Cloudflare Pages 대시보드 또는 wrangler로 설정
npx wrangler pages secret put ADMIN_USER_IDS
# 예: "1,5,12"
```

---

## 9. 지원금 페이지

**파일**: `src/pages/benefits/index.astro`  
**데이터**: `public/benefits-clean.json` (2,590건)

### 9-1. 상태 분류 로직

```javascript
마감일 파싱: YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD 포맷 지원

status 분류:
  '상시|연중|수시' 포함     → 'always'
  '신청불필요|불필요' 포함  → 'auto'
  daysLeft < 0             → 'expired'  (목록에서 제외)
  daysLeft <= 7            → 'urgent'   (빨간 배지)
  daysLeft <= 30           → 'soon'     (주황 배지)
  daysLeft > 30            → 'upcoming' (노란 배지)
  파싱 불가                → 'unknown'  (별도공고)
```

### 9-2. 탭 구성 (빌드 시점 기준)

| 탭 | 설명 | 색상 |
|----|------|------|
| 📋 전체 | 만료 제외 전체 | — |
| ⏰ 마감임박 | D-30 이내 | 빨강·주황 |
| 📅 예정 | D-30 초과 | 노랑 |
| ✅ 상시신청 | 상시·자동 | 초록 |
| 📌 별도공고 | 날짜 불명 | 회색 |

### 9-3. 클라이언트 기능

- **검색**: 이름·기관명 부분 일치
- **페이지네이션**: 50건씩 무한로드 (더 보기 버튼)
- **탭 전환**: 클라이언트 JS로 즉시 필터링 (서버 요청 없음)

---

## 10. 보안 구조

### 10-1. XSS 방어

모든 사용자 입력 데이터를 `innerHTML`에 삽입할 때 반드시 이스케이프:

```javascript
function escapeHtml(s) {
  return String(s||'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;');
}
```

**적용 위치**:
- `community/index.astro`: `p.title`, `p.author_name`, `p.region`, `p.age`, `p.sex`, `p.persona_type`
- `community/[id].astro`: `c.author_name`, `c.content` (댓글 목록)

### 10-2. Astro 스크립트 전역 함수 주의사항

Astro는 `<script>` 태그를 ES Module로 번들링하므로, `onclick="funcName()"` 인라인 핸들러에서 호출할 함수는 반드시 `window.funcName = function` 형태로 전역 등록 필요.

```javascript
// ❌ 잘못된 방법 (모듈 스코프에만 존재)
async function loadPosts(page) { ... }

// ✅ 올바른 방법 (window에 등록)
window.loadPosts = async function loadPosts(page) { ... }
```

### 10-3. 보안 체크리스트

- [x] OAuth CSRF state 검증
- [x] HMAC-SHA256 세션 서명
- [x] HttpOnly 세션 쿠키
- [x] Open Redirect 방어 (상대경로만 허용)
- [x] XSS 방어 (innerHTML 이스케이프)
- [x] SQL Injection 방어 (D1 prepared statements)
- [x] 입력 길이 제한
- [x] 타이밍 공격 방어 세션 비교
- [x] 위험 엔드포인트 삭제 (unauthenticated account creation)
- [ ] Rate Limiting (Cloudflare 레이어 활용 권장)
- [ ] 개인정보처리방침 국제 이전 조항 보강

---

## 11. 환경변수 및 배포

### 11-1. 환경변수 폴백 체계

**폴백 체계**: `.env`(프로젝트 고유) → `~/.env.common`(전역 공통)

```
.env.common (~/)          .env (프로젝트)
  CLOUDFLARE_ACCOUNT_ID     AI_BACKEND=nvidia
  TELEGRAM_BOT_TOKEN        KOSIS_API_KEY=...
  DATA_GO_KR_API_KEY        CF_DNS_TOKEN=...
  R2_ACCESS_KEY_ID          PUBLIC_KAKAO_REST_KEY=...
  ...전역 공통...           ...프로젝트 고유만...
```

| 환경 | 로더 | 사용법 |
|------|------|--------|
| **Python** | `scripts/load_env.py` | `from load_env import env; env("KEY")` |
| **Node.js** | `lib/env-loader.ts` | `import './lib/env-loader.js'` |
| **Cloudflare Functions** | 대시보드 Secrets | `.env` 무시, 대시보드 관리 |

`.env`에 값이 있으면 `.env.common`보다 **우선 적용**됩니다.

### 11-2. 환경변수 목록

| 변수명 | 위치 | 필수 | 설명 |
|--------|------|------|------|
| `SESSION_SECRET` | Cloudflare Pages Secret | **필수** | HMAC 서명 키 (최소 32자 랜덤) |
| `KAKAO_REST_KEY` | Cloudflare Pages Secret | 권장 | 카카오 REST API 키 (미설정 시 하드코딩 fallback) |
| `KAKAO_CLIENT_SECRET` | Cloudflare Pages Secret | 선택 | 카카오 Client Secret |
| `ADMIN_USER_IDS` | Cloudflare Pages Secret | 선택 | 관리자 D1 user.id 목록 (콤마 구분) |
| `PUBLIC_KAKAO_REST_KEY` | `.env` | 선택 | 프론트엔드용 (빌드 시 주입) |

### 11-3. Wrangler 설정

```toml
# wrangler.toml
name = "money-aikorea24"
compatibility_date = "2024-12-01"
pages_build_output_dir = "./dist"

[[d1_databases]]
binding = "DB"
database_name = "persona-db"
database_id = "476a89e1-4e2b-4b45-a2f8-e195127e5d32"
```

### 11-4. 배포 절차

```bash
# 1. 빌드
npm run build

# 2. 커밋 & 푸시
git add -A && git commit -m "..."
git push origin main

# 3. Cloudflare Pages 배포 (자동: GitHub 연동)
#    또는 수동:
npx wrangler pages deploy dist \
  --project-name money-aikorea24 \
  --branch main

# ⚠️ deploy.sh는 M1 Mac 전용 (M4에서 차단됨)
```

### 11-5. 환경변수 초기 설정 (신규 배포 시)

```bash
# SESSION_SECRET 설정 (필수)
npx wrangler pages secret put SESSION_SECRET
# → 32자 이상 랜덤 문자열 입력 (예: openssl rand -hex 32)

# 카카오 키 설정 (선택)
npx wrangler pages secret put KAKAO_REST_KEY
npx wrangler pages secret put KAKAO_CLIENT_SECRET

# 관리자 ID 설정
npx wrangler pages secret put ADMIN_USER_IDS
```

---

## 12. 주요 스크립트

### patch-income.mjs

소득 데이터를 중위값 기반으로 재계산해 `public/persona-stats.json`에 반영.

```bash
node scripts/patch-income.mjs
```

**변경 내용**:
- `income_employed` = `medianBase × regionFactor`
- `top_percentile` = 로그정규분포 기반 전체 취업자 상위 %
- `income_estimate` = `income_employed`와 동일화

### generate-seed-posts.mjs

커뮤니티 초기 게시글 100개 생성 (AI 페르소나 기반 자동 작성).

```bash
node scripts/generate-seed-posts.mjs
```

### deploy.sh

M1 Mac 전용 통합 배포 스크립트 (빌드 → git push → wrangler 배포).

```bash
npm run deploy
# 또는
bash scripts/deploy.sh
```

---

## 13. 오늘 작업 내역 (2026-05-26)

### 커밋 로그

```
19a7e14  fix: 커뮤니티 페이지네이션 버튼 클릭 안되는 버그 수정
4223f0a  security: 카카오 로그인 및 커뮤니티 전면 보안 강화
54eee73  fix: 소득 보정 중위값 기반 + 지원금 페이지 전체 목록 표시
```

---

### 1. 소득 추정 로직 전면 개선 (`54eee73`)

**문제**: 32세 서울 남자의 추정 소득이 524만원으로 비현실적으로 높게 표시됨.

**원인 분석**:
- 기존 로직이 고용노동부 **평균** 임금(398.8만원)에 성별·연령 보정계수를 곱해 사용
- 실제 한국 근로자 소득은 우편향 분포 → 평균이 중위값보다 훨씬 높음
- 상위 percentile도 지역보정계수를 직접 사용해 서울 거주자가 모두 동일 percentile 출력

**해결**:

| 항목 | 이전 | 이후 |
|------|------|------|
| 기준값 | 전국 평균 398.8만원 | 성별×연령 **중위값** (medianBase) |
| 지역 보정 | ageSexFactor × (지역계수 없음) | medianBase × **regionFactor** |
| percentile | 지역계수 직접 사용 (오류) | **로그정규분포** (전국 중위 288만원, σ=0.72) |
| 결과 (서울 남자 32) | 524만원, 상위 13% | **362만원, 상위 37.5%** |

**변경 파일**:
- `src/data/wage-table.json` — `medianBase`, `regionFactor` 테이블 추가
- `scripts/patch-income.mjs` — v3 재작성 (중위값 × 지역계수)
- `public/persona-stats.json` — 2,891개 레코드 전체 갱신
- `src/pages/persona/[...slug].astro` — KPI 소득 카드 제거, 직종 임금에 지역계수 적용

---

### 2. 지원금 페이지 전면 개편 (`54eee73`)

**문제**: "지원금 마감 임박" 탭에 2건만 표시됨.

**원인**: 기존 필터 `b._d !== null && b._d > 0`가 상시신청·별도공고 항목을 모두 제외.

**해결**: 상태를 5단계로 분류 후 만료 항목만 제거.

| 상태 | 조건 | 건수 |
|------|------|------|
| urgent | D-7 이내 | 2건 |
| soon | D-30 이내 | 0건 |
| upcoming | D-30 초과 | 1건 |
| always/auto | 상시 | 1,535건 |
| unknown | 별도공고 | 1,052건 |
| **합계** | | **2,590건** |

---

### 3. 카카오 로그인 보안 전면 강화 (`4223f0a`)

발견된 취약점과 조치:

| 취약점 | 파일 | 조치 |
|--------|------|------|
| 인증 없이 임의 계정 생성 | `kakao-session.js` | **파일 삭제** |
| base64 단순 디코딩 세션 (위조 가능) | `posts.js`, `comments.js`, `like.js` | HMAC-SHA256 검증으로 교체 |
| OAuth state 없음 (CSRF 취약) | `login.astro` | `crypto.getRandomValues()` state 생성 |
| state 검증 누락 | `callback/kakao.js` | 쿠키↔파라미터 state 일치 검증 |
| Open Redirect | `callback/kakao.js` | 상대경로 외 거부 |
| 세션 쿠키 HttpOnly 미적용 | `callback/kakao.js` | HttpOnly 추가 |
| XSS (innerHTML에 날 데이터) | `community/index.astro`, `community/[id].astro` | `escapeHtml()` 전면 적용 |

**신규 생성 파일**:
- `functions/api/_shared/session.js` — HMAC-SHA256 세션 헬퍼 (3개 API에서 공유)

---

### 4. 커뮤니티 페이지네이션 버그 수정 (`19a7e14`)

**문제**: 페이지네이션 버튼 (1, 2, 3, 다음 →) 클릭 시 아무 반응 없음.

**원인**: Astro가 `<script>`를 ES Module로 번들링 → `async function loadPosts()`가 모듈 스코프에 갇혀 인라인 `onclick="loadPosts(N)"` 핸들러에서 호출 불가.

**해결**: `window.loadPosts = async function loadPosts(page)` 로 전역 등록.

```javascript
// Before (모듈 스코프에만 존재)
async function loadPosts(page = 1) { ... }

// After (전역 등록)
window.loadPosts = async function loadPosts(page = 1) { ... }
```

---

## 20. 블로그 자동 발행 파이프라인 — Persona Publisher

### 20.1 개요

`scripts/persona-publisher/` 디렉터리의 Python 배치 파이프라인.  
외부 Blogsmith 시스템이 `inbox/`에 `.md` 파일을 넣으면 감지 → 분류 → 변환 → 썸네일 생성 → 빌드 → Cloudflare Pages 배포까지 자동화.

| 단계 | 모듈 | 작업 |
|------|------|------|
| 1 | `watcher.py` | `inbox/` 신규 MD 감지, `done.json` 상태 관리 |
| 2 | `classifier.py` | 본문 키워드 스코어링 → category 분류 |
| 3 | `transformer.py` | frontmatter 정리, slug 생성, `heroImage` 경로 설정 |
| 3.5 | `validator.py` | **frontmatter 타입 검증 + auto-fix** (2026-06-08 추가) |
| 4 | `thumbnail.py` | 1024×1024 OG 썸네일 생성 + **R2 업로드** |
| 5 | `entity_injector.py` | 내부 관련 글 링크 삽입 |
| 6 | 복사 | `src/content/blog/{slug}.md` |
| 7 | `deployer.py` | `npm run build` → `wrangler pages deploy --branch main` (Production) |

**실행**: `scripts/persona-publisher/.venv/bin/python publisher.py`  
**1회 실행**: 최대 **1개** 파일만 처리 (`new_files[:1]`)

---

### 20.2 아키텍처 다이어그램

```
                         ┌─────────────┐
                         │  Blogsmith   │ (외부 시스템)
                         │  (inbox/ 에  │
                         │   .md 생성)  │
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │  watcher.py  │  신규 파일 감지
                         │  done.json   │  (처리 이력 관리)
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │ classifier   │  카테고리 분류
                         │ .py          │  (insurance/invest/
                         └──────┬──────┘   loan/tax/general)
                                │
                         ┌──────▼──────┐
                         │ transformer  │  frontmatter 변환
                         │ .py          │  slug 생성, heroImage=R2
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                         │ validator.py │  ★ tags/bool 타입 auto-fix
                         │              │  NFD→NFC slug 정규화
                         └──────┬──────┘
                                │
                         ┌──────▼──────┐
                  ┌──────┤thumbnail.py  ├──────┐
                  │      │ (PIL 1024px) │      │
                  │      └──────┬──────┘      │
                  │             │              │
          public/         R2 업로드        배경 이미지 풀
     blog-thumbnails/   (퍼블릭 URL)     (15장 랜덤 선택)
                  │             │              │
                  └──────┬──────┘              │
                         │                     │
                         ├─────────────────────┘
                         │
                  ┌──────▼──────┐
                  │ entity_      │  내부 링크 삽입
                  │ injector.py  │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  deployer.py  │  build → deploy
                  │               │  실패 시 auto-fix →
                  │               │  재시도 → Telegram
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Cloudflare  │
                  │  Pages (Prod)│
                  │  persona.    │
                  │  aikorea24.kr│
                  └─────────────┘

   ┌─────────────────────────────────────┐
   │        launchd (30분 간격)           │
   │  ~/Library/LaunchAgents/            │
   │  com.aikorea24.persona-publisher    │
   │  .plist                             │
   │  StartInterval = 1800               │
   │  RunAtLoad = true                   │
   └─────────────────────────────────────┘
```

---

### 20.3 상세 모듈 설명

#### 20.3.1 watcher.py

- **감시 디렉터리**: `/Users/twinssn/projects/money-aikorea24/inbox/`
- **처리 조건**: `.md` 확장자 + `done.json`에 미등록된 파일
- **상태 관리**: `done.json`에 `published`, `duplicate_skip`, `error` 상태 기록
- **파일 이동**: 처리 완료 후 `inbox/YYYYMMDD/`로 이동 (아카이빙)

#### 20.3.2 classifier.py

- **분류 방식**: 카테고리별 키워드 사전 매칭 (`config/category-keywords.json`)
- **카테고리**: `insurance` | `invest` | `loan` | `tax` | `general`
- **동점/무득점**: `general` + `needs_review=true` 플래그

#### 20.3.3 transformer.py

- **slug 생성**: 파일명에서 타임스탬프 접두사(`YYYYMMDD-HHMMSS-`) 제거 → slug
- **heroImage**: R2 퍼블릭 URL 자동 생성
  ```python
  fm["heroImage"] = r2_upload.get_public_url(slug)
  # → https://pub-2f5c7af1c...r2.dev/blog-thumbnails/{slug}.jpg
  ```
- **frontmatter 필드**: `title`, `description`, `pubDate`, `updatedDate`, `draft`, `category`, `tags`, `heroImage`, `needs_review`

#### 20.3.4 validator.py (2026-06-08 신규)

**목적**: Astro content collection 스키마에 맞지 않는 frontmatter를 자동 수정

| 검증 항목 | auto-fix 동작 |
|-----------|---------------|
| `tags`가 문자열일 때 | `"a, b, c"` → `["a", "b", "c"]` 배열로 변환 |
| `draft`/`needs_review`가 문자열일 때 | `"true"` → `true` (boolean) |
| `category`가 유효하지 않을 때 | `"foobar"` → `"general"` fallback |
| NFD 파일명 | NFC 정규화 + 공백→하이픈 치환 |

**호출 위치**: `publisher.py` STEP 4.2 (transform 직후)

#### 20.3.5 thumbnail.py

- **크기**: 1024×1024px, JPEG quality 90
- **배경 이미지 풀** (38장, 카테고리별 랜덤 선택):

  | 카테고리 | 배경 이미지 |
  |---|---|
  | insurance | `bg_seoul_30.jpeg`, `bg_single_50.jpeg` |
  | invest | `bg_gyeonggi_40.jpeg`, `bg_general_01.jpeg`, `bg_general_02.jpeg` |
  | loan | `bg_seoul_20.jpeg`, `bg_busan_all.jpeg`, `bg_rural_50.jpeg` |
  | tax | `bg_seoul_60.jpeg`, `bg_single_20.jpeg`, `bg_general_03.jpeg` |
  | general | `bg_gangwon_all.jpeg`, `bg_jeju_all.jpeg`, `bg_general_04.jpeg`, `bg_general_05.jpeg` |

- **저장 경로**: `public/blog-thumbnails/{slug}.jpg`
- **R2 업로드**: 생성 후 자동으로 R2 (`hotissue-images/blog-thumbnails/`)에 업로드
- **R2 퍼블릭 URL**: `https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails/{slug}.jpg`

#### 20.3.6 deployer.py

**배포 명령어**:
```bash
npx wrangler pages deploy dist/ \
  --project-name money-aikorea24 \
  --commit-dirty=true \
  --commit-message="feat: auto publish new posts"
```
> ⚠️ `--branch` 플래그를 지정하지 않아야 **Production** 환경에 배포됨.  
> `--branch production`은 **Preview** 환경으로 가므로 주의.

**실패 시 auto-fix 로직**:
```
빌드 실패
  → stderr에서 콘텐츠 컬렉션 스키마 에러 파싱
  → 해당 .md 파일에 validator 실행 (auto-fix)
  → 재빌드
  → 성공 → 배포 진행
  → 실패 → Telegram으로 수동 발행 요청
```

**Telegram 알림 정책**:
| 상황 | 알림 |
|------|------|
| 빌드+배포 성공 | ❌ 보내지 않음 |
| auto-fix 후 성공 | ❌ 보내지 않음 |
| auto-fix 불가 (스키마 오류 파싱 실패) | 🚨 `자동 발행 실패 — 수동 발행 필요` |
| auto-fix 시도했지만 수정 불가 | 🚨 `자동 발행 실패 — 수동 발행 필요` |
| auto-fix → 재빌드도 실패 | 🚨 `자동 발행 실패 — 수동 발행 필요` |
| wrangler 배포 실패 | 🚨 `자동 발행 실패 — 수동 발행 필요` |

**환경변수**:
| 변수 | 출처 | 용도 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | `.env` | Telegram 봇 토큰 |
| `TELEGRAM_CHAT_ID` | `.env` | 알림 수신자 ID |
| `R2_ACCOUNT_ID` | `.env` | R2 계정 ID |
| `R2_ACCESS_KEY_ID` | `.env` | R2 S3 호환 키 |
| `R2_SECRET_ACCESS_KEY` | `.env` | R2 시크릿 키 |

---

### 20.4 launchd 스케줄러 (30분 간격)

**plist 파일 위치**: `~/Library/LaunchAgents/com.aikorea24.persona-publisher.plist`  
**소스 파일**: `scripts/persona-publisher/com.aikorea24.persona-publisher.plist` (git 관리)

**주요 설정**:
```xml
<key>StartInterval</key>
<integer>1800</integer>        <!-- 30분 -->

<key>RunAtLoad</key>
<true/>                        <!-- 로그인 시 자동 실행 -->

<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <!-- npm/node를 찾을 수 있도록 PATH 설정 필수 -->
</dict>
```

**로그**: `logs/persona-publisher.log` (프로젝트 루트 내, `/tmp/` 아님)

**재부팅 생존**: `~/Library/LaunchAgents/`에 plist가 있으면 로그인 시 자동 로드됨.

**관리 명령어**:
```bash
# 서비스 상태 확인
launchctl list kr.aikorea24.persona-publisher

# 상세 정보
launchctl print gui/501/kr.aikorea24.persona-publisher

# plist 재로드 (수정 후)
launchctl bootout gui/501/kr.aikorea24.persona-publisher
launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.aikorea24.persona-publisher.plist
```

---

### 20.5 R2 썸네일 업로드

**모듈**: `scripts/persona-publisher/r2_upload.py`

**연결 정보** (S3 호환 API):
- Endpoint: `https://{ACCOUNT_ID}.r2.cloudflarestorage.com`
- Bucket: `hotissue-images` (기존 버킷共用)
- Prefix: `blog-thumbnails/`
- Public URL: `https://pub-2f5c7af1c303419a933069212bc25874.r2.dev`

**업로드 조건**:
- 로컬 `public/blog-thumbnails/`에 저장 후 R2에도 업로드
- 이미 존재하는 slug는 스킵 (썸네일 재생성 방지)

---

### 20.6 데이터 파일 (build 필수)

| 파일 | 경로 | 비고 |
|------|------|------|
| benefits-clean.json | `public/` | 지원금 데이터 (git에 없음) |
| benefits-curated.json | `public/` | 큐레이션 혜택 |
| welfare-central.json | `public/` | 중앙부처 복지 데이터 |
| welfare-local.json | `public/` | 지방 복지 데이터 |
| persona-stats.json | `public/` | 2,891개 페르소나 통계 (git에 없음) |
| blog-match.json | `public/` | 블로그-페르소나 매칭 |
| bg_img/ | `public/bg_img/` | 배경 이미지 38장 (git에 없음) |
| 배경 이미지 | `public/bg_img/` | 38장 (git에 없음) |

---

### 20.7 알려진 이슈 및 주의사항

| 이슈 | 설명 |
|------|------|
| **npm PATH 문제** | launchd 실행 시 PATH에 `/opt/homebrew/bin` 없음. plist의 `EnvironmentVariables`에서 명시적 설정 필요 |
| **`--branch production` 주의** | `wrangler pages deploy`에 `--branch production`을 주면 **Preview** 환경으로 배포됨. Production 배포는 브랜치 미지정 또는 `--branch main` |
| **`tags` 타입** | Blogsmith가 `tags: "a, b, c"` (문자열)로 생성 시 Astro 스키마 검증 실패. `validator.py`가 auto-fix |
| **NFD 파일명** | macOS에서 한글 파일명이 NFD(자모 분리)로 저장될 수 있음. `validator.normalize_slug()`로 NFC 정규화 |
| **R2 API 토큰 권한** | `CLOUDFLARE_API_TOKEN`에 R2 권한 없음. 대신 S3 호환 키(`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`) 사용 |
| **데이터 파일 git 누락** | `benefits-clean.json` 등 대용량 파일이 git에 없어 clone 후 빌드 불가. Cloudflare Pages CI에서 생성 필요 |

---

### 20.8 운영 체크리스트

- [ ] inbox/에 새 .md 파일이 들어왔는가?
- [ ] launchd가 정상 실행 중인가? (`launchctl list kr.aikorea24.persona-publisher`)
- [ ] `logs/persona-publisher.log`에 에러가 없는가?
- [ ] `done.json`의 `error` 상태 항목이 없는가?
- [ ] 라이브 `search.json`에 신규 글이 포함되었는가?
- [ ] R2에 썸네일이 업로드되었는가?

---

---

## 14. 보안 감사 결과 (2026-06-23)

### 14-1. 감사 요약

| 항목 | 값 |
|------|-----|
| 전체 위험도 | 🔴 높음 |
| Critical 이슈 | 4건 |
| High 이슈 | 3건 |
| Medium 이슈 | 4건 |
| 총 이슈 | 11건 |

### 14-2. 발견 및 조치된 이슈

| 등급 | 이슈 | 파일 | 조치 |
|------|------|------|------|
| 🔴 Critical | 세션 인증 우회 (posts/[id].js) | `posts/[id].js:18-25` | HMAC 서명 검증 누락 → `_shared/session.js` import로 교체 |
| 🔴 Critical | 하드코딩 개발용 세션 시크릿 | `kakao.js:40`, `session.js:40` | `dev-secret-CHANGE-IN-PRODUCTION` fallback 제거 → 미설정 시 throw |
| 🔴 Critical | .env 백업 파일 시크릿 노출 | `.env.bak.telegram` | 파일 삭제 + `.gitignore`에 `*.bak`, `*.bak.*`, `.env.bak*` 추가 |
| 🔴 Critical | CORS wildcard(*) 설정 | `benefit-click.js:2,29` | `https://persona.aikorea24.kr` 화이트리스트 + OPTIONS preflight 핸들러 추가 |
| 🟡 High | 클릭재킹 방어 미흡 | `_headers` | `X-Frame-Options: DENY`, CSP, HSTS 등 보안 헤더 전면 교체 |
| 🟡 High | Rate Limiting 미적용 | 전체 API | `docs/SECURITY.md`에 WAF 설정 가이드 문서화 |
| 🟡 High | 세션 만료 7일 고정 | `kakao.js:122` | `Max-Age=60*60*24` (24h)로 단축 + `SameSite=Strict` 적용 |
| 🟠 Medium | 카카오 REST 키 하드코딩 폴백 | `kakao.js:38`, `login.astro:4` | `fac8da4c0dd8911f025dce7bf2f76f0d` fallback 제거 → throw Error |
| 🟠 Medium | 카카오 콜백 HTML 인젝션 위험 | `kakao.js:134-141` | HTML 문자열 주입 제거 → 302 리다이렉트 + Set-Cookie 헤더 방식 |
| 🟠 Medium | .bak 파일 git 추적 | 41개 .bak 파일 | `git rm --cached` + `.gitignore` 패턴 추가 |

### 14-3. 적용된 보안 헤더 (_headers)

```
/*
  X-Frame-Options: DENY
  Content-Security-Policy: frame-ancestors 'none'; default-src 'self'; script-src 'self' 'unsafe-inline' https://developers.kakao.com; connect-src 'self' https://kapi.kakao.com https://kauth.kakao.com; img-src 'self' data: https:;
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
/api/*
  Access-Control-Allow-Origin: https://persona.aikorea24.kr
  Access-Control-Allow-Methods: GET, POST, OPTIONS
```

### 14-4. 수동 작업 필요 항목

1. **Cloudflare Dashboard Secrets**: `SESSION_SECRET`, `KAKAO_REST_KEY`, `PUBLIC_KAKAO_REST_KEY` 설정 (미설정 시 로그인 불가)
2. **Cloudflare WAF Rate Limiting**: `docs/SECURITY.md` 가이드대로 규칙 등록
3. **시크릿 재발급**: `.env` 노출 이력 있으므로 `GITHUB_TOKEN`, `OPENAI_API_KEY`, `NVIDIA_API_KEY`, `TELEGRAM_BOT_TOKEN`, `R2_SECRET_ACCESS_KEY` 재발급 권장

---

## 15. 블로그 콘텐츠 분석 (2026-06-23)

### 15-1. 콘텐츠 현황

| 항목 | 값 |
|------|-----|
| 총 발행 글 수 | 236개 |
| 발행 기간 | 2026-04 ~ 2026-06 (3개월) |
| 월평균 발행량 | 78.7개 |
| 월별 분포 | 4월 16개 → 5월 186개 → 6월 34개 |

### 15-2. 카테고리 구조

| 카테고리 | 수 | 비중 |
|----------|-----|------|
| loan (대출) | 90 | 38.1% |
| tax (세금) | 59 | 25.0% |
| insurance (보험) | 47 | 19.9% |
| general (일반) | 26 | 11.0% |
| invest (투자) | 14 | 5.9% |

**불균형**: loan(38%) + insurance(20%) = 58% 과반 집중. invest(5.9%) 부족

### 15-3. 글 품질 지표

| 항목 | 값 |
|------|-----|
| 평균 본문 길이 | 2,618자 |
| heroImage 보유율 | 100% (236/236) |
| description 보유율 | 100% (236/236) |
| CTA 포함률 | 34.7% (82/236) |
| needs_review=true | 9.3% (22/236) |
| 본문 1500자 이상 | 204개 (86.4%) |
| 본문 500~1500자 | 32개 (13.6%) |
| 본문 500자 미만 | 0개 |

### 15-4. 프론트매터 필드 사용률

| 필드 | 사용 글 수 | 비율 |
|------|-----------|------|
| title | 236 | 100% |
| description | 236 | 100% |
| pubDate | 236 | 100% |
| draft | 236 | 100% |
| category | 236 | 100% |
| tags | 236 | 100% |
| heroImage | 236 | 100% |
| updatedDate | 205 | 86.9% |
| categories | 108 | 45.8% |
| needs_review | 22 | 9.3% |

### 15-5. 상위 태그 15개

| 태그 | 사용 횟수 |
|------|----------|
| #대출 | 42 |
| #2026 | 30 |
| #비상금대출 | 26 |
| #지원 | 25 |
| #관리 | 20 |
| #실손보험 | 20 |
| #프리랜서 | 18 |
| #절세 | 18 |
| #신용 | 18 |
| #거절 | 17 |
| #신용점수 | 17 |
| #보험 | 16 |
| #홈택스 | 15 |
| #보험료 | 15 |
| #재정 | 14 |

### 15-6. 퍼널 구조 현황

**내부 링크**: 228개 글 (96.6%)에서 내부 링크 보유

상위 내부 링크 편중:
- K-패스 활용법: 44회
- 대출 거절 가이드: 42회
- 소상공인 바우처: 14회
- 치아 임플란트: 13회

**외부 링크**: 77개 글 (32.6%)에서 외부 링크 보유
- 공공기관 위주: 홈택스(12), 금융감독원(12), LH(12)

**H2 헤딩 패턴 문제**:
- "마무리": 140회 (59%)
- "FAQ/자주 묻는 질문": 62회 (26%)
- 단조로운 반복. 주제별 세부 분석, 비교, 단계별 가이드 같은 구조적 헤딩 부족

**CTA 키워드 분포**:
- '신청 방법': 52개
- '클릭': 12개
- '신청하기': 12개
- '바로가기': 12개

### 15-7. 개선 권고 사항

1. **카테고리 재편**: loan 편중 해소. invest(투자), employment(일자리), life(생활) 등 신규 카테고리 도입
2. **CTA 강화**: 65%의 글에 행동 유도 없음. "신청하기", "바로가기" 버튼 필수 삽입하여 퍼널 전환율 개선
3. **내부 링크 분산**: 상위 2~3개 글에 링크 집중 해소. 카테고리별·시리즈별 교차 링크 구조화
4. **H2 구조 다각화**: "마무리/FAQ" 반복 패턴 탈피. 조건별 비교, 단계별 가이드, 사례 분석 헤딩 추가
5. **needs_review 22건 처리**: 발행 전 검수 대기 중인 글 정리 필요

---

## 16. Gov24 공공데이터 API 분석 (2026-06-23)

### 16-1. API 접속 정보

| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://api.odcloud.kr/api/gov24/v3/serviceList` |
| 인증 | `serviceKey` 쿼리 파라미터 (`DATA_GO_KR_API_KEY` — `~/.env.common`) |
| 총 서비스 수 | **10,967건** |
| 페이징 | `page`, `perPage` (최대 100건/요청) |
| 응답 필드 | 21개 (서비스명, 목적요약, 분야, 지원대상, 지원내용, 신청방법, 상세조회URL 등) |

### 16-2. 서비스분야 분포 (전체 10,967건)

| 분야 | 건수 | 비중 |
|------|------|------|
| 생활안정 | 2,282 | 20.8% |
| 농림축산어업 | 1,679 | 15.3% |
| 보육·교육 | 1,512 | 13.8% |
| 보건·의료 | 1,219 | 11.1% |
| 임신·출산 | 915 | 8.3% |
| 고용·창업 | 843 | 7.7% |
| 문화·환경 | 666 | 6.1% |
| 보호·돌봄 | 641 | 5.8% |
| 행정·안전 | 637 | 5.8% |
| 주거·자립 | 573 | 5.2% |

### 16-3. 소관기관유형 분포

| 기관 유형 | 건수 |
|-----------|------|
| 시군구 | 6,523 (59.5%) |
| 광역시도 | 1,389 |
| 중앙행정기관 | 1,053 |
| 공공기관 | 600 |
| 지방출자·출연기관 | 583 |
| 지방공기업 | 557 |
| 교육청 | 262 |

### 16-4. 페르소나별 매칭 결과

| 페르소나 | 매칭 건수 | 핵심 분야 |
|----------|----------|----------|
| 청년 | 1,259건 | 보육·교육(376), 주거·자립(202), 생활안정(191), 고용·창업(190) |
| 노인 | 1,290건 | 보건·의료, 생활안정, 보호·돌봄 |
| 직장인 | 346건 | 고용·창업(109), 생활안정(62), 주거·자립(42) |
| 중장년 | 85건 | 고용·창업(34), 생활안정(20) |

### 16-5. 업데이트 빈도

| 항목 | 값 |
|------|-----|
| 날짜 필드 | `등록일시`, `수정일시` (YYYYMMDDHHmmss, 14자리) |
| 주당 수정 건수 | **약 142건** (최근 4주 기준) |
| 월당 수정 건수 | **약 1,700건** |
| 신규 등록 월 평균 | **약 22건** |
| 4~5월 일괄 갱신 | 2026-04(3,672건), 2026-05(4,968건) |

### 16-6. 카테고리 매핑 테이블

```python
CATEGORY_MAP = {
    "고용·창업": "general",
    "주거·자립": "loan",
    "보건·의료": "insurance",
    "생활안정":  "general",
    "보육·교육": "general",
    "임신·출산": "insurance",
    "문화·환경": "general",
    "보호·돌봄": "insurance",
    "행정·안전": "general",
    "농림축산어업": None,  # persona 사이트와 무관
}
```

**매핑 결과**: general 1,093건 + insurance 516건 + loan 80건 = **1,689건** (전체의 15.4%)

---

## 17. 페르소나 진단 페이지 구조 (2026-06-23)

### 17-1. URL 구조

```
/persona/{지역}-{성별}-{나이}/
예: /persona/서울-남자-30대/
    /persona/경기-여자-40대/
    /persona/부산-남자-60대/
```

- **라우트 파일**: `src/pages/persona/[...slug].astro` (catchall)
- **슬러그 파싱**: `_` 구분자 → `서울_남자_32` (하이픈→언더스코어 변환)
- **10년 단위**: `/persona/서울-남자-30대/` (색인 대상, 204개)
- **1년 단위**: `/persona/서울-남자-35/` (noindex)

### 17-2. 페이지 섹션 구성

| 순서 | 섹션 | 컴포넌트 |
|------|------|----------|
| 1 | 히어로 (배경 카드 이미지) | 인라인 CSS |
| 2 | 페르소나 유형 카드 | 인라인 |
| 3 | 카드 이미지 (데스크톱/모바일) | 인라인 |
| 4 | 공유 버튼 (카카오/링크복사) | 인라인 |
| 5 | "당신은..." 섹션 | 인라인 |
| 6 | KPI 그리드 (아파트/학력/혼인/무직) | 인라인 |
| 7 | 소득 백분위 게이지 | 인라인 |
| 8 | 금융 인사이트 | 인라인 |
| 9 | 블로그 추천 | `PersonaBlogRecommend.astro` |
| 10 | 주거형태/학력/직업/혼인 TOP5 | 인라인 |
| 11 | 페르소나 스토리 (20명) | 인라인 |
| 12 | 다른 지역 비교 링크 | 인라인 |
| 13 | 혜택 매칭 카드 | `BenefitCards.astro` |
| 14 | 복지 매칭 카드 | `WelfareCards.astro` |
| 15 | 커뮤니티 연결 | 인라인 |
| 16 | 관련 금융 가이드 | 인라인 |
| 17 | CTA ("나도 분석해보기") | 인라인 |

### 17-3. 핵심 데이터 소스

| 데이터 | 파일 | 역할 |
|--------|------|------|
| 페르소나 통계 | `public/persona-stats.json` | 2,891개 조합별 통계 |
| 임금 테이블 | `src/data/wage-table.json` | 직종별 임금 + 성별·연령 보정 |
| 직업 카테고리 | `src/data/job-category-map.json` | 직업명 → 10개 카테고리 매핑 |
| 결정 카드 | `src/data/decision-cards.json` | 페르소나별 결정 카드 |
| 지원금 데이터 | `public/benefits-clean.json` | 정제된 지원금 |
| 큐레이션 혜택 | `public/benefits-curated.json` | 선별된 혜택 24건 |
| 복지 데이터 | `public/welfare-central.json`, `welfare-local.json` | 중앙부처+지방 복지 |

### 17-4. 매칭 로직

**`src/lib/benefitMatcher.ts`**:
- 연령 하드 필터 (age_range)
- 성별 하드 필터
- 지역 매칭 (전국/특정지역)
- 큐레이션 우선 가점 (+25)
- 카테고리 보너스 (+10)
- 소득/재산 경고 (-3)
- score > 35인 것만 반환

**`src/lib/welfareMatcher.ts`**:
- 지역 매칭 (ctpvNm 기반, 17개 시도)
- 생애주기 매칭 (청년/중장년/노년)
- 신선도 가점 (6개월 이내 갱신 +5)
- 조회수 보정 (+2~5)

---

## 18. 썸네일 생성 로직 (2026-06-23)

### 18-1. 생성 모듈

**파일**: `scripts/persona-publisher/thumbnail.py`

| 항목 | 값 |
|------|-----|
| 이미지 크기 | 1024x1024px |
| 포맷 | JPEG (quality=90) |
| 출력 경로 | `public/blog-thumbnails/{slug}.jpg` |
| R2 업로드 | `pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails/` |

### 18-2. 카테고리별 설정

| 카테고리 | 배경 이미지 풀 | 뱃지 색상 (RGB) | 뱃지 텍스트 |
|----------|---------------|-----------------|-------------|
| insurance | `bg_seoul_30.jpeg`, `bg_single_50.jpeg` | (30, 58, 95) | 보험 |
| invest | `bg_gyeonggi_40.jpeg`, `bg_general_01~02.jpeg` | (6, 95, 70) | 투자·절세 |
| loan | `bg_seoul_20.jpeg`, `bg_busan_all.jpeg`, `bg_rural_50.jpeg` | (146, 64, 14) | 대출·부동산 |
| tax | `bg_seoul_60.jpeg`, `bg_single_20.jpeg`, `bg_general_03.jpeg` | (76, 29, 149) | 세금·절약 |
| general | `bg_gangwon_all.jpeg`, `bg_jeju_all.jpeg`, `bg_general_04~05.jpeg` | (31, 41, 55) | 금융 가이드 |

### 18-3. 생성 과정

1. 배경 이미지 로드 (`public/bg_img/`에서 카테고리별 풀에서 랜덤 선택)
2. 밝기 45% 조정 (텍스트 가독성)
3. 하단 반투명 검정 그라디언트 오버레이
4. 카테고리 뱃지 (상단 좌측, 둥근 사각형)
5. 제목 텍스트 (중앙 하단, 최대 3줄, 그림자 포함)
6. 도메인 워터마크 (하단 중앙)
7. JPEG 저장 후 R2 업로드

### 18-4. heroImage URL 패턴

```
https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails/{slug}.jpg
```

### 18-5. R2 업로드 모듈

**파일**: `scripts/persona-publisher/r2_upload.py`

- **방식**: boto3 (S3 호환 API)
- **버킷**: `hotissue-images`
- **접두사**: `blog-thumbnails/`
- **캐시**: `Cache-Control: public, max-age=31536000, immutable`

---

## 19. 자동 글쓰기 파이프라인 준비도 (2026-06-23)

### 19-1. 준비도 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| Gov24 API 데이터 소스 | **확보** | 10,967건, 주 142건 업데이트 |
| 카테고리 매핑 | **확정** | 5개 카테고리, 1,689건 매핑 |
| 썸네일 생성 | **재사용 가능** | `thumbnail.py` 그대로 사용 |
| R2 업로드 | **재사용 가능** | `r2_upload.py` 그대로 사용 |
| 프론트매터 스키마 | **확정** | title, description, pubDate, draft, category, tags, heroImage |
| 페르소나 CTA 링크 | **가능** | Gov24 `상세조회URL` 직접 연결 |
| AI 글쓰기 모듈 | **신규 구축 필요** | 5000 프로젝트 `shared/ai_writer.py` 참고 |
| 스케줄러 | **신규 구축 필요** | 5000 프로젝트 `scheduler.py` 참고 |
| 프로토타입 1건 생성 | **즉시 가능** | Gov24 → 매핑 → AI 글쓰기 → thumbnail → R2 → .md |

### 19-2. 기존 publisher 모듈 재사용 가능 목록

| 모듈 | 경로 | 재사용 |
|------|------|--------|
| 분류기 | `classifier.py` | O (카테고리 키워드 매핑) |
| 변환기 | `transformer.py` | O (프론트매터 생성) |
| 검증기 | `validator.py` | O (스키마 검증) |
| 썸네일 | `thumbnail.py` | O (1024x1024 JPEG 생성) |
| R2 업로드 | `r2_upload.py` | O (boto3 업로드) |
| 배포기 | `deployer.py` | O (npm build + wrangler deploy) |
| 필터 | `filter.py` | △ (import 되었으나 미사용) |
| 엔티티 주입 | `entity_injector.py` | O (관련글 연결) |

### 19-3. 블로그 콘텐츠 현황과 자동 글쓰기 정합성

| 항목 | 기존 블로그 | 자동 글쓰기 예상 |
|------|------------|-----------------|
| 평균 본문 길이 | 2,618자 | 2,000~3,000자 권장 |
| heroImage | 100% 보유 | thumbnail.py로 100% 생성 가능 |
| CTA 포함률 | 24.2% | 100% 삽입 가능 (Gov24 URL) |
| 내부 링크 | 96.6% 보유 | entity_injector로 자동 연결 |
| 카테고리 분포 | loan(38%), tax(25%), insurance(20%) | general(65%), insurance(30%), loan(5%) 예상 |

### 19-4. 보완 필요 사항

1. **AI writer 모듈 구축**: Gov24 데이터 → 블로그 글 생성 AI 프롬프트 개발
2. **키워드 매칭 정확도 개선**: `지원대상` 외 `서비스명` 기반 2차 필터링
3. **카테고리 매핑 다각화**: `고용·창업` → 별도 `employ` 카테고리 추가 검토
4. **thumbnail.py 경로 유연화**: 하드코딩된 절대 경로 → 환경변수화
5. **r2_upload.py 보안 개선**: 소스코드 내 자격증명 기본값 제거
6. **스케줄러 구축**: `daily_quota` 관리 + 중복 방지 + catchup 로직

---

*문서 갱신: 2026-06-23 | Reasonix Code*
