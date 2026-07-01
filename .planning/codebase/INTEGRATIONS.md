# External Integrations

**Analysis Date:** 2026-07-01

## APIs & External Services

### LLM / AI APIs (auto-writer pipeline)

**NVIDIA NIM API** — Primary article generation, proofreading
- **Purpose:** Generate blog articles via NVIDIA NIM LLM models (OpenAI-compatible API)
- **Base URL:** `https://integrate.api.nvidia.com/v1`
- **Auth:** `NVIDIA_API_KEY` env var
- **Client:** OpenAI SDK (`from openai import OpenAI`)
- **Models used:**
  - `google/diffusiongemma-26b-a4b-it` (main, 120s timeout, 2 retries) — experimental, triggers `needs_review`
  - `google/gemma-4-31b-it` (fallback 1, 120s timeout, 1 retry)
  - `google/gemma-3n-e4b-it` (fallback 2, 90s timeout, 1 retry) — also used for proofreading
- **Generation params:** `temperature=0.6, max_tokens=8192, top_p=0.9, frequency_penalty=0.3, presence_penalty=0.3`
- **Proofread params:** `temperature=0.0`

**DeepSeek API** — Final fallback generation + proofreading fallback
- **Purpose:** Fallback when all NVIDIA NIM models fail; also used as proofreading fallback
- **Base URL:** `https://api.deepseek.com/v1`
- **Auth:** `DEEPSEEK_API_TOKEN` or `DEEPSEEK_API_KEY` env var
- **Client:** OpenAI SDK
- **Model:** `deepseek-chat` (V4 Flash, 180s timeout, 2 retries)
- **Proofread params:** `temperature=0.0`

**Mimo API (Reviewer)** — Content quality review
- **Purpose:** Reviews generated articles for quality, flags `needs_review`, ensures CTA/related-post markers
- **Base URL:** `https://api.mimo.kr/v2_5/complete`
- **Auth:** `MIMO_API_KEY` env var
- **Model:** Unsloth Qwen2.5 14B
- **Params:** `temperature=0.1, top_p=0.2`
- Used by: `scripts/auto-writer/shared/reviewer.py`

### Authentication

