# Phase 1: Security & Portability — EXECUTION PLAN (REVISED)

**Status:** Revised | **Target:** `.planning/PLAN.md`
**Phase:** 01-security-portability
**Plans:** 5 plans in 3 waves

---

## Objective

Remediate **15 critical/high-severity issues** from the CONCERNS.md audit across four domains: security (credential leakage, XSS, auth bypass, rate limiting), portability (hardcoded paths, font dependencies), configuration extraction (AdSense, Kakao keys), and codebase cleanup (`.bak`, `__pycache__`, dead code, TODOs).

**Success Criteria:**
- Zero hardcoded credentials in source code
- No R2/Kakao secrets exposed in fallback defaults
- All user-generated content sanitized before innerHTML insertion
- Admin authorization consistently uses `env.ADMIN_USER_IDS`
- All community API endpoints have D1 error handling and rate limiting
- All absolute paths use `scripts/paths.py` relative computation
- macOS-only font paths have cross-platform fallbacks
- All `.ssr-backup/`, `__pycache__/` files removed from git tracking; `.bak` files cleaned from disk
- Dead code (`filter.py`) removed, TODO placeholders validated
- AdSense ID lives in `src/consts.ts`, Kakao JS key in env var, OAuth redirect computed from origin

---

## ⚠ PREREQUISITES (Must Complete Before Wave 1)

### P-1: R2 Credential Rotation (HUMAN — Before ANY Plan Executes)

The three R2 credential fallback defaults (Account ID, Access Key ID, Secret Access Key) currently exist in `r2_upload.py`. Task 1.1 removes these fallbacks. Therefore, valid credentials MUST exist in `.env` **before** Task 1.1 removes the hardcoded fallbacks.

**What must happen:**
1. Go to Cloudflare Dashboard → R2 → Manage API Tokens
2. Create a **new** API token with Object Read & Write permissions for the `hotissue-images` bucket
3. Copy Account ID, Access Key ID, Secret Access Key
4. Add to `.env`:
   ```
   R2_ACCOUNT_ID=<new_account_id>
   R2_ACCESS_KEY_ID=<new_access_key_id>
   R2_SECRET_ACCESS_KEY=<new_secret_access_key>
   ```
5. Verify new credentials work: `python3 scripts/manual-publisher/r2_upload.py` with a test file
6. **After verification**, go back to Cloudflare Dashboard and **revoke** the old token (ID starting with `f283c44d`)

**Rollback if rotation fails:** Restore old token from Cloudflare R2 → Manage API Tokens (check if still active), revert `.env` additions, and keep the fallback defaults in `r2_upload.py` temporarily. Reopen the issue.

### P-2: Kakao Developer Console Update (HUMAN — Before Wave 2 / Plan 03)

Task 3.3 changes the OAuth redirect URI from a hardcoded domain to a dynamic origin computed at runtime. Kakao's OAuth whitelist must include the new callback URLs **before** this change deploys, otherwise existing OAuth logins will break with "redirect_uri_mismatch."

