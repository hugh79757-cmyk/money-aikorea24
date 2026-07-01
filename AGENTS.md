# AGENTS.md — 프로젝트 에이전트 가이드

> persona.aikorea24.kr · 한국인 페르소나 통계·지원금·금융 가이드 플랫폼
> 마지막 갱신: 2026-06-29

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
    persona/[...slug].astro        # 페르소나 결과 페이지 (2,244개)
    benefits/index.astro           # 지원금 검색
    blog/index.astro               # 블로그 목록
    blog/[...slug].astro           # 블로그 상세
    blog/category/[category]/      # 카테고리별 블로그
    community/index.astro          # 커뮤니티 목록 (클라이언트 렌더링)
    community/[id].astro           # 게시글 상세
    community/write.astro          # 글쓰기
    auth/login.astro               # 카카오 로그인
    nomad/                         # 디지털 노마드
    contact.astro                  # 문의
    data.astro                     # 데이터 페이지
    data/nemotron-korea.astro      # Nemotron 데이터 설명
    about.astro, terms.astro, privacy.astro, disclaimer.astro
    rss.xml.js                     # RSS 피드
    search.json.js                 # 검색 인덱스
  components/
    BaseHead.astro                 # <head> 메타 (OG, GA4, AdSense)
    Header.astro                   # 네비 + session_ui 쿠키 파싱
    Footer.astro
    AiTip.astro                    # AI 팁 컴포넌트
    BenefitCards.astro             # 지원금 매칭 카드
    WelfareCards.astro             # 복지 카드
    DecisionCards.astro            # 적합 지원금 TOP 3
    PersonaBlogRecommend.astro     # 페르소나별 블로그 추천
    InlinePersonaCTA.astro         # 블로그 인라인 CTA
    HeaderLink.astro               # 헤더 네비게이션 링크
    FormattedDate.astro            # 날짜 포맷
    JsonLd.astro                   # JSON-LD 구조화 데이터
    Disclaimer.astro               # 면책조항
    FloatingFab.astro, SearchBar.astro, ThemeToggle.astro, ...
    ui/Badge.astro, Button.astro, Card.astro, index.ts
  lib/
    benefitMatcher.ts              # 점수 기반 지원금 매칭
    deadlineExtractor.ts           # 마감일 추출
    welfareMatcher.ts              # 페르소나 ↔ 복지 매칭
    personaMatcher.ts              # 페르소나 매칭 유틸
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
  api/community/posts/[id].js      # 게시글 상세 CRUD
  api/community/comments.js        # 댓글 CRUD
  api/community/like.js            # 좋아요 토글
  api/benefit-click.js             # 혜택 클릭 집계
  community/[id].js                # 커뮤니티 라우트 패스스루
  og/index.js                      # OG → /cards/ 리다이렉트
