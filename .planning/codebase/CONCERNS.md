# Codebase Concerns

**Analysis Date:** 2026-07-01

## Tech Debt

### Hardcoded Absolute Paths (19+ files)

**Issue:** All Python scripts in `scripts/auto-writer/` and `scripts/manual-publisher/` use absolute paths hardcoded to the developer's machine (`/Users/twinssn/Projects/money-aikorea24/...`). This makes the code non-portable — it will break on any other machine or CI environment.

**Files:**
- `scripts/manual-publisher/publisher.py:19` — `BLOG_DIR = "/Users/twinssn/projects/money-aikorea24/src/content/blog"`
- `scripts/manual-publisher/watcher.py:5` — `BLOGSMITH_OUTPUT = "/Users/twinssn/projects/money-aikorea24/inbox"`
- `scripts/manual-publisher/entity_injector.py:4` — `BLOG_DIR = "/Users/twinssn/projects/money-aikorea24/src/content/blog"`
- `scripts/manual-publisher/thumbnail.py:8-9` — `THUMBNAIL_DIR`, `BG_DIR`
- `scripts/manual-publisher/deployer.py:10` — `PROJECT_DIR = "/Users/twinssn/projects/money-aikorea24"`
- `scripts/auto-writer/pipeline.py:9` — `BLOG_DIR = "/Users/twinssn/Projects/money-aikorea24/src/content/blog"`
- `scripts/auto-writer/fetcher.py:6`, `scheduler.py:17`, `writer.py:6`, `pipeline.py:6`, `fetcher_invest.py:6`, `fetcher_loan_fin.py:6` — all have `load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")`
- `scripts/auto-writer/shared/thumbnail_gen.py:9` — `"/Users/twinssn/Projects/money-aikorea24/public/bg_img"`
- `scripts/auto-writer/shared/build_deploy.py:7` — `PROJECT_DIR = "/Users/twinssn/Projects/money-aikorea24"`
- `scripts/auto-writer/shared/reviewer.py:4` — `load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")`

**Impact:** Code is non-portable. Cannot run on any other machine, CI runner, or deployment without modifying source files. macOS case-insensitivity masks the inconsistency (`projects/` vs `Projects/`).

**Fix approach:** Replace all hardcoded paths with:
1. A shared `PROJECT_ROOT` computed from `__file__` or `Path(__file__).resolve().parent`
2. Use `os.getenv()` or `dotenv` for path overrides
3. Create a `scripts/paths.py` utility that all scripts import

---

### Massive Code Duplication: auto-writer/shared vs manual-publisher

**Issue:** Two parallel content generation pipelines (`scripts/auto-writer/` and `scripts/manual-publisher/`) maintain separate, near-identical copies of several modules:

| Function | auto-writer (shared/) | manual-publisher |
|----------|----------------------|-------------------|
| Thumbnail generation | `shared/thumbnail_gen.py` (143 lines) | `thumbnail.py` (131 lines) |
| R2 upload | Inline in `thumbnail_gen.py` | `r2_upload.py` (73 lines) |
| Deploy/build | `shared/build_deploy.py` (42 lines) | `deployer.py` (270 lines) |
| Telegram notification | `shared/notifier.py` (56 lines) | Inline in `deployer.py` |
| Review/validation | `shared/reviewer.py` | `validator.py` |

**Impact:** ~600 lines of duplicated logic. Bug fixes must be applied in two places. The manual-publisher deployer (270 lines) has substantially more logic (auto-fix, Telegram alerts, build error parsing) than the auto-writer deployer (42 lines), suggesting one diverged from the other.

**Fix approach:** Extract shared code into `scripts/shared/` with common modules for:
- Thumbnail generation (parameterize SIZE/quality)
- Build & deploy
- Telegram notifications
- R2 upload

---

### Dead Code: `scripts/manual-publisher/filter.py`

**Issue:** `filter.py` is imported in `publisher.py:22` (`import filter as finance_filter`) but **never called**. The `finance_filter` variable is unused. AGENTS.md confirms it is dead code.

