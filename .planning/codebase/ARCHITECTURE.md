<!-- refreshed: 2026-07-01 -->
# Architecture

**Analysis Date:** 2026-07-01

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                  BUILD TIME (Astro SSG, npm run build)            │
├──────────────────────┬───────────────────────┬───────────────────┤
│  Static Pages        │  Persona Pages        │  Content Pages    │
│  `src/pages/*.astro` │  `persona/[...slug]`  │  `blog/*.astro`   │
│  (index, about, etc) │  (2,244 routes)        │  + `nomad/*.astro`│
│  Build-time rendered │  getStaticPaths()     │  Astro content     │
│  from .astro + .md   │  reads persona-stats  │  collections       │
└──────────┬───────────┴───────────┬───────────┴──────────┬────────┘
           │                       │                      │
           ▼                       ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                         DIST (Static Output)                      │
│         `./dist/` — HTML/CSS/JS/JSON served by Cloudflare Pages  │
│         Cloudflare 25MiB file limit: persona-stats.json removed  │
└───────────┬──────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│               RUNTIME (Cloudflare Pages Functions)                │
├────────────────────┬────────────────────┬────────────────────────┤
│ Community API      │ Auth API           │ Redirects / Proxies    │
│ CRUD posts,        │ Kakao OAuth login  │ OG → cards redirect   │
│ comments, likes    │ logout             │ Community SPA passthru │
│ D1: persona-db     │ HMAC-SHA256 session│                        │
└────────────────────┴────────────────────┴────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                     │
│ Cloudflare D1 (`persona-db`)                                      │
│ Tables: users, persona_posts, persona_comments, persona_likes,    │
│         benefit_clicks                                             │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Persona pages | Build 2,244 static HTML persona pages with stats, benefits, wages | `src/pages/persona/[...slug].astro` |
| My Persona | Client-side SPA: multi-step input → results | `src/pages/my-persona.astro` |
| Blog pages | Static blog posts from Astro content collections | `src/pages/blog/[...slug].astro` |
| Blog index | Category-filtered blog listing | `src/pages/blog/index.astro` |
| Community SPA | Client-rendered community (SSG shell + JS fetch) | `src/pages/community/index.astro` |
| Community API | CRUD for posts, comments, likes (D1-backed) | `functions/api/community/*.js` |
| Auth | Kakao OAuth callback, session creation, logout | `functions/api/auth/*.js` |
| Session | HMAC-SHA256 token creation/verification | `functions/api/_shared/session.js` |
| Auto-writer | AI blog content generation pipeline (NVIDIA NIM) | `scripts/auto-writer/pipeline.py` |
| Manual-publisher | User-inbox blog publishing pipeline | `scripts/manual-publisher/publisher.py` |
| Benefit matcher | Score-based benefit-welfare matching | `src/lib/benefitMatcher.ts` |
| Welfare matcher | Region/life-stage welfare matching | `src/lib/welfareMatcher.ts` |
| BaseHead | Global <head> with OG, GA4, AdSense, fonts | `src/components/BaseHead.astro` |
| Header | Navigation + session_ui cookie parsing | `src/components/Header.astro` |

## Pattern Overview

**Overall:** Static Site Generation (SSG) with Cloudflare Pages Functions for dynamic API endpoints

The system is fundamentally split into two layers:
1. **Build time (SSG):** All Astro pages are rendered to static HTML during `npm run build`. Frontmatter runs at build time — no SSR.
2. **Runtime:** Cloudflare Pages Functions handle dynamic operations: community CRUD, Kakao OAuth, like/click tracking, and URL redirects.

**Key Characteristics:**
- `output: 'static'` — every `.astro` frontmatter script executes during build, not per request
- Cloudflare D1 (`persona-db`) used only for dynamic features (community, auth, analytics)
- All persona statistics, benefit data, and blog content loaded at build time from static JSON/MD files
- Community pages use client-rendered SPA pattern: Astro provides an HTML shell, JavaScript fetches data from Functions API

## Layers

**Static Frontend (Astro SSG):**
- Purpose: Render all public-facing pages as static HTML
- Location: `src/pages/`
- Contains: Astro pages (`.astro`, `.md`, `.mdx`), RSS/JSON endpoints
- Depends on: `src/lib/` (matchers), `src/data/` (wage tables), `public/` (JSON datasets), `src/content/` (blog/nomad collections)
- Used by: Cloudflare Pages (serves `./dist/` directly)

**Cloudflare Functions API:**
- Purpose: Dynamic operations requiring server-side execution
- Location: `functions/`
- Contains: Community CRUD, Kakao OAuth, click tracking, URL redirects
- Depends on: Cloudflare D1 (`DB` binding), `KAKAO_REST_KEY`, `SESSION_SECRET` secrets
- Used by: Community SPA pages (client-side JS fetch), Login/logout flows