public/
  persona-stats.json               # 페르소나 통계 (2,244키, 25MiB, 빌드 타임 전용)
  persona-stats-decade.json        # 10년 단위 서브셋 (204키, 4MiB, my-persona 런타임용)
  benefits-clean.json              # 지원금 정제 데이터
  benefits-curated.json            # 큐레이션 혜택 (25건)
  welfare-central.json             # 중앙부처 복지
  welfare-local.json               # 지방 복지
  blog-match.json                  # 블로그-페르소나 매칭
  bg_img/                          # 배경 이미지 (38장, (1) 중복 3개 포함 41파일)
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
- **getStaticPaths()**: persona-stats.json의 모든 키(2,244개)에 대해 HTML 생성
- **주의**: `persona-stats.json`의 지역명은 **짧은 이름**(경남, 충북, 전남 등) 사용. 인덱스 페이지 REGIONS 배열과 일치해야 함.
- **my-persona.astro 런타임**: `persona-stats-decade.json`(204키, 4MiB)을 fetch. 풀 데이터(25MiB)는 Cloudflare 25MiB 파일 제한 초과로 배포 제외.

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
npm run deploy       # scripts/deploy.sh (3-step: build → git push → wrangler)
```

**deploy.sh** 수행 순서:
1. `.env`에서 Cloudflare 인증 정보 로드
2. **Pre-check**: Cloudflare Pages에 `KAKAO_REST_KEY`, `KAKAO_CLIENT_SECRET`, `SESSION_SECRET` 3개 Secrets 존재 여부 검증
3. `npm run build` (prebuild → generate-decade-stats.mjs → Astro SSG)
4. `rm -f dist/persona-stats.json` (25MiB, Cloudflare 25MiB 파일 제한 초과)
5. `git add -A && git commit && git push origin main`
6. `npx wrangler pages deploy dist --project-name money-aikorea24 --branch main --commit-dirty=true`

**직접 Cloudflare Pages 배포**:
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

- **Python** (`scripts/load_env.py`): `.env` → `.env.common` 순서로 `os.environ`에 주입
  ```python
  from load_env import env
  API_KEY = env("DATA_GO_KR_API_KEY")
  ```
- **Node.js** (`lib/env-loader.ts`): `.env` → `.env.common` 순서로 `process.env`에 주입
  ```typescript
  import './lib/env-loader.js';
  const key = process.env.DATA_GO_KR_API_KEY;
  ```
- **Cloudflare Pages Functions**: 대시보드 Secrets에서 관리 (`.env` 무시)
  - **주의**: `functions/`의 Cloudflare Pages Functions가 참조하는 환경변수는 **Cloudflare Pages Secrets**에 등록되어야 함
  - `env.KAKAO_REST_KEY` — `login.astro`의 `import.meta.env.PUBLIC_KAKAO_REST_KEY`와 별개의 이름. 값은 같지만 `PUBLIC_` prefix가 없음
  - 필수 Pages Secrets: `KAKAO_REST_KEY`, `KAKAO_CLIENT_SECRET`, `SESSION_SECRET`
  - **Secret이 없으면 배포가 차단됨** (deploy.sh pre-check)

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
  auto-writer/        ← AI 자동 생성 (NVIDIA NIM LLM, 완전 자동)
  manual-publisher/  ← 수동 인박스 발행 (사용자가 inbox/에 파일을 넣으면 발행)
  generate-decade-stats.mjs  ← 빌드 시 persona-stats-decade.json 생성 (prebuild)
```

**핵심 차이점**:
| 항목 | auto-writer | manual-publisher |
|------|-------------|------------------|
| 트리거 | launchd 매일 09:00 | launchd 30분 간격 polling |
| 글 생성 | LLM이 자동 생성 | 사용자가 직접 작성 |
| 데이터 소스 | Gov24/finlife/invest API | inbox/ 디렉토리 |
| 필터링 | 부적합 키워드 차단 (42개) | 필터 없음 (사용자 의도 존중) |
| 분류 | DB 카테고리 가중치 기반 선택 | 키워드 기반 자동 분류 |
| 썸네일 | Pillow + R2 업로드 | Pillow + R2 업로드 |
| 배포 | 빌드 + wrangler deploy | 빌드 + wrangler deploy |

---

### ⚙️ auto-writer (AI 자동 생성)

**목적**: Gov24/금감원/data.go.kr 데이터를 LLM으로 블로그 글로 자동 생성

**실행**: `python3 scheduler.py [--dry-run | --status | --fetch]`
- CLI 옵션:
  - `--dry-run`: 발행 없이 데이터 확인만
  - `--status`: 오늘 발행 현황 출력
  - `--fetch`: 데이터 수집만 (발행 없음)
- launchd: `~/Library/LaunchAgents/com.aikorea24.auto-writer.plist` — 매일 09:00 1회 실행
  - plist는 `scripts/manual-publisher/.venv/bin/python3` 사용 (두 시스템이 같은 venv 공유)
  - `RunAtLoad`: false (예약 시간에만 실행)
- 하루 최대 **5개** 생성 + 발행 (`DAILY_QUOTA=5`, env로 재정의 가능)

**전체 파이프라인** (`pipeline.py:run()`):