**Files:** `scripts/manual-publisher/filter.py` (imported but unused), `scripts/manual-publisher/publisher.py:22`

**Impact:** Misleading code structure. The import suggests a filtering step that doesn't exist, confusing future maintainers.

**Fix approach:** Remove the unused import from `publisher.py` and optionally delete `filter.py` (or keep if planned for future use).

---

### `.bak` Files Committed to Repository (10 files)

**Issue:** Ten `.bak` backup files are present in the repo, cluttering the codebase.

**Files:**
- `src/pages/community/[id].astro.bak`
- `src/pages/my-persona.astro.bak`
- `src/pages/persona/[...slug].astro.bak`
- `src/pages/index.astro.bak`
- `src/components/Header.astro.bak`
- `functions/og/index.js.bak`
- `functions/api/auth/callback/kakao.js.bak`
- `scripts/generate-missing-cards.mjs.bak`
- `scripts/deploy.sh.bak`
- `scripts/manual-publisher/deployer.py.bak`

**Impact:** Codebase noise. Files can be regenerated from git history if needed. Backup files create confusion about which is the active version.

**Fix approach:** Add `*.bak` to `.gitignore` and delete all `.bak` files.

---

### `.ssr-backup/` Directory Committed

**Issue:** A `/.ssr-backup/` directory exists in the repository root containing backup copies of several source files (`login.astro`, `community/[id].astro`, `community/write.astro`, `api/` subdirectories).

**Files:** `/.ssr-backup/` (entire directory tree)

**Impact:** Same as `.bak` files — stale backup copies create confusion. Appears to be from an SSR migration attempt that was abandoned.

**Fix approach:** Add `.ssr-backup/` to `.gitignore` and delete the directory.

---

### `__pycache__` Directories Committed (24 `.pyc` files)

**Issue:** Python bytecode cache files are present in the repository under `scripts/auto-writer/__pycache__/`, `scripts/manual-publisher/__pycache__/`, and `scripts/__pycache__/`.

**Impact:** Unnecessary binary files in version control. Waste of repository size.

**Fix approach:** Add `__pycache__/` to `.gitignore` and remove tracked `__pycache__/` directories.

---

### `generate_post.py` Contains Unresolved TODO Placeholders

**Issue:** `scripts/generate_post.py` — a template generator script — contains literal TODO strings that would produce broken content if executed:

```
Line 151: "**TODO: 기본 개념 내용 작성**"
Line 159: "**TODO: 일반 조건 분석 내용 작성**"
Line 163: "**TODO: 특수 조건 분석 내용 작성**"
Line 167: "**TODO: 신청 절차 단계별 작성**"
Line 183: "**TODO: 핵심 요약 및 독자가 지금 당장 취할 행동 1가지 작성**"
Line 185: "오늘 할 수 있는 첫 번째 행동은 TODO 입니다."
```

**Files:** `scripts/generate_post.py:151,159,163,167,183,185`

**Impact:** If this script is run without proper data injection, it will publish blog posts containing literal "TODO" text, damaging site credibility.

**Fix approach:** Add validation that prevents publishing if any `TODO` remains in the output, or convert to a proper error mechanism.

---

### Duplicate Background Images in `public/bg_img/`

**Issue:** AGENTS.md notes 38 unique background images but 41 files — meaning 3 duplicate files exist.

**Location:** `public/bg_img/`

**Impact:** Wasted storage. Unclear which files are canonical.

**Fix approach:** Identify and remove duplicates. Use checksum comparison.

---

### AdSense Client ID Hardcoded in 12+ Locations

**Issue:** The Google AdSense publisher ID `ca-pub-5938862195544185` is hardcoded directly in multiple Astro components and pages instead of being in an environment variable.

**Files (examples):**
- `src/components/BaseHead.astro:66`
- `src/pages/persona/[...slug].astro:322`
- `src/pages/community/write.astro:8`
- `src/pages/community/[id].astro:241`
- `src/pages/community/index.astro:324`
- `src/pages/benefits/index.astro:394`
- `src/pages/my-persona.astro:271,283,308`
- `src/layouts/BlogPost.astro:357,383,408`

