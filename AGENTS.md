# AGENTS.md — 프로젝트 에이전트 가이드

> persona.aikorea24.kr · 한국인 페르소나 통계·지원금·금융 가이드 플랫폼
> 마지막 갱신: 2026-06-24

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

---

## 두 콘텐츠 생성 시스템

`src/content/blog/`에 글을 쓰는 두 개의 **독립된 Python 파이프라인**이 존재합니다.
혼동하지 않도록 주의하세요.

```
scripts/
  auto-writer/        ← AI 자동 생성 (NVIDIA NIM LLM)
  manual-publisher/  ← 수동 인박스 발행 (사용자가 파일을 떨어뜨림)
```

아래는 각 시스템의 상세 아키텍처입니다.

---

### ⚙️ auto-writer (AI 자동 생성)

**목적**: Gov24/금감원/data.go.kr 데이터를 LLM으로 블로그 글로 자동 생성

**실행**: `python3 scheduler.py [--dry-run | --status | --fetch]`
- launchd: `~/Library/LaunchAgents/com.aikorea24.auto-writer.plist` — 매일 09:00 1회 실행
- 하루 최대 **5개** 생성 + 발행 (`DAILY_QUOTA=5`)

**12단계 파이프라인** (`pipeline.py`):

| 단계 | 설명 | 코드 위치 |
|------|------|-----------|
| 1 | 오늘 quota 확인 (5개 초과 시 종료) | `pipeline.py:124-131` |
| 2 | pending 없으면 Gov24 + finlife + invest 3개 소스 재수집 | `pipeline.py:133-143` |
| 3 | 카테고리 가중치 기반 서비스 선택 (loan 40%, insurance 25%, tax 20%, invest 10%, general 5%) | `pipeline.py:148` → `db_utils.pick_next_service()` |
| 2b | 블로그 부적합 키워드 필터링 → skip + mark_error | `pipeline.py:155-181` |
| 3 | NVIDIA NIM LLM으로 글 생성 (fallback 체인: diffusiongemma → gemma-4 → gemma-3n) | `pipeline.py:188` → `writer.generate_article()` |
| 3a | 맞춤법·문법 교정 (gemma-3n proofreader + regex 후처리) | `pipeline.py:198` → `writer.proofread()` |
| 3b | LLM 출력에서 `# 제목` 추출 | `pipeline.py:201-205` |
| 3c | H2 기반 SUMMARY_BOX (목차) 생성 | `pipeline.py:208-210` |
| 3d | 인라인 CTA 삽입 (조건 섹션 뒤 + 금리 섹션 뒤) | `pipeline.py:213` |
| 4 | Reviewer 검수 (Mimo Qwen2.5 14B → needs_review 플래그) | `pipeline.py:216` → `shared/reviewer.py` |
| 4b | Validator: CTA 강제 삽입, 헤딩·본문 길이 검증 | `pipeline.py:224` → `validator.validate_and_fix()` |
| 5 | Slug 생성 | `pipeline.py:232` → `validator.make_slug()` |
| 6 | RELATED_POSTS 채우기 (내부 링크 균등 분배) | `pipeline.py:235-238` |
| 7 | 썸네일 생성 + R2 업로드 | `pipeline.py:241-243` |
| 8 | Frontmatter + 본문 조합 | `pipeline.py:246-256` |
| 9 | 파일 저장 (`src/content/blog/{slug}.md`) | `pipeline.py:259-262` |
| 10 | DB 기록 (publish_ledger + services.status='published') | `pipeline.py:265-270` |
| 11 | 빌드 + 배포 | `pipeline.py:273-280` |

**데이터 소스**:
| 소스 | 파일 | API 설명 |
|------|------|----------|
| Gov24 | `fetcher.py` | 공공데이터포털 gov24/v3/serviceList (API 키 필요) |
| 금감원 finlife | `fetcher_loan_fin.py` | 금융상품 (정기예금/적금/주택담보대출/전세자금대출) |
| data.go.kr | `fetcher_invest.py` | ETF시세/지수시세 |

**DB**: `scripts/auto-writer/db/auto-writer.db` (SQLite, 3개 테이블)
- `services`: 수집된 서비스 (service_id, title, category, field, summary, detail, target, persona, status 등)
- `publish_ledger`: 발행 기록 (slug, title, category, persona, model_used, internal_link_count)
- `fetch_meta`: 마지막 수집 시각

**상태 관리**:
- `pending` → `published` / `error` / `updated`
- `pick_next_service()`: 카테고리 가중치 기반 deficit 계산 → 가장 부족한 카테고리부터 선택
- `get_related_posts()`: internal_link_count 적은 글 우선 (링크 편중 방지)

**LLM 모델**:
| 우선순위 | 모델 | timeout | max_retries | 비고 |
|----------|------|---------|-------------|------|
| 1 | `google/diffusiongemma-26b-a4b-it` | 120s | 2 | 메인 (실험모델, 품질 경고) |
| 2 | `google/gemma-4-31b-it` | 120s | 1 | 폴백 |
| 3 | `google/gemma-3n-e4b-it` | 90s | 1 | 최후 폴백 |

Reviewer: Unsloth Qwen2.5 14B (Mimo API)