**What must happen (before Plan 03 executes):**
1. Go to [Kakao Developers](https://developers.kakao.com) → 내 애플리케이션 → 플랫폼 → Web
2. Add these Redirect URIs:
   - `http://localhost:4321/api/auth/callback/kakao`
   - `https://*.pages.dev/api/auth/callback/kakao`
   - `https://persona.aikorea24.kr/api/auth/callback/kakao` (already exists)
3. Verify the 사이트 도메인 also includes `http://localhost:4321`

**Rollback if OAuth breaks:** Temporarily revert `login.astro:5` and `callback/kakao.js:43` to the hardcoded `https://persona.aikorea24.kr/api/auth/callback/kakao` value, rebuild and redeploy. Re-verify that Kakao dev console has the right URIs.

### P-3: Noto Sans CJK Font Download (HUMAN — Before Plan 04)

Task 4.1 needs `fonts/NotoSansCJK-Regular.otf` — download ~3MB and place at `fonts/NotoSansCJK-Regular.otf` relative to project root.

---

## Task Breakdown

### Wave 1 — Cleanup & Foundation (parallel, no dependencies, after P-1)

---

#### Plan 01: Security-Critical & Git Hygiene

**Files modified:** `scripts/manual-publisher/r2_upload.py`, `scripts/auto-writer/shared/thumbnail_gen.py`, `.gitignore`, `scripts/manual-publisher/deployer.py`, `scripts/manual-publisher/publisher.py`
**Autonomous:** Yes (P-1 already completed)

| # | Task | Description | Files | Verify |
|---|------|-------------|-------|--------|
| 1.1 | **Remove R2 credential fallback defaults** | In `r2_upload.py:16-18`, change `env("R2_ACCOUNT_ID", "fac9808c...")` → `env("R2_ACCOUNT_ID")` (remove fallback). Same for ACCESS_KEY_ID and SECRET_ACCESS_KEY on lines 17-18. **Do NOT change** `R2_BUCKET` or `R2_PUBLIC_URL` fallbacks (those are non-secret config). Add `.secrets` pattern marker comment. **Prerequisite P-1 guarantees `.env` has valid R2 credentials at this point.** | `scripts/manual-publisher/r2_upload.py` | `grep -c 'env("R2_ACCOUNT_ID"' r2_upload.py` returns exactly 1 occurrence with NO second-string argument. `grep 'R2_SECRET_ACCESS_KEY' r2_upload.py` shows no hardcoded hex string |
| 1.2 | **Parameterize R2 public URL with env var fallback** | In `thumbnail_gen.py:16`, replace hardcoded `R2_BASE_URL` with `os.getenv("R2_PUBLIC_URL", "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev") + "/blog-thumbnails"`. The public URL is NOT a secret — the current URL serves as a backward-compatible fallback, but the env var override enables portability to different R2 buckets/regions. | `scripts/auto-writer/shared/thumbnail_gen.py` | Verify `R2_BASE_URL = os.getenv("R2_PUBLIC_URL", "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev") + "/blog-thumbnails"` |
| 1.3 | **Git hygiene — .ssr-backup/, __pycache__, .bak cleanup** | (a) Add `.ssr-backup/` and `__pycache__/` to `.gitignore` (`*.bak` already present at line 21). (b) `git rm --cached -r .ssr-backup/` (9 files tracked). (c) Remove all 24 tracked `__pycache__/` `.pyc` files via `git rm --cached` per-directory or `find . -path '*/__pycache__/*' -exec git rm --cached {} +`. (d) Delete all 10 `.bak` files from disk (they exist on disk but are already gitignored — still cluttering the working tree). (e) Verify no remaining tracked `.ssr-backup` or `__pycache__` files. | `.gitignore`, plus git rm for .ssr-backup and __pycache__ | `git ls-files .ssr-backup/ '**/__pycache__/*'` returns empty. `find . -name '*.bak' -not -path './.git/*'` returns 0. |
| 1.4 | **Remove dead code + TODO validation** | (a) In `publisher.py:22`, remove `import filter as finance_filter`. (b) In `generate_post.py:151,159,163,167,183,185`, replace TODO strings with either `raise ValueError("TODO placeholder not filled")` or remove the lines. Add a validation function that checks for remaining "TODO" in output before writing. | `scripts/manual-publisher/publisher.py`, `scripts/generate_post.py` | `grep -n "TODO" generate_post.py` returns 0 matches after fix. `grep "import filter" publisher.py` returns empty. |

**Rollback if R2 upload breaks after 1.1:**
Re-add fallback defaults temporarily, rebuild. Root cause is either missing `.env` entries (re-check P-1) or wrong credential values. The old token should NOT be revoked until P-1 step 6 verification passes.

---

#### Plan 02: Absolute Path Portability

**Files modified:** `scripts/paths.py` (new), 19+ Python files in auto-writer and manual-publisher
**Autonomous:** Yes

| # | Task | Description | Files | Verify |
|---|------|-------------|-------|--------|
| 2.1 | **Create `scripts/paths.py`** | New shared module: compute `PROJECT_ROOT = Path(__file__).resolve().parent.parent`, expose `BLOG_DIR`, `INBOX_DIR`, `BG_IMG_DIR`, `THUMBNAIL_DIR`, `DOTENV_PATH`, `COMMON_ENV_PATH`, `SCRIPTS_DIR`. All paths derive from `PROJECT_ROOT` not hardcoded strings. | `scripts/paths.py` | `python3 -c 'from paths import PROJECT_ROOT; print(PROJECT_ROOT)'` outputs the correct project directory |
| 2.2 | **Replace all hardcoded paths in auto-writer** | Update 10 files that call `load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")` to `load_dotenv(paths.DOTENV_PATH)`. Update `pipeline.py:9` BLOG_DIR, `thumbnail_gen.py:9` BG_DIR, `build_deploy.py:7` PROJECT_DIR, etc. The `pipeline.py:6-7` becomes `load_dotenv(paths.DOTENV_PATH)` and `load_dotenv(paths.COMMON_ENV_PATH)`. | `scripts/auto-writer/pipeline.py`, `scheduler.py`, `writer.py`, `fetcher.py`, `fetcher_invest.py`, `fetcher_loan_fin.py`, `shared/thumbnail_gen.py`, `shared/build_deploy.py`, `shared/reviewer.py`, `shared/notifier.py` | `grep -c 'Users/twinssn' scripts/auto-writer/**/*.py` returns 0 |
| 2.3 | **Replace all hardcoded paths in manual-publisher** | Update `publisher.py:19` BLOG_DIR, `watcher.py:5` BLOGSMITH_OUTPUT, `entity_injector.py:4` BLOG_DIR, `thumbnail.py:8-9` THUMBNAIL_DIR/BG_DIR, `deployer.py:10` PROJECT_DIR. All use `from paths import ...`. | `scripts/manual-publisher/publisher.py`, `watcher.py`, `entity_injector.py`, `thumbnail.py`, `deployer.py` | `grep -c 'Users/twinssn' scripts/manual-publisher/**/*.py && grep -c 'projects/' scripts/manual-publisher/**/*.py` both return 0 |

**Rollback if path changes break auto-writer:**
Revert `paths.py` and all changed files. The old hardcoded paths still work. Fix is low-risk because `Path(__file__).resolve().parent.parent` is a deterministic computation.

---

### Wave 2 — Configuration & Font Portability (independent from each other; after P-2, P-3)

---

#### Plan 03: Configuration Extraction

**Files modified:** `src/consts.ts`, `src/components/BaseHead.astro`, `src/pages/persona/[...slug].astro`, `src/pages/my-persona.astro`, `src/pages/community/write.astro`, `src/pages/community/index.astro`, `src/pages/community/[id].astro`, `src/pages/benefits/index.astro`, `src/layouts/BlogPost.astro`, `src/pages/auth/login.astro`, `functions/api/auth/callback/kakao.js`
**Autonomous:** Yes (P-2 already completed)

| # | Task | Description | Files | Verify |
|---|------|-------------|-------|--------|
| 3.1 | **Extract AdSense ID to consts.ts** | Add `export const ADSENSE_CLIENT = "ca-pub-5938862195544185"` to `src/consts.ts`. Then update all 12+ inline references to `data-ad-client={ADSENSE_CLIENT}` or `' data-ad-client="' + ADSENSE_CLIENT + '"'`. Files: BaseHead.astro:66, `[...slug].astro:322`, `community/write.astro:8`, `community/[id].astro:241`, `community/index.astro:324`, `benefits/index.astro:394`, `my-persona.astro:271,283,308`, `BlogPost.astro:357,383,408`. Also add `export const ADSENSE_SLOT_DEFAULT = "auto"` and `export const ADSENSE_SLOT_BLOG = "8107272066"`. | `src/consts.ts` + all 12 location files | `grep -c 'ca-pub-5938862195544185' src/` returns 0. `grep 'ADSENSE_CLIENT' src/consts.ts` returns 1 |
| 3.2 | **Extract Kakao JS key to env var** | (a) Define `PUBLIC_KAKAO_JS_KEY` in `.env` (with current key `8ee60344ebc6252b953d28de31bf5dac`). (b) In `[...slug].astro:908` and `my-persona.astro:1003`, replace literal key with `import.meta.env.PUBLIC_KAKAO_JS_KEY`. (c) Add `define:vars={{ kakaoJsKey: import.meta.env.PUBLIC_KAKAO_JS_KEY }}` to the `<script>` tag or inline the var. (d) Verify env passthrough via `vite.define` in `astro.config.mjs`. | `src/pages/persona/[...slug].astro:908`, `src/pages/my-persona.astro:1003` | `grep -c "8ee60344ebc6252b953d28de31bf5dac" src/` returns 0 |
| 3.3 | **Fix Kakao OAuth redirect URI** | (a) In `login.astro:5`, change hardcoded `REDIRECT_URI` to compute from `Astro.site` or `window.location.origin`: `const REDIRECT_URI = import.meta.env.PROD ? 'https://persona.aikorea24.kr/api/auth/callback/kakao' : window.location.origin + '/api/auth/callback/kakao'`. (b) In `callback/kakao.js:43`, change to `const REDIRECT_URI = (new URL(request.url)).origin + '/api/auth/callback/kakao'`. (c) Remove legacy cookie invalidation block (lines 131-132) — the `.aikorea24.kr` migration cookies. **Prerequisite P-2 guarantees Kakao dev console already allows localhost + wildcard redirect URIs.** | `src/pages/auth/login.astro:5`, `functions/api/auth/callback/kakao.js:43,131-132` | `grep -c 'persona\.aikorea24\.kr.*callback' login.astro` returns 0. `grep 'Domain=\.aikorea24\.kr' callback/kakao.js` returns 0 |

**Rollback if OAuth redirect breaks:**
Revert `login.astro:5` and `callback/kakao.js:43` to hardcoded `REDIRECT_URI = 'https://persona.aikorea24.kr/api/auth/callback/kakao'`. Revert legacy cookie removal (lines 131-132). Rebuild and redeploy. The Kakao dev console already has the old fixed URI whitelisted, so this restores the previous working state.

---

#### Plan 04: Font Portability & API Hardening

**Files modified:** `scripts/auto-writer/shared/thumbnail_gen.py`, `scripts/manual-publisher/thumbnail.py`, `functions/api/community/posts.js`, `functions/api/community/posts/[id].js`, `functions/api/community/comments.js`, `functions/api/community/like.js`, `functions/api/auth/callback/kakao.js`, `functions/api/_shared/rate-limit.js` (new)
**Autonomous:** Yes (P-1, P-3 already completed)

| # | Task | Description | Files | Verify |
|---|------|-------------|-------|--------|
| 4.1 | **Fix macOS font dependency** | In both `thumbnail_gen.py:44-54` and `thumbnail.py:38-50`: (a) Add `NotoSansCJK-Regular.otf` path (`fonts/NotoSansCJK-Regular.otf` relative to project root). (b) Download the font if missing (or rely on P-3 having placed it). (c) Keep AppleGothic as first fallback but add the bundled Noto Sans as a second fallback. (d) Do NOT rely on `ImageFont.load_default()` as primary. | `scripts/auto-writer/shared/thumbnail_gen.py`, `scripts/manual-publisher/thumbnail.py` | `python3 -c 'from PIL import ImageFont; f=ImageFont.truetype("fonts/NotoSansCJK-Regular.otf", 32); print("ok")'` succeeds |
| 4.2 | **Add D1 error handling (community APIs + callback/kakao.js)** | Wrap all D1 operations in `posts.js`, `posts/[id].js`, `comments.js`, `like.js`, AND `callback/kakao.js` in try/catch blocks. Return `{ error: "database_error", message: e.message }` with status 500. Operations to cover: **posts.js:** lines 12-13,34-40,57-60,71-80; **posts/[id].js:** lines 8-13,24-29; **comments.js:** lines 13,22-26,42; **like.js:** lines 8-16; **callback/kakao.js:** lines 76-102 (7 D1 operations: SELECT user, 2× nickname dedup loops INSERT/UPDATE/SELECT). For callback/kakao.js, on DB error redirect to `/?error=db_error` (don't expose stack traces in redirect URL). | `functions/api/community/posts.js`, `posts/[id].js`, `comments.js`, `like.js`, `functions/api/auth/callback/kakao.js` | `grep -c 'try' posts.js posts/\[id\].js comments.js like.js callback/kakao.js` returns >= 5 (one per file) |
| 4.3 | **Fix Admin ID fallback across all three community files** | Replace `|| '1'` Admin ID fallback with `|| ''` in ALL three locations: **(a)** `posts/[id].js:74` (currently `env.ADMIN_USER_IDS || '1'`). **(b)** `posts.js:74` (same pattern — currently missed). **(c)** `comments.js:38` (same pattern — currently missed). The fix is: `const admins = (env.ADMIN_USER_IDS || '').split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));`. When `ADMIN_USER_IDS` is unset or empty, no user is admin (removes the implicit admin status for user ID 1). | `functions/api/community/posts.js:74`, `posts/[id].js:74`, `comments.js:38` | `grep "|| '1'" posts.js posts/\[id\].js comments.js` returns 0. `grep "|| ''" posts.js` returns at least 1 match. Verify `ADMIN_USER_IDS` must be explicitly set for admin access. |
| 4.4 | **Add D1-based rate limiting middleware + WAF setup note** | Create `functions/api/_shared/rate-limit.js` implementing IP-based rate limiting using **D1** (NOT in-memory Map — edge nodes are isolated, Map loses state across requests). Approach: (a) Create D1 table `rate_limits` with columns `ip TEXT, endpoint TEXT, window_start INTEGER, count INTEGER`, primary key on `(ip, endpoint, window_start)`. (b) On each request, check current count: if window has expired (>60s), reset; if count >= limit, return 429. (c) TTL cleanup via periodic DELETE of old windows. Apply to: `posts.js` POST/DELETE (10 req/min), `comments.js` POST/DELETE (10 req/min), `like.js` POST (20 req/min). (d) Add human step to configure Cloudflare WAF rate limiting rules in the dashboard for production (lower latency than D1). | `functions/api/_shared/rate-limit.js` (new), plus imports and integration in posts.js, comments.js, like.js | `curl -X POST /api/community/like` 10+ times in quick succession returns 429 on the 11th request. `grep -c 'rate-limit' posts.js comments.js like.js` returns 3. |

**Rollback if D1 error handling in callback/kakao.js breaks OAuth:**
The hardest rollback scenario — if try/catch in callback/kakao.js causes redirect issues, revert to the original code (lines 76-102 with no try/catch). The D1 operations were previously unhandled, meaning errors would throw 500s — rollback restores that status quo.

**Rollback if rate limiting blocks legitimate users:**
Set rate limit thresholds very high (e.g., 1000 req/min) to effectively disable, or remove the rate-limit import from each file. Monitor after deployment and adjust limits.

---

### Wave 3 — XSS Mitigation

---

#### Plan 05: innerHTML XSS Fix

**Files modified:** `src/pages/community/[id].astro`, `src/pages/community/index.astro`, `src/pages/my-persona.astro`, `src/pages/benefits/index.astro`, `src/components/SearchBar.astro`, `src/lib/html-sanitizer.ts` (new)
**Autonomous:** Yes

| # | Task | Description | Files | Verify |
|---|------|-------------|-------|--------|
| 5.1 | **Create HTML sanitizer utility** | Create `src/lib/html-sanitizer.ts` with two exports: (a) `escapeHtml(str: string): string` — escapes `<`, `>`, `&`, `"`, `'` to HTML entities. (b) `safeInnerHTML(el: HTMLElement, html: string): void` — sets `textContent` or uses a simple regex-based tag whitelist. For the MVP, use escapeHtml for user-generated content (comments, post titles) and only allow safe HTML for controlled templates. | `src/lib/html-sanitizer.ts` | Unit tests: `escapeHtml('<script>')` returns `&lt;script&gt;`. |
| 5.2 | **Fix community comment rendering** | In `community/[id].astro:313`, the `comments.map(function(c) { ... })` renders comment content via `list.innerHTML`. Change to use `escapeHtml(c.content)` for all user-supplied fields (`c.content`, `c.author_name`). The HTML structure (the `<div>` wrappers) is safe template, but interpolated strings must be escaped. | `src/pages/community/[id].astro:313` | Verify injected `<script>alert(1)</script>` in comment body renders as text, not executable |
| 5.3 | **Fix community post listing** | In `community/index.astro:337`, post titles rendered via `innerHTML` must use `escapeHtml(p.title)`. Also fix lines 303, 332, 380 for static "loading"/"empty"/"error" messages (these are safe, but use `textContent` pattern for defense in depth). | `src/pages/community/index.astro:337` | `grep -c 'innerHTML.*p\.' community/index.astro` returns 0 |
| 5.4 | **Fix my-persona.astro and SearchBar.astro** | In `my-persona.astro:555,602,694,750,764` and `SearchBar.astro:164`, apply `escapeHtml()` to any interpolated user data. The results rendering (`results.map`) contains `r` fields that originate from API responses — must be sanitized. | `src/pages/my-persona.astro`, `src/components/SearchBar.astro` | `grep 'innerHTML' my-persona.astro | grep -v 'escapeHtml'` returns 0 |

**Rollback if XSS fix breaks community page rendering:**
Revert to the original `innerHTML` patterns temporarily. Risk is low because the fix only escapes user-controlled interpolations — the HTML template structure remains unchanged.

---

## Dependency Graph

```
Plans 01-02 (Wave 1) ────── after P-1 (R2 rotation), no inter-dependency
Plans 03-04 (Wave 2) ────── after P-2 (Kakao dev console) + P-3 (font download), no inter-dependency
Plan 05   (Wave 3) ────── after Wave 2 completion (review before XSS changes)
```

**Key dependency notes:**
- **P-1 (R2 rotation) is mandatory BEFORE Wave 1.** Task 1.1 removes credential fallbacks — without valid `.env` R2 values, uploads fail.
- **P-2 (Kakao dev console) is mandatory BEFORE Wave 2.** Task 3.3 changes redirect URI computation — Kakao must whitelist new callback URLs first.
- **P-3 (Noto Sans font download) is mandatory BEFORE Plan 04.** Task 4.1 needs the font file.
- Plans 01-02 are completely independent (different files: Python cleanups vs path portability).
- Plans 03-04 touch different files (Astro/JS vs Python/Cloudflare Functions) and are independent.
- Plan 05 (XSS) is Wave 3 because it should be verified AFTER API hardening (Plan 04) ensures the API doesn't store unescaped HTML in the first place.

---

## Multi-Source Coverage Audit

| Source | Items | Plan Coverage | Status |
|--------|-------|---------------|--------|
| **GOAL** | Security & Portability fixes from CONCERNS.md | Plans 01-05 | ✅ All 15 issues addressed |
| **CONCERNS.md** | R2 credentials (Security 1) | Plan 01, Task 1.1 | ✅ |
| **CONCERNS.md** | innerHTML XSS (Security 2) | Plan 05, Tasks 5.1-5.4 | ✅ |
| **CONCERNS.md** | Admin ID hardcoded (Security 3) | Plan 04, Task 4.3 | ✅ (all 3 files fixed) |
| **CONCERNS.md** | Rate limiting (Security 4) | Plan 04, Task 4.4 | ✅ (D1 + WAF) |
| **CONCERNS.md** | D1 error handling (Security 5) | Plan 04, Task 4.2 | ✅ (includes callback/kakao.js) |
| **CONCERNS.md** | Hardcoded absolute paths (Portability 6) | Plan 02, Tasks 2.1-2.3 | ✅ |
| **CONCERNS.md** | macOS font dependency (Portability 7) | Plan 04, Task 4.1 | ✅ |
| **CONCERNS.md** | .bak files (Cleanup 8) | Plan 01, Task 1.3 | ✅ (disk cleanup only; already gitignored) |
| **CONCERNS.md** | .ssr-backup/ (Cleanup 9) | Plan 01, Task 1.3 | ✅ (git rm --cached + .gitignore) |
| **CONCERNS.md** | __pycache__ (Cleanup 10) | Plan 01, Task 1.3 | ✅ (git rm --cached + .gitignore) |
| **CONCERNS.md** | Dead code filter.py (Cleanup 11) | Plan 01, Task 1.4 | ✅ |
| **CONCERNS.md** | TODO placeholders (Cleanup 12) | Plan 01, Task 1.4 | ✅ |
| **CONCERNS.md** | AdSense ID hardcoded (Config 13) | Plan 03, Task 3.1 | ✅ |
| **CONCERNS.md** | Kakao JS key hardcoded (Config 14) | Plan 03, Task 3.2 | ✅ |
| **CONCERNS.md** | Kakao OAuth redirect URI (Config 15) | Plan 03, Task 3.3 | ✅ |

**No gaps found.** All 15 CONCERNS.md items covered. Prerequisites P-1/P-2/P-3 are non-plan human steps outside the 15 issues.

---

## Rollback & Recovery Procedures

### R2 Credential Rotation Failure (P-1 / Plan 01 Task 1.1)

| Failure Mode | Detection | Recovery |
|---|---|---|
| New R2 token doesn't work | `r2_upload.py` upload test fails (step 5) | Do NOT revoke old token. Verify credentials in `.env` are correct. Check R2 token permissions (must have Object Read & Write). |
| Old token revoked before testing | Upload breaks during/after Task 1.1 | Re-add fallback defaults to `r2_upload.py`. Create a new token from scratch. Test new token. Repeat rotation properly. |
| `.env` R2 values lost after rotation | Environment missing vars, upload fails | Check `.env` file integrity. Restore from shell history or password manager. The fallback defaults are gone (removed by 1.1) so `.env` is the only source. |

### OAuth Redirect Breakage (P-2 / Plan 03 Task 3.3)

| Failure Mode | Detection | Recovery |
|---|---|---|
| Kakao returns "redirect_uri_mismatch" | Users report login failure | Revert `login.astro:5` and `callback/kakao.js:43` to hardcoded URL. Rebuild + redeploy. Verify Kakao dev console has the right URIs. |
| Legacy cookie removal breaks session clearing | Session invalidation doesn't work on old-domain cookies | Re-add lines 131-132 in callback/kakao.js. These set `Domain=.aikorea24.kr` — only needed if users still have old-domain cookies. Safe to re-add. |

### Font File Missing (P-3 / Plan 04 Task 4.1)

| Failure Mode | Detection | Recovery |
|---|---|---|
| NotoSansCJK-Regular.otf not found | Thumbnail generation crashes | Switch to AppleGothic-only fallback (works on macOS). For cross-platform, download the font from Google Fonts / Noto CJK release page (~3MB). |
| PIL can't load the font | Font loading exception | Verify the font file isn't corrupt. Re-download from official source. |

### Rate Limiting Blocks Users (Plan 04 Task 4.4)

| Failure Mode | Detection | Recovery |
|---|---|---|
| Legitimate user gets 429 | User reports "too many requests" | Temporarily remove rate-limit import from the affected endpoint file. Adjust limits after reviewing usage patterns. |
| D1 rate limit table doesn't exist | 500 errors on community endpoints | Run D1 migration to create the `rate_limits` table. Without the table, the middleware throws on first query. |

### D1 Error Handling in callback/kakao.js (Plan 04 Task 4.2)

| Failure Mode | Detection | Recovery |
|---|---|---|
| try/catch redirects to `/?error=db_error` falsely | Users reporting login failures | Check D1 availability. Remove try/catch from callback/kakao.js (revert to throwing errors). The OAuth flow should be high-availability — it's better to crash with a 500 than silently redirect to an error page. |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **R2 credential revocation breaks production** | Low (after P-1) | High | P-1 mandates rotation BEFORE fallback removal. Verify new credentials work before revoking old ones (Task 1.1 runs only after P-1 verification). |
| **Path portability typos break auto-writer pipeline** | Medium | High | After replacing 19+ hardcoded paths, a typo in `paths.py` could crash the daily auto-writer. Test by running `python3 scripts/auto-writer/pipeline.py --dry-run` after changes. |
| **AdSense refactor breaks ad rendering** | Low | Medium | Client ID change in 12+ files — a missed reference still works but isn't centralized. The grep-based verification (`grep returns 0`) is reliable. |
| **XSS fix breaks community page UI** | Medium | Medium | Changing from `innerHTML` to `escapeHtml()` might break if any template relies on HTML injection for formatting. The community templates use HTML structure in template literals — careful separation is needed. |
| **Rate limiting blocks legitimate users** | Low | Medium | D1-based rate limiting adds ~10-30ms latency per write request. Conservative limits (10 req/min for writes) should not affect normal usage. WAF rate limiting is the production recommendation (zero latency for authenticated requests). |
| **Callback/kakao.js redirect_uri change breaks OAuth** | Low (after P-2) | High | P-2 mandates adding localhost/wildcard/custom domain URIs to Kakao dev console BEFORE Plan 03 executes. |
| **callback/kakao.js try/catch masks real D1 errors** | Medium | Medium | The DB error path redirects to `/?error=db_error` which is less informative than a 500 stack trace. Add structured logging to detect this scenario. |

---

## Checkpoint / Human Steps

| Step | When | What Human Must Do |
|------|------|-------------------|
| **P-1: R2 Credential Rotation** | **BEFORE Wave 1** | 1. Go to Cloudflare Dashboard → R2 → Manage API Tokens. 2. Create a new API token with Object Read & Write permissions for the `hotissue-images` bucket. 3. Copy Account ID, Access Key ID, Secret Access Key. 4. Add to `.env`: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. 5. Test: `python3 scripts/manual-publisher/r2_upload.py` with a test file. 6. After verification, **revoke the old token** (ID starting with `f283c44d`). |
| **P-2: Kakao Developer Console** | **BEFORE Wave 2** | Add to Kakao developer console (내 애플리케이션 → 플랫폼 → Web → Redirect URI): `http://localhost:4321/api/auth/callback/kakao`, `https://*.pages.dev/api/auth/callback/kakao`. Verify `https://persona.aikorea24.kr/api/auth/callback/kakao` already exists. |
| **P-3: Noto Sans CJK Font** | **BEFORE Plan 04** | Download `NotoSansCJK-Regular.otf` (~3MB) and place in `fonts/` directory (create if missing). Or run a setup script. |
| **Cloudflare WAF Rate Limiting** | **After Plan 04, Task 4.4** | Configure Cloudflare WAF rate limiting rules in the dashboard as the production-grade solution. Apply rate limits to the community API endpoints (`/api/community/*`). The D1-based rate limiter works but adds latency. |

---

## Effort Estimate

| Plan | Domain | Files Changed | Est. Context | Est. Agent Time |
|------|--------|---------------|-------------|-----------------|
| 01 | Security-Critical + Cleanup | ~38 files (git rm) + 4 edits | 35% | 45 min |
| 02 | Path Portability | 1 new + 19 edits | 40% | 60 min |
| 03 | Config Extraction | ~18 files | 30% | 40 min |
| 04 | Font + API Hardening | 9+ files | 40% | 60 min |
| 05 | XSS Mitigation | 7 files | 30% | 45 min |
| **Total** | **15 issues** | **~95 file operations** | | **~4 hours** |

---

## Execution Order

```
PREREQUISITES (manual, before any automation):
  P-1: R2 Credential Rotation ← affects Plan 01 (must complete first)
  P-2: Kakao Dev Console Update ← affects Plan 03 (must complete before Wave 2)
  P-3: Noto Sans CJK Font Download ← affects Plan 04 (must complete before Wave 2)

Wave 1:   Plan 01 (Security + Git Hygiene) ──▶ Plan 02 (Path Portability)
          (parallel — different file sets; after P-1)

Wave 2:   Plan 03 (Config Extraction) ──▶ Plan 04 (Font + API Hardening)
          (parallel — different file sets; after P-2, P-3)

Wave 3:   Plan 05 (XSS Mitigation)
          (after Wave 2 review)
```

**End of Phase 1 Plan (Revised).**