**Impact:** To change the AdSense account (e.g., for different environments or if publisher ID changes), every file must be updated individually. This is a configuration concern rather than a security one (AdSense client IDs are public by design).

**Fix approach:** Define `PUBLIC_ADSENSE_CLIENT` in `src/consts.ts` and reference it everywhere.

---

### Content Generation Pipeline Has 6 Independent TODO Placeholders

**Issue:** Same as above — these are distinct TODOs embedded in template strings.

**Files:** `scripts/generate_post.py`

**Impact:** Could generate broken blog posts if the pipeline ever uses this script without filling placeholders.

**Fix approach:** Add a validation check — if any TODO pattern remains in the generated content after template rendering, abort publication.

---

### AdSense Ad Slot IDs Left Empty

**Issue:** Two pages have TODO comments for empty AdSense ad slot IDs.

**Files:**
- `src/pages/community/index.astro:325` — `/* TODO: AdSense 콘솔에서 발급받은 광고 단위 ID */`
- `src/pages/benefits/index.astro:395` — `/* TODO: AdSense 콘솔에서 발급받은 광고 단위 ID */`

**Impact:** Ad slots with empty IDs may not render ads correctly on these pages, losing potential ad revenue.

**Fix approach:** Configure proper ad slot IDs from the AdSense console.

---

### Kakao OAuth Redirect URI Hardcoded

**Issue:** The Kakao OAuth callback URL is hardcoded in two places instead of being computed from the request hostname.

**Files:**
- `src/pages/auth/login.astro:5` — `const REDIRECT_URI = 'https://persona.aikorea24.kr/api/auth/callback/kakao'`
- `functions/api/auth/callback/kakao.js:43` — `const REDIRECT_URI = 'https://persona.aikorea24.kr/api/auth/callback/kakao'`

**Impact:** Cannot run OAuth flow on localhost or in preview deployments. `login.astro` could compute it from `window.location.origin`, and the callback could use `request.url` origin. Breaks dev workflow for any OAuth-related changes.

**Fix approach:** In `login.astro`, compute from `window.location.origin`. In the callback, compute from `new URL(request.url).origin`.

---

### AdSense Async Ad Code Has No Error Handling

**Issue:** The AdSense `<script>` tags and ad `<ins>` elements have no error handling or fallback if the ad network fails to load (e.g., due to ad blockers).

**Files:** All pages with AdSense code (12+ files)

**Impact:** If AdSense fails (blocked by ad blocker, network error), the entire page experience isn't degraded, but there's no visibility into whether ads are rendering correctly. No graceful fallback for ad-block users.

**Fix approach:** Consider adding a CSS class that hides AdSense containers if the ad fails to render (use the `data-adsbygoogle-status` attribute pattern).

---

## Security Considerations

### CRITICAL: Hardcoded R2 Credentials with Fallback Values

**Issue:** `scripts/manual-publisher/r2_upload.py` contains hardcoded R2 credentials as fallback values in `env()` calls. If the environment variable is not set, the code falls back to the hardcoded default — which exposes real credentials in the source code.

**Files:** `scripts/manual-publisher/r2_upload.py:16-18`
```python
R2_ACCOUNT_ID = env("R2_ACCOUNT_ID", "fac9808c757df31d797190c529aaa71a")
R2_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID", "f283c44d6346fe3577067aeda789fd56")
R2_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY", "03b9bc340fee3b087cdf9fb2fd9c69782d515ad1a22073cbbc5cc5550da42a8e")
```

**Impact:** Anyone with access to this repository (including public forks, if any) can read R2 credentials and potentially access or modify the blog thumbnail bucket. This is a leak of cloud storage credentials.

**Fix approach:**
1. Revoke the current credentials in Cloudflare R2 dashboard
2. Remove the fallback default values — use `env("VAR_NAME")` without defaults
3. Add `r2_upload.py` to a `.secrets` scan list
4. Rotate R2 access keys

---