**Content Generation Pipelines:**
- Purpose: Automatically create blog content from external data sources
- Location: `scripts/auto-writer/` and `scripts/manual-publisher/`
- Contains: Python data fetchers, LLM content generators, build+deploy orchestrators
- Depends on: NVIDIA NIM API, Kakao/Dgov APIs, Cloudflare R2, Cloudflare wrangler
- Outputs to: `src/content/blog/*.md`

## Data Flow

### Primary Request Path (Static Page)

1. User requests `/persona/서울-남자-35/` → Cloudflare Pages serves pre-built HTML from `./dist/`
2. Build-time (`getStaticPaths()`): reads `public/persona-stats.json`, `public/benefits-clean.json`, `public/benefits-curated.json`, `public/blog-match.json`, `src/data/wage-table.json`, `src/data/job-category-map.json`, `src/data/decision-cards.json`
3. Each persona page has benefits & welfare pre-matched at build time
4. Card images served from `https://cards.persona.aikorea24.kr/` (external CDN)
5. Client-side JS handles: Kakao share, URL copy, dark mode toggle, visitor counter

### Community SPA Flow

1. User navigates to `/community/` → pre-built shell page loads
2. Client-side JS: fetches `GET /api/community/posts?board=persona` → renders post list
3. User writes post → `POST /api/community/posts` → HMAC-SHA256 session validated → D1 insert
4. Post detail: `/community/123` → `community/[id].js` proxied through `functions/community/[id].js`

### OAuth Login Flow

1. `login.astro`: generates CSRF state → sets `oauth_state` cookie (Max-Age=600)
2. Kakao OAuth redirect → `callback/kakao.js`: validates state (CSRF), exchanges code for token
3. Fetches Kakao user info, upserts user in D1, creates HMAC-SHA256 session token
4. Sets `session` cookie (HttpOnly, Secure, SameSite=Strict, 7 days) + `session_ui` cookie (non-HttpOnly for UI)

### Auto-Writer Pipeline

1. `scheduler.py` triggered by launchd daily at 09:00
2. Fetches Gov24/finlife/invest data → stores in `services` table (SQLite)
3. `pick_next_service()`: category deficit calculation → picks most-needed service
4. Filters 42 excluded keywords → LLM generates article (NVIDIA NIM, 4-tier fallback chain)
5. Review (Qwen2.5 14B) → validate → thumbnail gen (R2 upload) → `{slug}.md` → `npm run build` → wrangler deploy

### Manual-Publisher Pipeline

1. `watcher.py` polls `inbox/` every 30 minutes (launchd)
2. Classifies category → transforms frontmatter → validates → checks duplicate titles
3. Generates thumbnail → injects persona entities → `{slug}.md` → `npm run build` → wrangler deploy

### Benefits Matching Flow

1. `public/benefits-clean.json` + `public/benefits-curated.json` loaded at build time
2. `benefitMatcher.ts` scores each benefit against persona (age, sex, region, category)
3. Filters out `not_eligible` → sorts by curated-first, score-desc → returns top 8
4. Same pattern for welfare matching via `welfareMatcher.ts` (region + life stage)

**State Management:**
- Build-time: No state — everything computed from static files at build
- Runtime: D1 database for auth sessions, community posts, likes, comments, click tracking
- Client: `session_ui` cookie for login state display; `localStorage` for theme preference

## Key Abstractions

**Persona Key:**
- Purpose: Uniquely identifies a persona demographic bucket
- Format: `{region}_{sex}_{age}` — e.g., `서울_남자_35`
- URL representation: `{region}-{sex}-{age}` — e.g., `/persona/서울-남자-35/`
- Data sources: `public/persona-stats.json` (2,244 keys, full), `public/persona-stats-decade.json` (204 decade keys)

**Benefit Matching System:**
- Purpose: Score-based eligibility matching between persona and government benefits
- Location: `src/lib/benefitMatcher.ts`
- Pattern: Scoring function with hard filters (age, sex, region) + soft scoring (curation, category bonus, warnings)
- Output: `BenefitMatch[]` with `matchStatus: 'eligible_likely' | 'needs_check' | 'not_eligible'`

**Content Collections:**
- Purpose: Zod-schema validated blog/nomad content
- Location: `src/content/` with `src/content.config.ts` schema
- Collections: `blog` (insurance/invest/loan/tax/general), `nomad` (digital nomad guides)
- Schema: title, description, draft (default true), pubDate, category, tags, needs_review, etc.

## Entry Points

**Main Entry (Astro Pages):**
- Location: `src/pages/`
- Triggers: Build-time rendering
- Responsibilities: Generate all static HTML pages

**Community API:**
- Location: `functions/api/community/posts.js`, `comments.js`, `like.js`
- Triggers: HTTP requests from client-side JS
- Responsibilities: CRUD for community features, requires session auth for writes

**Auth API:**
- Location: `functions/api/auth/callback/kakao.js`, `logout.js`
- Triggers: OAuth redirect, logout clicks
- Responsibilities: Kakao token exchange, session creation/destruction