**환경변수**:
- `NVIDIA_API_KEY`: NVIDIA NIM LLM API 키
- `MIMO_API_KEY`: Reviewer Mimo API 키
- `DAILY_QUOTA`: 일일 발행 한도 (기본 5, env로 재정의 가능)
- `CF_R2_*`: R2 썸네일 업로드용
- `TELEGRAM_BOT_TOKEN`: 에러 알림용

**카테고리 가중치** (`config/category_map.yaml`):
```yaml
category_quota:
  loan:      0.40
  insurance: 0.25
  tax:       0.20
  invest:    0.10
  general:   0.05
```

**Gov24 분야 → 카테고리 매핑** (일부 필드는 제외됨):
- "농림축산어업" → `null` (수집에서 제외)
- "보건·의료" → `insurance`
- "보호·돌봄" → `insurance`
- "임신·출산" → `insurance`
- "고용·창업" → `general`
- "주거·자립" → `loan`
- "생활안정" → `general`

**현재 부적합 키워드 필터** (`pipeline.py:156-166`):
```python
_EXCLUDE_KW = ["농업", "어업", "축산", "수산", "임업", "농림",
               "천일염", "포장재", "동물", "백신", "가축",
               "양식", "어가", "영농", "농기계", "비료",
               "종자", "사료", "축사", "수산물"]
```
→ 이 필터는 **너무 좁음**. 아래 확장 필요 목록 참조.

---

### 📥 manual-publisher (수동 인박스 발행)

**목적**: 사용자가 수동으로 작성/수집한 글을 `inbox/`에 넣으면 30분마다 감지하여 발행

**실행**: launchd (plist: `com.aikorea24.manual-publisher.plist`) → `watcher.py`가 30분 간격으로 `publisher.run()` 호출

**파이프라인** (`publisher.py`):
| 단계 | 설명 |
|------|------|
| 1 | `watcher.get_new_files()` → inbox/에서 새 파일 감지 (모든 파일 처리) |
| 2 | `classifier.classify()` → 카테고리 분류 (insurance/invest/loan/tax/general) + needs_review |
| 3 | `transformer.transform()` → frontmatter 변환 + slug 생성 |
| 4 | `validator.normalize_slug()` → slug 정규화 (NFD→NFC, 공백→하이픈) |
| 5 | `validator.validate_and_fix_content()` → frontmatter 타입 검증 + auto-fix |
| 6 | 중복 제목 체크 |
| 7 | `thumbnail.generate()` → 썸네일 생성 |
| 8 | `entity_injector.inject()` → 엔티티 링크 삽입 |
| 9 | `resolve_dst_path()` → 충돌 시 `_2`, `_3` suffix |
| 10 | `src/content/blog/`에 복사 + inbox/ → inbox/YYYYMMDD/로 이동 |
| 11 | `watcher.mark_done()` → done.json 기록 |
| 12 | `deployer.build_and_deploy()` → 빌드 + 배포 |

**중요**: 이 시스템은 **사용자가 수동으로 선별한 파일**만 처리합니다.
- inbox/에 파일을 직접 넣는 것 = 발행 의사 표현
- `filter.py`는 **데드코드** (import만 되고 실제 호출되지 않음)
- `classifier.py`는 카테고리 판별만 함 (컨텐츠 필터링 아님)
- **이 시스템에는 컨텐츠 필터를 추가하지 말 것** — 사용자의 의도적 발행을 방해하면 안 됨

---

### 🎯 콘텐츠 필터링 전략

**문제**: auto-writer가 생성한 글 중에 사이트 취지에 맞지 않는 콘텐츠가 포함됨
(한센인·마약치료보조금·의료급여·법률구조·특수직군 지원금 등)

**해결 방향**: auto-writer의 **step 3b** 키워드 필터 확장 (글 생성 전 차단)

**적용할 부적합 키워드 목록** (2026-06-24 기준):
```
# 의료·질환 (한센인·결핵·치매·백내장·임플란트 등)
한센, 수술비, 치매, 백내장, 임플란트, 발달장애, 학대피해,
보호종료, 가정폭력, 북한이탈, 귀화,

# 특수직군·업종
선원, 어업인, 항로표지, 해양사고, 초지, 원산지검증, 유휴간호사,

# 중독·법률
금연, 마약, 결핵,

# 법률구조
진술조력인, 국선변호사, 법률홈닥터,

# 고위험·희귀·감염병
고위험임산부, 희귀질환, 감염병격리, 영양플러스, 방문건강,

# 의료비·보조기기
응시료, 노인안검진, 개안술, 인공관절, 장기요양, 낙상방지, 보조기기
```

**필터 위치**: `scripts/auto-writer/pipeline.py:156-166` — `_EXCLUDE_KW` 리스트 확장

**참고**: Gov24 fetcher에서 `category is None` (농림축산어업)은 이미 수집 단계에서 제외됨.
의료 관련 서비스는 "보건·의료" 필드로 `insurance` 카테고리에 할당되어 **수집은 되지만**,
LLM이 부적합한 내용(질병·치료·법률)을 다루는 글을 생성하므로 **글 생성 전에 키워드 차단**하는 편이 효과적.

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