### HIGH: Hardcoded Kakao JavaScript SDK Key

**Issue:** The Kakao JavaScript SDK key is hardcoded in client-side code in two places. While a JavaScript SDK key is a public client ID (not a secret), it should still be managed as a config variable.

**Files:**
- `src/pages/persona/[...slug].astro:908` — `window.Kakao.init('8ee60344ebc6252b953d28de31bf5dac');`
- `src/pages/my-persona.astro:1003` — `window.Kakao.init('8ee60344ebc6252b953d28de31bf5dac');`

**Impact:** This key is public-facing by nature (JavaScript SDK needs it exposed), but having it hardcoded means:
1. Cannot use different keys per environment (dev/staging/prod)
2. Key rotation requires finding and replacing all instances

**Fix approach:** Define as `PUBLIC_KAKAO_JS_KEY` in an environment variable and pass via `define:vars` in Astro's script blocks.

---

### Questionable Admin User ID Default

**Issue:** Community API functions use a hardcoded admin user ID fallback of `1` when `ADMIN_USER_IDS` env var is not set.

**Files:**
- `functions/api/community/posts.js:74` — `const admins = (env.ADMIN_USER_IDS || '1').split(',')...`
- `functions/api/community/comments.js:38` — `const admins = (env.ADMIN_USER_IDS || '1').split(',')...`
- `functions/api/community/posts/[id].js:26` — `user.id !== 1` (hardcoded check without env var)

**Impact:** Any user who happens to have ID `1` in the database becomes an admin. The difference between `posts.js` (env var with fallback) and `posts/[id].js` (hardcoded `1`) creates an inconsistency.

**Fix approach:** Always require `ADMIN_USER_IDS` to be explicitly set. Remove hardcoded `user.id !== 1` check.

---

### Extensive `innerHTML` Usage (28 Matches) — Potential XSS Risk

**Issue:** Pages use `innerHTML` extensively for rendering dynamic content from API responses and user input. If any user-generated content (post titles, content, comments) is rendered via `innerHTML` without sanitization, it could lead to XSS.

**Files (examples):**
- `src/pages/community/[id].astro:313` — `list.innerHTML = comments.map(function(c) {...}` — renders comment content
- `src/pages/community/index.astro:337` — `list.innerHTML = posts.map(function(p, i) {...}` — renders post titles
- `src/pages/my-persona.astro:555` — `wrap.innerHTML = results.map(r => {...}`
- `src/pages/benefits/index.astro:481` — `pagerEl.innerHTML = html`
- `src/components/SearchBar.astro:164` — `resultsEl!.innerHTML = results.map(...)`

**Impact:** If any user input in comments, posts, or search results contains `<script>` or event handlers, they could execute in the context of other users' browsers.

**Mitigation:** Currently, user content (comments, posts) goes through HTTP API responses. The API returns raw JSON, and the client renders it with `.innerHTML`. If the backend doesn't strip HTML from user content, this is an XSS vector.

**Fix approach:**
1. Use `textContent` instead of `innerHTML` where possible
2. Sanitize user content on the backend before storing
3. Use `DOMPurify` on the client if HTML rendering is intentional
4. At minimum, escape HTML entities (`<`, `>`, `&`, `"`, `'`) before inserting

---

### No Rate Limiting on Community API

**Issue:** Community API endpoints (`/api/community/posts`, `/api/community/comments`, `/api/community/like`) have no rate limiting.

**Files:** `functions/api/community/posts.js`, `functions/api/community/comments.js`, `functions/api/community/like.js`

**Impact:** An attacker (even unauthenticated for GET endpoints) could:
- Flood the D1 database with POST requests (though auth-protected)
- Scrape all posts/comments at high throughput
- Mass-like or mass-delete if they compromise a session

**Fix approach:** Add rate limiting middleware — Cloudflare WAF rate limiting rules or a simple in-function counter using D1 or KV.

---

### No Input Validation on Like API

**Issue:** `functions/api/community/like.js` accepts `post_id` from the request body without type validation before using it in SQL queries.