**Kakao OAuth 2.0** — User login
- **Purpose:** Social login for community features
- **Auth URL:** `https://kauth.kakao.com/oauth/authorize`
- **Token URL:** `https://kauth.kakao.com/oauth/token`
- **User Info URL:** `https://kapi.kakao.com/v2/user/me`
- **Redirect URI:** `https://persona.aikorea24.kr/api/auth/callback/kakao`
- **Env vars:** `KAKAO_REST_KEY` (client_id), `KAKAO_CLIENT_SECRET`
- **CSRF protection:** `oauth_state` cookie (Max-Age=600), server-side state vs cookie comparison
- **Open Redirect defense:** Only relative URLs starting with `/` allowed for redirect target
- **Files:**
  - `functions/api/auth/callback/kakao.js` — OAuth callback handler
  - `src/pages/auth/login.astro` — Login page (uses `import.meta.env.PUBLIC_KAKAO_REST_KEY` — note: different variable name from Functions' `env.KAKAO_REST_KEY`)

**Session Management** — Post-authentication
- **Mechanism:** HMAC-SHA256 signed session tokens
- **Secret:** `SESSION_SECRET` env var (required Cloudflare Pages Secret)
- **Token format:** `base64url(payload).base64url(signature)`
- **Cookies:**
  - `session` — HttpOnly, Secure, SameSite=Strict, 7 day expiry (for server-side auth)
  - `session_ui` — non-HttpOnly, base64-encoded JSON with `{id, name}` (for UI display)
- **Timing-safe comparison:** Custom `timingSafeEqual()` prevents timing attacks
- **Files:**
  - `functions/api/_shared/session.js` — Token creation, verification, cookie parsing
  - `src/components/Header.astro` — Parses `session_ui` cookie for UI state

### Government/Financial Data APIs

**Gov24 (공공데이터포털)** — Government service listings
- **Purpose:** Source for auto-writer blog article generation (welfare benefits)
- **Base URL:** `https://api.odcloud.kr/api/gov24/v3/serviceList`
- **Auth:** `DATA_GO_KR_API_KEY` env var (query param `serviceKey`)
- **Rate/Fetch:** Paginated fetch (100 items/page), all services collected
- **Field mapping:** 10 gov24 fields → 4 blog categories (`loan`, `insurance`, `general`, or excluded)
- **Files:** `scripts/auto-writer/fetcher.py`

**금감원 FinLife (금융감독원)** — Financial product data
- **Purpose:** Source for loan/interest rate articles (savings deposits, mortgages, rental loans)
- **Base URL:** `https://finlife.fss.or.kr/finlifeapi`
- **Auth:** `FINLIFE_API_KEY` env var
- **Endpoints:**
  - `savingProductsSearch.json` — savings deposits (정기예금/적금)
  - `mortgageLoanProductsSearch.json` — mortgage loans (주택담보대출)
  - `rentHouseLoanProductsSearch.json` — rental loans (전세자금대출)
- **Products:** 4 types, all mapped to `loan` category
- **Files:** `scripts/auto-writer/fetcher_loan_fin.py`

**data.go.kr (공공데이터포털)** — Market index data
- **Purpose:** Source for invest/market articles (KOSPI, KOSDAQ, index data)
- **Base URL:** `http://apis.data.go.kr/1160100/service/GetMarketIndexInfoService`
- **Auth:** `DATA_GO_KR_API_KEY` env var (same key as Gov24)
- **Service:** `getStockMarketIndex`
- **Major indices tracked:** 14 indices (KOSPI, KOSDAQ, KOSPI 200, etc.)
- **Files:** `scripts/auto-writer/fetcher_invest.py`

## Data Storage

### Cloudflare D1 (Production Database)
- **Database:** `persona-db`
- **Binding:** `DB` (configured in `wrangler.toml`)
- **Tables:**
  - `users` — User accounts (kakao_id, email, name, nickname, avatar, provider, marketing_consent, agreed_at)
  - `persona_posts` — Community posts (title, content, board_type, persona_slug, views, likes)
  - `persona_comments` — Comments on posts (post_id, user_id, content)
  - `persona_likes` — Like/unlike tracking (post_id, user_id)
  - `benefit_clicks` — Benefit click analytics (benefit_id, count, updated_at)
- **Access:** Cloudflare Pages Functions via `env.DB` binding (D1 driver API: `prepare().bind().run()` / `.first()` / `.all()`)

### SQLite (Local Development)
- **File:** `scripts/auto-writer/db/auto-writer.db`
- **Tables:**
  - `services` — Collected service records (service_id, title, category, status, persona, etc.)
  - `publish_ledger` — Publication history (service_id, slug, title, category, model_used, internal_link_count)
  - `fetch_meta` — Last fetch timestamp (last_fetched, total_fetched)
- Used exclusively by the auto-writer pipeline (not deployed to production)

### File Storage

**Cloudflare R2** — Blog thumbnail storage
- **Bucket:** `hotissue-images`
- **Endpoint:** `https://{account_id}.r2.cloudflarestorage.com`
- **Public URL:** `https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails`
- **Access:** boto3 (S3-compatible API, signature v4)
- **Cache:** `public, max-age=31536000, immutable` (1 year)
- **Env vars:** `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT`, `R2_ACCOUNT_ID`
- **Files:**
  - `scripts/auto-writer/shared/thumbnail_gen.py` — Generates 800x800 JPG, uploads to R2
  - `scripts/manual-publisher/r2_upload.py` — S3-compatible R2 upload client
  - `scripts/manual-publisher/thumbnail.py` — Generates 1024x1024 JPG, uploads via r2_upload

### Caching
- **Not detected** — No Redis, KV, or CDN-level cache configuration

## Monitoring & Observability

**Telegram Bot** — Error/Warning notification (auto-writer + manual publisher)
- **Purpose:** Sends `ERROR` and `WARN` level alerts from the content pipelines
- **API:** `https://api.telegram.org/bot{TOKEN}/sendMessage`
- **Env vars:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **Policy:** `INFO` → local log only; `WARN` → immediate send; `ERROR` → immediate send
- **Formatted as Markdown** with emoji prefixes (🚨 ERROR, ⚠️ WARN, ✅ INFO)
- **Files:**
  - `scripts/auto-writer/shared/notifier.py` — Telegram sender for auto-writer
  - `scripts/manual-publisher/deployer.py` — Telegram sender for manual publisher (has its own inline sender)

**Logging:**
- **Rotating file handler** — 5 MiB per file, 3-5 backup files
- **Log locations:**
  - `scripts/auto-writer/logs/pipeline.log`
  - `scripts/auto-writer/logs/scheduler.log`
  - `scripts/manual-publisher/logs/manual-publisher.log`
- **Console:** Logging also outputs to stdout/stderr
- Centralized production logging: Not configured

## CI/CD & Deployment

**Hosting:**
- **Cloudflare Pages** — project `money-aikorea24`, production branch `main`
- Domain: `https://persona.aikorea24.kr`
- Build command: `npm run build`
- Build output: `./dist`

**CI Pipeline:**
- **None** — No GitHub Actions, no external CI
- Deployment triggered by:
  - `launchd` schedulers (auto-writer daily at 09:00, manual-publisher every 30 min)
  - Manual `npm run deploy` → `scripts/deploy.sh`
- **Pre-deploy Secrets check:** `deploy.sh` validates 3 Cloudflare Secrets exist before building (pre-check fails fast)

**Secrets Management:**

**Cloudflare Pages Secrets** (required for production Functions runtime):
| Secret | Used by | Purpose |
|--------|---------|---------|
| `KAKAO_REST_KEY` | `functions/api/auth/callback/kakao.js` | Kakao OAuth client_id |
| `KAKAO_CLIENT_SECRET` | `functions/api/auth/callback/kakao.js` | Kakao OAuth client_secret |
| `SESSION_SECRET` | `functions/api/_shared/session.js` | HMAC-SHA256 session signing key |

**Local `.env` variables** (used by build scripts and Python pipelines):
| Variable | Required | Purpose |
|----------|----------|---------|
| `PUBLIC_KAKAO_REST_KEY` | Yes (build) | Astro public env for login page |
| `NVIDIA_API_KEY` | Yes (auto-writer) | NVIDIA NIM API key |
| `DEEPSEEK_API_TOKEN` or `DEEPSEEK_API_KEY` | Yes (auto-writer) | DeepSeek API key |
| `MIMO_API_KEY` | Yes (auto-writer) | Mimo reviewer API key |
| `DATA_GO_KR_API_KEY` | Yes (auto-writer) | Gov24 + data.go.kr API key |
| `FINLIFE_API_KEY` | Yes (auto-writer) | FinLife API key |
| `TELEGRAM_BOT_TOKEN` | Yes (auto-writer) | Telegram notification bot |
| `TELEGRAM_CHAT_ID` | Yes (auto-writer) | Telegram notification target |
| `DAILY_QUOTA` | No (default 5) | Max daily auto-published articles |
| `CLOUDFLARE_API_TOKEN` | Yes (deploy) | Wrangler deployment auth |
| `CLOUDFLARE_ACCOUNT_ID` | Yes (deploy) | Cloudflare account identifier |
| `R2_ACCESS_KEY_ID` | Yes (thumbnails) | R2 S3-compatible access key |
| `R2_SECRET_ACCESS_KEY` | Yes (thumbnails) | R2 S3-compatible secret key |
| `R2_BUCKET_NAME` | Yes (thumbnails) | R2 bucket for blog thumbnails |
| `R2_ENDPOINT` | Yes (thumbnails) | R2 S3 endpoint URL |
| `R2_ACCOUNT_ID` | Yes (thumbnails) | R2 account identifier |
| `KOSIS_API_KEY` | Conditional | KOSIS statistics API key (fallback) |

**Global `.env.common` (`~/`):**
- `CLOUDFLARE_ACCOUNT_ID`, `TELEGRAM_BOT_TOKEN`, `DATA_GO_KR_API_KEY`, `R2_ACCESS_KEY_ID`, etc.
- Shared across projects; project `.env` values override `.env.common`

## Webhooks & Callbacks

**Incoming:**
- **Kakao OAuth callback** — `GET https://persona.aikorea24.kr/api/auth/callback/kakao`
- CSRF-protected via `oauth_state` cookie exchange

**Outgoing:**
- Not detected

## Key Integration Flows

### Auto-Writer Article Pipeline (daily)
```
Gov24 API ──┐
FinLife API ─┼──→ fetchers → SQLite (services table) → pick_next_service()
data.go.kr ─┘                                                      │
                   ┌───────────────────────────────────────────────┘
                   ↓
        NVIDIA NIM (diffusiongemma/Gemma) ← fallback → DeepSeek
                   │
                   ↓
        Mimo Reviewer (Qwen2.5 14B)
                   │
                   ↓
        Thumbnail gen (Pillow) → R2 upload (boto3)
                   │
                   ↓
        Article saved to src/content/blog/
                   │
                   ↓
        npm run build → wrangler pages deploy
                   │
                   ↓
        Telegram notification (success/failure)
```

### Authentication Flow
```
User → login.astro → Kakao Auth URL → User consents → redirect to callback/kakao.js
                                                                         │
                                    ┌── CSRF: oauth_state cookie check ←─┘
                                    │
                                    ↓
                              Kakao token exchange (POST /oauth/token)
                                    │
                                    ↓
                              Kakao user info (GET /v2/user/me)
                                    │
                                    ↓
                              D1: upsert users table
                                    │
                                    ↓
                              HMAC-SHA256 session token → 2 cookies
                              (session: HttpOnly, session_ui: non-HttpOnly)
                                    │
                                    ↓
                              302 redirect to /community
```

---

*Integration audit: 2026-07-01*
