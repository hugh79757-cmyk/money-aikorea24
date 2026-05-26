# 페르소나 (persona.aikorea24.kr) — 기술 문서

> 최종 업데이트: 2026-05-26

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
│   │   ├── privacy.astro      # 개인정보처리방침
│   │   └── terms.astro        # 이용약관
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
│   │   └── WelfareCards.astro # 복지 카드 컴포넌트
│   │
│   └── data/
│       └── wage-table.json    # 임금 기준표 (직종·성별·연령·지역)
│
├── functions/                 # Cloudflare Pages Functions
│   └── api/
│       ├── _shared/
│       │   └── session.js     # HMAC-SHA256 세션 헬퍼 ★
│       ├── auth/
│       │   ├── callback/
│       │   │   └── kakao.js   # OAuth 콜백 처리 ★
│       │   └── logout.js      # 로그아웃 (쿠키 삭제)
│       └── community/
│           ├── posts.js       # 게시글 CRUD ★
│           ├── comments.js    # 댓글 CRUD ★
│           └── like.js        # 좋아요 토글 ★
│
├── public/
│   ├── persona-stats.json     # 페르소나 통계 데이터 (2,891개 조합)
│   ├── benefits-clean.json    # 지원금 데이터 (2,590건)
│   ├── blog-thumbnails/       # 블로그 OG 이미지
│   ├── cards/                 # 페르소나 카드 이미지 (데스크탑)
│   └── cards-mobile/          # 페르소나 카드 이미지 (모바일)
│
├── scripts/                   # 데이터 생성·관리 스크립트
│   ├── patch-income.mjs       # 소득 데이터 재계산
│   ├── deploy.sh              # 배포 스크립트 (M1 전용)
│   ├── generate-seed-posts.mjs # 커뮤니티 시드 게시글
│   └── fetch_benefits.py      # 정부 지원금 데이터 수집
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

### 11-1. 환경변수 목록

| 변수명 | 위치 | 필수 | 설명 |
|--------|------|------|------|
| `SESSION_SECRET` | Cloudflare Pages Secret | **필수** | HMAC 서명 키 (최소 32자 랜덤) |
| `KAKAO_REST_KEY` | Cloudflare Pages Secret | 권장 | 카카오 REST API 키 (미설정 시 하드코딩 fallback) |
| `KAKAO_CLIENT_SECRET` | Cloudflare Pages Secret | 선택 | 카카오 Client Secret |
| `ADMIN_USER_IDS` | Cloudflare Pages Secret | 선택 | 관리자 D1 user.id 목록 (콤마 구분) |
| `PUBLIC_KAKAO_REST_KEY` | `.env` | 선택 | 프론트엔드용 (빌드 시 주입) |

### 11-2. Wrangler 설정

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

### 11-3. 배포 절차

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

### 11-4. 환경변수 초기 설정 (신규 배포 시)

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

*문서 작성: Claude Sonnet 4.6 | 2026-05-26*