**File:** `functions/api/community/like.js:8` — `post_id` parsing lacks `parseInt()` or type checking seen in other endpoints.

**Impact:** While D1 bindings are parameterized, `NaN` or null values could cause unexpected query behavior.

---

## Performance Bottlenecks

### 2,244 Static Persona Pages on SSG Build

**Issue:** `getStaticPaths()` generates 2,244 individual HTML pages for persona profiles at build time. Each page loads and processes the full `persona-stats.json` (25 MiB) in memory.

**Files:** `src/pages/persona/[...slug].astro`

**Impact:**
- Build time increases linearly with persona count
- Memory usage spikes during build (loading 25 MiB JSON + processing)
- Failed builds waste significant time (cannot restart from checkpoint)

**Fix approach:** If build time becomes problematic, consider:
1. Pre-rendering only popular pages (204 decade-based pages)
2. Using client-side data loading with skeleton states for long-tail pages
3. Incremental static regeneration if/when Cloudflare supports it

---

### Large `persona-stats.json` (25 MiB) Build Dependency

**Issue:** The 25 MiB persona-stats.json must be loaded in Astro frontmatter at build time for every persona page. Additionally, it must be manually removed from `dist/` before deployment (both in `deploy.sh` and `build_deploy.py`) because it exceeds Cloudflare's 25 MiB file limit.

**Files:**
- `public/persona-stats.json`
- `scripts/deploy.sh:135` — `rm -f dist/persona-stats.json`
- `scripts/auto-writer/shared/build_deploy.py:22-23` — `os.remove(...)`

**Impact:** This is a recurring fragility point. The 25 MiB limit was recently hit (commit `f174eab`), causing deployment failures. If a future build script doesn't include this removal step, deployments will silently fail.

**Fix approach:** Add the removal step as a build script hook in `package.json` rather than in multiple deploy scripts. Consider splitting the data into per-region chunks.

---

### 30-Minute Polling for Manual Publisher

**Issue:** `launchd` runs `watcher.py` every 30 minutes to check for new files in `inbox/`, even when the inbox is empty.

**File:** `scripts/manual-publisher/watcher.py` (launchd interval: 1800s)

**Impact:** Wastes system resources on polling. Each check involves scanning the inbox directory and reading `done.json`.

**Fix approach:** Use filesystem events (e.g., `watchdog` library) instead of polling, or increase the polling interval to 1-2 hours.

---

## Fragile Areas

### Cloudflare Pages Secret Pre-check in `deploy.sh`

**Issue:** The deployment script validates Cloudflare secrets exist before building. This is good practice, but if a secret check fails mid-deploy, the build has already run, wasting time.

**File:** `scripts/deploy.sh:133-134`

**Impact:** Build takes ~2-3 minutes before secret validation. If a secret is missing, the build time is wasted.

**Fix approach:** Validate secrets before running the build.

---

### Login Session Cookie Domain Migration

**Issue:** The Kakao OAuth callback sets legacy `.aikorea24.kr` domain cookies to invalidate them during migration (lines 131-132). This is a migration workaround that can be cleaned up.

**File:** `functions/api/auth/callback/kakao.js:131-132`

**Impact:** Dead migration code left in a critical authentication flow.

**Fix approach:** Remove after confirming no clients still have `.aikorea24.kr` cookies.

---

### Hardcoded R2 Public URL

**Issue:** The R2 public base URL is hardcoded with a specific R2 bucket hash in two files.

**Files:**
- `scripts/auto-writer/shared/thumbnail_gen.py:16` — `R2_BASE_URL = "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails"`
- `scripts/manual-publisher/r2_upload.py:20` — `R2_PUBLIC_URL = env("R2_PUBLIC_URL", "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev")`

**Impact:** If the R2 bucket is migrated or the public URL changes, all thumbnails will 404. The `r2_upload.py` version at least supports env override.

**Fix approach:** Use the bucket name to derive the public URL, or use a custom domain consistently.

---

### Inconsistent Enum Naming Convention