| 단계 | 설명 | 코드 위치 |
|------|------|-----------|
| 1 | 오늘 quota 확인 (`today_count >= DAILY_QUOTA` 시 종료) | `pipeline.py:124-131` |
| 2 | pending 없으면 Gov24 + finlife + invest 3개 소스 재수집 | `pipeline.py:133-143` |
| 3 | 카테고리 가중치 기반 `pick_next_service()` 선택 (deficit 계산) | `pipeline.py:146-151` → `db_utils.py:90` |
| 3b | **부적합 키워드 필터** (42개, 6개 그룹) → match 시 `mark_error()` + skip | `pipeline.py:155-181` |
| 4 | NVIDIA NIM LLM으로 `generate_article()` (fallback 체인 4단계) | `pipeline.py:183-195` → `writer.py` |
| 4a | 맞춤법·문법 교정: `proofread()` (gemma-3n → deepseek-chat fallback) | `pipeline.py:197-198` → `writer.py:474` |
| 4b | LLM 출력에서 `# 제목` 추출, 없으면 서비스 title fallback | `pipeline.py:200-205` |
| 4c | `build_summary_box()` — H2 기반 목차 생성 (최대 6개) | `pipeline.py:207-210` |
| 4d | `insert_inline_ctas()` — 2개 CTA 삽입 (H2 #2 뒤, H2 #3 뒤) | `pipeline.py:212-213` |
| 5 | Reviewer 검수: Mimo Qwen2.5 14B → `needs_review` 플래그 | `pipeline.py:215-218` → `shared/reviewer.py` |
| 5b | Validator: CTA 강제 삽입, 헤딩·본문 길이 검증 (<800자 = BODY_TOO_SHORT) | `pipeline.py:220-229` → `validator.py` |
| 6 | `make_slug()` — NFC 정규화, 60자 제한, `-{service_id[-6:]}` 접미사 | `pipeline.py:231-232` → `validator.py:108` |
| 7 | `get_related_posts()` (internal_link_count 적은 3개) → `[RELATED_POSTS]` 치환 | `pipeline.py:234-238` |
| 8 | `gen_thumbnail()` — Pillow 800x800 + R2 업로드 | `pipeline.py:240-243` → `shared/thumbnail_gen.py` |
| 9 | `make_frontmatter()` — tags, description, frontmatter 조합 | `pipeline.py:245-256` |
| 10 | `{slug}.md` 저장 → `src/content/blog/` | `pipeline.py:258-262` |
| 11 | DB 기록: `services.status='published'` + `publish_ledger` INSERT | `pipeline.py:264-270` |
| 12 | 발행 건수 > 0 → `deploy()` (npm build + wrangler deploy) | `pipeline.py:272-283` |

**데이터 소스**:
| 소스 | 파일 | 설명 |
|------|------|------|
| Gov24 | `fetcher.py` | 공공데이터포털 gov24/v3/serviceList (DATA_GO_KR_API_KEY) |
| 금감원 finlife | `fetcher_loan_fin.py` | 정기예금/적금/주택담보대출/전세자금대출 (FINLIFE_API_KEY) |
| data.go.kr | `fetcher_invest.py` | ETF시세/지수시세 (DATA_GO_KR_API_KEY) |

**DB**: `scripts/auto-writer/db/auto-writer.db` (SQLite, 3개 테이블)
- `services`: 수집된 서비스 (service_id, title, category, field, summary, detail, target, persona, status, source 등)
- `publish_ledger`: 발행 기록 (service_id, slug, title, category, persona, model_used, internal_link_count, published_at)
- `fetch_meta`: 마지막 수집 시각 (last_fetched, total_fetched)

**상태 관리**:
- `services.status`: `pending` → `published` / `error` / `updated`
- `pick_next_service()`: 카테고리 가중치 기반 deficit 계산 → 가장 부족한 카테고리부터 선택
- `get_related_posts()`: `internal_link_count` 적은 글 우선 (링크 편중 방지)

**LLM 모델 - 생성**:
| 우선순위 | 모델 | timeout | max_retries | 비고 |
|----------|------|---------|-------------|------|
| 1 | `google/diffusiongemma-26b-a4b-it` | 120s | 2 | 메인 (실험모델, 품질 경고 → 자동 needs_review) |
| 2 | `google/gemma-4-31b-it` | 120s | 1 | 폴백 |
| 3 | `google/gemma-3n-e4b-it` | 90s | 1 | 폴백 |
| 4 | `deepseek-chat` (V4 Flash) | 180s | 2 | **최후 폴백** |

**LLM 모델 - 교정**:
| 우선순위 | 모델 | temperature |
|----------|------|-------------|
| 1 | `google/gemma-3n-e4b-it` | 0.0 |
| 2 | `deepseek-chat` | 0.0 |

**LLM 모델 - 리뷰어**: Unsloth Qwen2.5 14B (Mimo API, temperature=0.1, top_p=0.2)

**생성 파라미터**: `temperature=0.6, max_tokens=8192, top_p=0.9, frequency_penalty=0.3, presence_penalty=0.3`

**환경변수**:
- `NVIDIA_API_KEY`: NVIDIA NIM LLM API 키
- `DEEPSEEK_API_TOKEN` / `DEEPSEEK_API_KEY`: DeepSeek API 키 (proofread + 최후 폴백)
- `MIMO_API_KEY`: Reviewer Mimo API 키
- `DAILY_QUOTA`: 일일 발행 한도 (기본 5)
- `CF_R2_*`: R2 썸네일 업로드용
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`: ERROR/WARN 알림용
- `FINLIFE_API_KEY`: 금감원 API 키
- `DATA_GO_KR_API_KEY`: 공공데이터포털 API 키

**카테고리 가중치** (`config/category_map.yaml`):
```yaml
category_quota:
  loan:      0.40
  insurance: 0.25
  tax:       0.20
  invest:    0.10
  general:   0.05
```

**Gov24 분야 → 카테고리 매핑**:
| Gov24 field | category | 비고 |
|-------------|----------|------|
| 고용·창업 | general | |
| 주거·자립 | loan | |
| 보건·의료 | insurance | |
| 생활안정 | general | |
| 보육·교육 | general | |
| 임신·출산 | insurance | |
| 문화·환경 | general | |
| 보호·돌봄 | insurance | |
| 행정·안전 | general | |
| 농림축산어업 | `null` | 수집 단계에서 제외 |

**Finlife 상품 → 카테고리 매핑**: 정기예금/적금/주택담보대출/전세자금대출 → 모두 `loan`

**부적합 키워드 필터** (`pipeline.py:155-181`, `_EXCLUDE_KW`, 42개):
```python
# 농림·수산 (기존)
"농업","어업","축산","수산","임업","농림",
"천일염","포장재","동물","백신","가축",
"양식","어가","영농","농기계","비료","종자","사료","축사","수산물"

# 의료·질환
"한센","수술비","치매","백내장","임플란트",
"발달장애","학대피해","보호종료","가정폭력","북한이탈","귀화"

# 특수직군
"선원","어업인","항로표지","해양사고","초지","원산지검증","유휴간호사"

# 중독·법률
"금연","마약","결핵","진술조력인","국선변호사","법률홈닥터"

# 고위험·희귀
"고위험임산부","희귀질환","감염병격리","영양플러스","방문건강"

# 의료비·보조기기
"응시료","노인안검진","개안술","인공관절","장기요양","낙상방지","보조기기"
```
→ 6개 그룹, 총 42개 키워드. 글 생성 전 서비스 제목/요약에서 매치 시 skip.

**CTA 삽입 (3단계)**:
1. `pipeline.py` `insert_inline_ctas()`: H2 #2 뒤 peer CTA, H2 #3 뒤 stats CTA
2. `reviewer.py` `_ensure_markers()`: `[PERSONA_CTA]` / `[RELATED_POSTS]` 마커 보강
3. `validator.py` `validate_and_fix()`: 마커 부재 시 강제 삽입 + 실제 블록으로 치환

**썸네일 생성** (`shared/thumbnail_gen.py`):
- 800x800 JPG, AppleGothic 폰트
- 카테고리별 배경 이미지 풀 (public/bg_img/)
- 45% 어둡게 → 반투명 그라데이션 → 카테고리 배지 → 제목 (최대 3줄)
- R2 업로드: `blog-thumbnails/{slug}.jpg`

**income_series 시드**: `seeder_income.py` — persona-stats.json에서 "내 또래 연봉" 시리즈 34개 주제 생성

---

### 📥 manual-publisher (수동 인박스 발행)

**목적**: 사용자가 수동으로 작성/수집한 글을 `inbox/`에 넣으면 30분마다 감지하여 발행

**실행**: launchd (plist: `kr.aikorea24.manual-publisher`) → `watcher.py`가 1800초(30분) 간격으로 `publisher.run()` 호출
- **RunAtLoad**: true (시작 시 실행)
- **로그**: `logs/manual-publisher.log`
- **환경**: `.venv/bin/python3 publisher.py` (프로젝트 루트에서 실행)

**전체 파이프라인** (`publisher.py:run()`):

| 단계 | 설명 | 코드 위치 |
|------|------|-----------|
| 1 | `watcher.get_new_files()` → inbox/에서 새 `.md` 파일 감지 (done.json 기준 중복 제외) | `publisher.py:60` → `watcher.py:18` |
| 2 | `classifier.classify()` → 키워드 기반 카테고리 분류 (동점/0점 = general) | `publisher.py:68` → `classifier.py:11` |
| 3 | `transformer.transform()` → frontmatter 추출·변환·재조립 (date→pubDate, draft=false) | `publisher.py:75` → `transformer.py:77` |
| 4 | `validator.normalize_slug()` → 슬러그 정규화 (NFD→NFC, 공백→하이픈) | `publisher.py:79` → `validator.py:103` |
| 5 | `validator.validate_and_fix_content()` → frontmatter 타입 검증 + auto-fix | `publisher.py:80` → `validator.py:22` |
| 6 | **중복 제목 체크** — BLOG_DIR 내 기존 파일과 제목 비교 | `publisher.py:92-108` |
| 7 | `thumbnail.generate()` → 1024x1024 JPG + R2 업로드 | `publisher.py:111` → `thumbnail.py:53` |
| 8 | `entity_injector.inject()` → persona-entity 마커 + 동일 카테고리 관련글 콜아웃 | `publisher.py:113` → `entity_injector.py:42` |
| 9 | `resolve_dst_path()` → slug 충돌 시 `_2`, `_3` suffix | `publisher.py:118` → `publisher.py:35` |
| 10 | `src/content/blog/{slug}.md` 저장 → inbox/ → `inbox/YYYYMMDD/`로 이동 | `publisher.py:120-135` |
| 11 | `watcher.mark_done()` → done.json 기록 (published/duplicate_skip/error) | `publisher.py:125-135` → `watcher.py:32` |
| 12 | `deployer.build_and_deploy()` → npm build + wrangler deploy | `publisher.py:147` → `deployer.py` |

**슬러그 생성 규칙** (`transformer.py:70`):
- 파일명에서 `YYYYMMDD-HHMMSS-` 또는 `YYYYMMDD-` 프리픽스 제거
- `validator.normalize_slug()`: NFD→NFC, 공백→하이픈, 연속 하이픈 제거

**중요**: 이 시스템은 **사용자가 수동으로 선별한 파일**만 처리합니다.
- `inbox/`에 파일을 직접 넣는 것 = 발행 의사 표현
- `filter.py`는 **데드코드** (import만 되고 실제 호출되지 않음)
- `classifier.py`는 카테고리 판별만 함 (컨텐츠 필터링 아님)
- **이 시스템에는 컨텐츠 필터를 추가하지 말 것** — 사용자의 의도적 발행을 방해하면 안 됨

**done.json 포맷** (`watcher.py:32`):
```json
"YYYYMMDD-HHMMSS-...slug.md": {
  "status": "published" | "duplicate_skip" | "error",
  "recorded_at": "ISO-8601",
  "category": "insurance" | "invest" | "loan" | "tax" | "general",
  "slug": "...",
  "published_at": "ISO-8601",
  "reason": "error message"
}
```

**중복 체크** (`publisher.py:92-108`): BLOG_DIR 내 모든 `.md` 파일의 frontmatter `title`을 읽어 동일 제목 감지 → 중복 시 `duplicate_skip`

---

## 데이터 출처

| 데이터 | 위치 | 출처 |
|--------|------|------|
| 페르소나 통계 | `public/persona-stats.json` (2,244키) | Nemotron + KOSIS |
| 소득 추정 | `income` 객체 + `scripts/patch-income.mjs` | 통계청·국세청 |
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
- **경로 대소문자**: `scripts/manual-publisher/` 코드 일부에 `/Users/twinssn/projects/` (소문자) 경로 하드코딩 존재. macOS는 대소문자 미구분이므로 정상 동작하나, cross-platform 시 문제될 수 있음.
- **데이터 파일**: `benefits-clean.json`, `persona-stats.json` 등은 git에 없을 수 있음 (용량 문제).
- **Persona stat 키**: `functions/api/auth/callback/kakao.js`의 `env.KAKAO_REST_KEY`와 `login.astro`의 `import.meta.env.PUBLIC_KAKAO_REST_KEY`는 별개의 변수명. 값은 같지만 `PUBLIC_` prefix 유무 차이 있음.
- **provinceMap 없음**: `my-persona.astro` `selectProvince()`에 과거 `충북`→`충청북` 식의 매핑이 있었으나 제거됨. UI 버튼값 = 데이터 키값 = 짧은 이름.
- **하드코딩 Kakao Key 이력**: 초기 `callback/kakao.js`는 실제 Kakao REST Key가 하드코딩되어 있었음. 보안 강화 커밋(`4223f0a`)에서 `env.KAKAO_REST_KEY || '...'` fallback으로 변경, `04cc55e`에서 fallback 제거 → Cloudflare Pages Secret 필수화.