**Auto-Writer:**
- Location: `scripts/auto-writer/scheduler.py`, `pipeline.py`
- Triggers: launchd daily at 09:00
- Responsibilities: Fetch data → generate LLM articles → build → deploy

**Manual-Publisher:**
- Location: `scripts/manual-publisher/watcher.py`, `publisher.py`
- Triggers: launchd every 30 minutes
- Responsibilities: Detect inbox files → process → build → deploy

## Architectural Constraints

- **Threading:** Single-threaded event loop (Node.js); Python pipelines are sequential
- **Global state:** `public/persona-stats.json` is the central data dependency — all 2,244 persona pages depend on it at build time. `scripts/auto-writer/db/auto-writer.db` is a SQLite file with pipeline state
- **File size limits:** Cloudflare Pages has a 25 MiB per-file limit. `persona-stats.json` (~25 MiB) exceeds this and must be removed from `dist/` before deploy (done in `deploy.sh:52`, `build_deploy.py:22`). A subset `persona-stats-decade.json` (~4 MiB) is used at runtime by `my-persona.astro`
- **Static mode limitation:** All data fetching in Astro frontmatter happens only at build time. New blog posts require a rebuild and redeploy to appear
- **External card images:** Persona card images are hosted on a separate subdomain (`cards.persona.aikorea24.kr`) — not served from this project's Cloudflare Pages

## Anti-Patterns

### Hardcoded Absolute Paths

**What happens:** Both Python pipelines hardcode absolute filesystem paths (`/Users/twinssn/Projects/money-aikorea24/...`)
**Why it's wrong:** Not portable — will break if cloned to a different machine or username
**Files:** `scripts/auto-writer/pipeline.py:9`, `scripts/auto-writer/shared/build_deploy.py:7`, `scripts/manual-publisher/publisher.py:19`, `scripts/manual-publisher/deployer.py:10`, `scripts/deploy.sh:5`
**Do this instead:** Use `__file__`-relative or environment-variable-based paths

### Inconsistent Lowercase Path in manual-publisher

**What happens:** `scripts/manual-publisher/publisher.py:19` uses `projects` (lowercase) while the actual path is `Projects` (uppercase) on macOS
**Why it's wrong:** Works on macOS (case-insensitive filesystem) but would break on Linux/CI
**Do this instead:** Use `os.path.dirname(os.path.abspath(__file__))` to derive paths

### Dead Code: filter.py in manual-publisher

**What happens:** `scripts/manual-publisher/filter.py` exists, is imported in `publisher.py` as `filter as finance_filter`, but the `finance_filter` object is never called in the pipeline
**Why it's wrong:** Misleading import, increases cognitive load
**Do this instead:** Remove the unused import

### .bak File Clutter

**What happens:** Multiple `.bak` and `.bak.*` backup files scattered throughout `src/pages/persona/`, `src/pages/community/`, `src/pages/`, `src/components/`, `src/layouts/`, `functions/`
**Why it's wrong:** Makes directory navigation noisy, could be confused with active files
**Files:** 30+ `.bak` files across `src/pages/persona/` (10), `src/pages/community/` (6), `src/pages/blog/` (0), `src/components/` (8), `src/layouts/` (2), `functions/` (5+)
**Do this instead:** Delete or move to a `.trash/` directory

## Error Handling

**Strategy:**
- **Build time:** Astro build fails if content collection schemas are violated. The manual-publisher includes auto-fix retry logic (2 attempts with frontmatter repair)
- **Runtime:** Cloudflare Functions use try-catch blocks with JSON error responses. Session auth returns 401; forbidden actions return 403
- **Pipeline:** Auto-writer has `mark_error()` status for failed services; Telegram notifications for critical failures

**Patterns:**
- API endpoints return `{ error: "message" }` with appropriate HTTP status codes
- Session validation uses `timingSafeEqual()` to prevent timing attacks
- OAuth state validation prevents CSRF
- Open redirect protection via `safeNext` check in `callback/kakao.js`

## Cross-Cutting Concerns

**Logging:**
- Auto-writer pipeline: `RotatingFileHandler` (5MB, 3 backups) + stdout
- Manual-publisher: Print statements + Telegram notifications for failures
- Cloudflare Functions: No logging framework — errors surface in Cloudflare dashboard

**Validation:**
- Content collections: Zod schemas in `src/content.config.ts`
- API inputs: Length limits on title (100), content (5000), comments (2000)
- Pipeline validator: frontmatter type validation, CTA presence, body length checks

**Authentication:**
- Kakao OAuth 2.0 with HMAC-SHA256 session tokens
- Two cookies: `session` (HttpOnly, Secure, SameSite=Strict) and `session_ui` (non-HttpOnly, for JS UI state)
- CSRF protection via `oauth_state` cookie + state parameter comparison

---

*Architecture analysis: 2026-07-01*