**Issue:** The community page uses inconsistent naming variants for the same concept:
- `board_type` in backend: `persona` / `benefit`
- Board labels in JS: `persona` / `benefit`

**File:** `src/pages/community/write.astro:167-171`

**Impact:** Low — works correctly but creates confusion for future schema changes.

---

## Cross-Platform Compatibility

### macOS-Specific Font Fallback

**Issue:** Both thumbnail generators hardcode macOS font paths as fallbacks.

**Files:**
- `scripts/auto-writer/shared/thumbnail_gen.py:47-49` — `/System/Library/Fonts/Supplemental/AppleGothic.ttf`
- `scripts/manual-publisher/thumbnail.py:40-41` — same paths

**Impact:** Will fail to find fonts on Linux (CI/CD, Cloudflare Workers, etc.). The code falls back to `ImageFont.load_default()` which produces pixelated, small text.

**Fix approach:** Include a bundled font file in the repo or download one if missing. Use a cross-platform font like Noto Sans CJK.

---

### Case-Insensitive Path Inconsistency

**Issue:** `manual-publisher/` scripts use `/Users/twinssn/projects/` (lowercase) while `auto-writer/` scripts use `/Users/twinssn/Projects/` (mixed case). macOS is case-insensitive, so this works, but it would break on Linux.

**Fix approach:** Eliminate hardcoded paths entirely (see first entry).

---

## Test Coverage Gaps

### No Tests for Any API Endpoints

**Issue:** The entire `functions/` directory (7 API endpoints for community CRUD, OAuth, and benefit click tracking) has **zero test files**. No unit tests, integration tests, or E2E tests.

**Files:** All files under `functions/`

**Risk:** Any change to API logic (D1 queries, auth checks, input validation) can silently break. Error handling regressions cannot be detected.

**Priority:** High

---

### No Tests for Community Client Pages

**Issue:** The SPA-like community pages (`community/index.astro`, `community/[id].astro`, `community/write.astro`) with inline JavaScript have no tests.

**Files:**
- `src/pages/community/index.astro` — 225 lines of inline JS
- `src/pages/community/[id].astro` — significant inline JS for comments rendering
- `src/pages/community/write.astro` — 88 lines of inline JS

**Risk:** Client-side logic (DOM manipulation, API calls, error handling) changes can break user flows without detection.

**Priority:** Medium

---

### No Tests for Content Generation Pipelines

**Issue:** The auto-writer and manual-publisher Python pipelines (~2,000+ lines combined) have no tests.

**Files:** All files under `scripts/auto-writer/`, `scripts/manual-publisher/`

**Risk:** LLM outputs change over time, API endpoints evolve, and schema changes can break content generation. Without tests, failures only surface at deploy time or in production.

**Priority:** Medium

---

### No Tests for Persona Matching Logic

**Issue:** The core business logic in `src/lib/` (`benefitMatcher.ts`, `welfareMatcher.ts`, `personaMatcher.ts`) has no tests.

**Files:**
- `src/lib/benefitMatcher.ts`
- `src/lib/welfareMatcher.ts`
- `src/lib/personaMatcher.ts`

**Risk:** These functions encode the site's primary value proposition (matching users to benefits/welfare). Incorrect matching logic directly impacts user trust.

**Priority:** High

---

## Missing Critical Features

### No Graceful Error Handling for D1 Failures

**Issue:** Several API functions (`like.js`, `comments.js`, `posts.js`) do not wrap D1 operations in try/catch blocks. If the D1 database is unavailable or a query fails, the function throws an unhandled error, returning a 500 with no useful information.

**Files:**
- `functions/api/community/like.js` — no try/catch around any D1 query
- `functions/api/community/comments.js` — no try/catch around D1 queries
- `functions/api/community/posts.js` — no try/catch around D1 queries
- `functions/api/community/posts/[id].js` — no try/catch

**Example:** `functions/api/community/like.js:8` — if `env.DB.prepare(...).first()` throws, the function crashes with no error response.

**Impact:** D1 downtime or throttling causes 500 responses with no informative error to the client.

---

*Concerns audit: 2026-07-01*
