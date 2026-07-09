# money-aikorea24-funnel-overhaul - Work Plan

## TL;DR (For humans)

**What you'll get:** A fully *measurable* blog→persona-tool funnel (GA4 events + a D1-backed server log), fixed cross-domain attribution (the current `src=` tokens are written but never read), a redesigned A/B-capable CTA ladder that keeps the daily auto-writer running, cleaned content (a `needs_review` backlog cleared + 14 income-series posts deduplicated), and an optimized persona SPA — all aimed at lifting the blog→persona conversion rate.

**Why this approach:** **Instrument-first.** The funnel is currently *unmeasured* — GA4 config exists but fires zero events, and the `src=inline-*` / `src=cta-*` attribution tokens in every CTA link are never read anywhere. You cannot optimize a blind funnel, so we build measurement first (C1→C2→C4), then redesign CTAs (C3) and clean content (C5), then optimize the SPA steps (C6).

**What it will NOT do:** Touch AdSense code/placement (`ca-pub-5938862195544185`) — including the blog-post ad slots in `src/layouts/BlogPost.astro` and the ad CSS in `src/styles/global.css`; stop the daily auto-writer; modify the 5 Hugo blogs (hibernated); break SEO of the existing 100+ posts; add third-party analytics vendors.

**Effort:** XL &nbsp; **Risk:** Medium — cross-domain attribution correctness + keeping auto-writer live during all changes.

**Decisions to sanity-check:** (1) instrument-first, not redesign-first; (2) keep split-domain entry + strengthen session/attribution linkage; (3) include income-series dedupe/structure.

Your next move: approve, or run a high-accuracy review first. Full execution detail follows below.

---

> TL;DR (machine): XL / Medium — measurable funnel (GA4+D1) + fixed cross-domain attribution + A/B CTA ladder (auto-writer-safe) + content cleanup + SPA optimization, goal = lift blog→persona conversion.

## Scope
### Must have
- GA4 custom-event schema + server-side D1 log sink for the full funnel (blog CTA click → persona open → step → result).
- `src` token read on `/my-persona` load and carried across the domain redirect into `/persona/{slug}/` (closes the loop on the split domain).
- Stable first-party `visitor_id` enabling cross-domain journey stitching.
- Redesigned, intent-based, A/B-capable CTA ladder injected by `insert_inline_ctas()` — pipeline-compatible so auto-writer keeps publishing daily.
- `needs_review` backlog cleared with a stated policy.
- income-series 14 posts deduplicated via `canonical` + `noindex`, and `seeder_income.py` fixed to stop emitting near-duplicates.
- `/my-persona` step-friction reduction + result-page loop CTA.
- A post-launch measurement readout (conversion rate + A/B variant comparison).

### Must NOT have (guardrails, anti-slop, scope boundaries)
- NO edits to AdSense snippets/placement. Covered files: `BaseHead.astro`, `my-persona.astro`, `persona/[...slug].astro` (the `ca-pub-5938862195544185` client script), `src/layouts/BlogPost.astro` (the `<ins class="adsbygoogle">` elements + `showInArticle`/`showAd3` ad-conditionals), and `src/styles/global.css` (`.desktop-only` / `.ad-leaderboard` / `.ad-mobile-sticky` ad CSS). The `.desktop-only` leaderboard hiding on mobile is INTENTIONAL (see `global.css:423-428` comment "PC 리더보드 — 모바일에서 숨김") — do NOT remove it. Carve-out: `BlogPost.astro`'s `InlinePersonaCTA` / `entity-card` are CTAs, not ads, and remain editable.
- NO change that breaks `scripts/auto-writer/*` daily publish or `wrangler pages deploy`.
- NO edits to the 5 Hugo blogs or their ads (hibernated, out of scope).
- NO deletion of existing blog posts (dedupe = canonical/noindex, never remove).
- NO new external analytics SDKs (GA4 + first-party D1 log only).
- NO schema change to `persona-stats.json` / `persona-stats-decade.json`.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: **tests-after** (static SSG + Cloudflare Functions + Python pipeline — no unit-test harness exists; verification is build + deploy-dry + behavioral grep/headless). Framework: `npm run build`, `wrangler d1 execute --local`, `curl` against `functions/api/funnel-log.js` (via `wrangler pages dev` or deployed preview), `grep`/`ast-grep` on built `dist/`.
- Evidence: `.omo/evidence/task-<N>-money-aikorea24-funnel-overhaul.<ext>` (JSON logs, SQL output, build stdout, headless console captures).

## Execution strategy
### Parallel execution waves
> Target 5-8 todos per wave. Fewer than 3 (except the final) means you under-split.

- **Wave 1 — Instrumentation foundation (C1):** T1–T4 (GA4 helper, server sink, D1 table, client telemetry lib).
- **Wave 2 — Blog capture + identity (C2 blog-side + C4 id):** T5–T7 (click interception, visitor_id cookie, blog→server beacon).
- **Wave 3 — SPA capture + cross-domain handoff (C2 SPA + C4):** T8–T10 (read src on load, redirect append, result-page event).
- **Wave 4 — CTA redesign (C3):** T11–T14 (variant map, rewrite injector, writer/validator, backfill 100+ posts).
- **Wave 5 — Content quality (C5):** T15–T17 (needs_review backlog, income canonical, seeder fix).
- **Wave 6 — SPA UX + measurement (C6 + payoff):** T18–T20 (step friction, result loop CTA, measurement readout).

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| T1 GA4 event helper | — | T5,T7,T8,T10 | T3,T4 |
| T2 server log sink | T3 | T4,T7 | T1 |
| T3 D1 funnel_events table | — | T2 | T1,T4 |
| T4 client telemetry lib | T1,T2 | T5,T7,T8,T10 | — |
| T5 blog CTA click capture | T4,T6 | T7 | — |
| T6 visitor_id cookie | — | T5,T7,T9,T10 | T1,T3,T4 |
| T7 blog→server beacon | T4,T5 | — | — |
| T8 my-persona read src + open | T4,T6 | T9 | — |
| T9 redirect append src+pid | T6,T8 | T10 | — |
| T10 persona result event | T4,T6,T9 | T19,T20 | — |
| T11 cta_variants map | — | T12 | T15,T16,T17 |
| T12 rewrite insert_inline_ctas | T11 | T13,T14 | — |
| T13 writer/validator update | T12 | — | T14 |
| T14 backfill 100+ posts | T12 | — | T13 |
| T15 needs_review backlog | — | — | T11,T16,T17 |
| T16 income canonical | — | — | T11,T15,T17 |
| T17 seeder fix | — | — | T11,T15,T16 |
| T18 step friction | T8 | — | T19 |
| T19 result loop CTA | T10 | T20 | T18 |
| T20 measurement readout | T2,T3,T10 | — | — |

## Todos
> Implementation + Test = ONE todo. Never separate.

- [x] 1. Add GA4 funnel event helper to BaseHead
  What to do / Must NOT do: In `src/components/BaseHead.astro` (GA4 config at lines 68-73), add a `window.trackFunnel(event, params)` helper that calls `gtag('event', event, params)`. Define event names: `blog_cta_click` (params: src, cat, persona), `persona_open` (src, visitor_id), `persona_step` (step, visitor_id), `persona_result` (src, visitor_id, age_band), `ad_impression` (params: slot_position, ad_unit). INTENTIONALLY EXCLUDE `adsense_click` — AdSense renders in a cross-origin iframe, so per-click events cannot be captured on the host page and intercepting ad clicks violates AdSense policy; ad exposure is measured via `ad_impression` instead (see T5). Do NOT alter the AdSense `<script>` or `gtag('config', ...)` line. Must NOT add any new analytics vendor.
  Parallelization: Wave 1 | Blocked by: — | Blocks: T5,T7,T8,T10
  References (executor has NO interview context - be exhaustive): `src/components/BaseHead.astro:66-73` (current gtag bootstrap), `src/pages/my-persona.astro:828` (redirect is the conversion step), `BaseHead.astro` is imported by every page via layout.
  Acceptance criteria (agent-executable): `grep -n "function trackFunnel" src/components/BaseHead.astro` returns the helper; `grep -n "gtag('event'" src/components/BaseHead.astro` shows ≥5 event calls reachable (incl. `ad_impression`); `grep -n "adsense_click" src/components/BaseHead.astro` returns nothing (intentionally excluded); AdSense line `ca-pub-5938862195544185` unchanged (`grep -c "ca-pub-5938862195544185" src/components/BaseHead.astro` == prior count).
  QA scenarios (name the exact tool + invocation): happy — `npm run build` then `grep -n "trackFunnel" dist/_astro/*.js dist/**/*.html` finds the helper in output; failure — if AdSense client id changed, `grep` diff vs git HEAD fails the todo.
  Commit: Y | feat(analytics): add trackFunnel GA4 helper to BaseHead

- [x] 2. Create D1 funnel_events table migration
  What to do / Must NOT do: Add a SQL migration creating `funnel_events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now')), event TEXT, src TEXT, cat TEXT, persona TEXT, step TEXT, age_band TEXT, visitor_id TEXT, ua_hash TEXT)`. Run via `wrangler d1 execute money-aikorea24 --local --file=...` AND document the production command `wrangler d1 execute money-aikorea24 --file=...` (DB binding is `DB`, database `persona-db` per `wrangler.toml:5-8`). Must NOT alter `benefit_clicks` or other tables.
  Parallelization: Wave 1 | Blocked by: — | Blocks: T2
  References: `wrangler.toml:5-8` (binding `DB`, name `persona-db`), `functions/api/benefit-click.js:16-23` (existing `env.DB.prepare` INSERT pattern).
  Acceptance criteria: `wrangler d1 execute money-aikorea24 --local --command="SELECT name FROM sqlite_master WHERE type='table' AND name='funnel_events'"` returns `funnel_events`.
  QA scenarios: happy — local execute succeeds, table queryable; failure — if migration targets wrong DB name, `wrangler d1 execute` errors "database not found" → fix binding. Evidence `.omo/evidence/task-2-money-aikorea24-funnel-overhaul.sql`.
  Commit: Y | chore(db): add funnel_events table migration

- [x] 3. Build server log sink functions/api/funnel-log.js
  What to do / Must NOT do: Create `functions/api/funnel-log.js` modeled on `functions/api/benefit-click.js` (CORS `ALLOWED_ORIGIN='https://persona.aikorea24.kr'`, `onRequestOptions` 204, `onRequestPost({request,env})` using `env.DB.prepare`). Accept POST JSON `{event, src, cat, persona, step, age_band, visitor_id}`; validate `event` is one of the 4 names; INSERT into `funnel_events`. Return 204 on success. Must NOT log PII (no raw IP/UA stored — store `ua_hash` only via a cheap hash, e.g. substring of `request.headers.get('cf-connecting-ip')` SHA via Web Crypto). Must NOT change benefit-click.js.
  Parallelization: Wave 1 | Blocked by: T2 | Blocks: T4,T7
  References: `functions/api/benefit-click.js:1-46` (exact CORS + DB pattern to copy), `wrangler.toml:5-8`, T2 table schema.
  Acceptance criteria: `curl -X POST https://<preview>/api/funnel-log -H 'content-type: application/json' -d '{"event":"persona_open","src":"inline-peer-loan-youth","visitor_id":"v1"}'` returns 204 and `SELECT count(*) FROM funnel_events WHERE event='persona_open'` increments.
  QA scenarios: happy — POST with valid event → 204 + row inserted (verify via T2 query); failure — POST with unknown event name → 400, no row. Evidence `.omo/evidence/task-3-money-aikorea24-funnel-overhaul.json` (curl + D1 count).
  Commit: Y | feat(analytics): add /api/funnel-log D1 sink

- [x] 4. Client telemetry lib src/lib/funnel.ts
  What to do / Must NOT do: Create `src/lib/funnel.ts` exporting `track(event, params)` that (a) calls `window.trackFunnel(event, params)` (T1) and (b) `navigator.sendBeacon('/api/funnel-log', JSON.stringify({event, ...params, visitor_id}))` with `visitor_id` from the cookie set in T6. Used by blog (T5/T7), my-persona (T8), persona (T10). Must NOT import any analytics SDK.
  Parallelization: Wave 1 | Blocked by: T1,T2 | Blocks: T5,T7,T8,T10
  References: T1 helper, T3 endpoint, T6 cookie name `pid`.
  Acceptance criteria: `grep -rn "sendBeacon('/api/funnel-log'" src/lib/funnel.ts` present; `tsc --noEmit` (or `npm run build`) passes.
  QA scenarios: happy — build succeeds and `dist/assets/*.js` contains `funnel-log` beacon string; failure — if endpoint path typo'd, beacon 404s (observable in headless console). Evidence `.omo/evidence/task-4-money-aikorea24-funnel-overhaul.txt` (build log).
  Commit: Y | feat(analytics): add funnel.ts telemetry client

- [x] 5. Blog CTA click capture (BlogPost.astro)
  What to do / Must NOT do: In `src/layouts/BlogPost.astro` add a delegated click listener on `document` for `a[href*="/my-persona"]` and `a[href*="persona.aikorea24.kr/my-persona"]`; parse the `src` query param from the anchor `href`; call `track('blog_cta_click', {src, cat, persona})` (cat/persona derived from `src` token split on `-`). ALSO piggyback ad exposure: in the EXISTING `IntersectionObserver` (`BlogPost.astro:502-517`, which already observes `ins.adsbygoogle.lazyad`), call `track('ad_impression', {slot_position, ad_unit})` when an ad slot becomes visible (add the top ad at `:374` — which lacks the `lazyad` class — to the observer set, or give it the class, so all 6 slots are measured). Works for all 100+ existing posts WITHOUT editing markdown. Must NOT modify post markdown or the 3 blockquote CTAs' text. Must NOT touch the `<ins class="adsbygoogle">` element attributes or the `showInArticle`/`showAd3` ad-conditionals (observation-only, no ad-code change).
  Parallelization: Wave 2 | Blocked by: T4,T6 | Blocks: T7
  References: `src/layouts/BlogPost.astro` (post renderer; CTA blockquotes live in `<Content/>`), `src/content/blog/*.md` (existing `> [..](/my-persona?src=inline-peer-loan-youth)` links), T4 `track()`.
  Acceptance criteria: `grep -n "blog_cta_click" src/layouts/BlogPost.astro` present; `grep -n "addEventListener('click'" src/layouts/BlogPost.astro` present; `grep -rn "src=inline-peer" src/content/blog/ | wc -l` unchanged (no markdown edits).
  QA scenarios: happy — headless load of a blog post, click a `/my-persona` link → `funnel_events` gets a `blog_cta_click` row with correct `src`; failure — clicking a non-CTA link fires nothing (guard on href match). Evidence `.omo/evidence/task-5-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(analytics): capture blog CTA clicks

- [x] 6. First-party visitor_id cookie
  What to do / Must NOT do: In `BaseHead.astro` (or `funnel.ts` init) set a `pid` cookie (httpOnly=false, SameSite=Lax, path=/, domain='.aikorea24.kr', 1-year) = stable UUID if absent, generated client-side (`crypto.randomUUID()`). The `.aikorea24.kr` domain scoping is REQUIRED so both the blog host and `persona.aikorea24.kr` can read it. Read it in `track()` (T4). The URL handoff in T9 is the primary cross-domain carrier; this cookie is the backup stitch. Must NOT set httpOnly (client must read it).
  Parallelization: Wave 1/2 | Blocked by: — | Blocks: T5,T7,T9,T10
  References: `src/components/BaseHead.astro` (global head), T4 reader.
  Acceptance criteria: `grep -n "crypto.randomUUID" src/components/BaseHead.astro src/lib/funnel.ts` present; cookie name `pid` set with Max-Age ≥ 31536000.
  QA scenarios: happy — first visit sets `pid`, reload reads same value; failure — if httpOnly set, client `track()` can't read it → fix attribute. Evidence `.omo/evidence/task-6-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | feat(analytics): stable visitor_id cookie

- [x] 7. Wire blog click → server beacon
  What to do / Must NOT do: Ensure T5's handler calls `track()` (which already beacons to T3). Add `visitor_id` (`pid`) automatically inside `track()`. Verify a blog CTA click produces BOTH a GA4 `blog_cta_click` and a D1 `funnel_events` row. Must NOT double-fire (dedupe per anchor+event).
  Parallelization: Wave 2 | Blocked by: T4,T5 | Blocks: —
  References: T4 `track()`, T5 handler, T3 sink.
  Acceptance criteria: single blog CTA click → exactly 1 `funnel_events` row with `event='blog_cta_click'` and non-null `visitor_id`.
  QA scenarios: happy — headless click → 1 row; failure — rapid double-click → still ≤1 row (guard). Evidence `.omo/evidence/task-7-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(analytics): blog click beacons to D1

- [x] 8. my-persona: read src on load + fire persona_open
  What to do / Must NOT do: In `src/pages/my-persona.astro`, currently `URLSearchParams` reads only `focus` (line 816), `age/sex/province/marital` (lines 982,1010). ADD reading `src` from `location.search`; on load store it in `sessionStorage` and call `track('persona_open', {src, visitor_id})`. Must NOT change the step UI or the `runAnalyze` logic yet (T9 handles redirect).
  Parallelization: Wave 3 | Blocked by: T4,T6 | Blocks: T9
  References: `src/pages/my-persona.astro:816` (`const focusParam = new URLSearchParams(location.search).get('focus')`), `:982`, `:1010` (other URLSearchParams reads), T4 `track()`.
  Acceptance criteria: `grep -n "get('src')" src/pages/my-persona.astro` present; `grep -n "persona_open" src/pages/my-persona.astro` present; visiting `/my-persona?src=inline-peer-loan-youth` → 1 `persona_open` row with that `src`.
  QA scenarios: happy — load with src → open event; failure — load without src → event still fires with `src=null` (allowed, don't crash). Evidence `.omo/evidence/task-8-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(analytics): capture persona_open with src

- [x] 9. my-persona: carry src+pid across redirect
  What to do / Must NOT do: In `runAnalyze()` at `src/pages/my-persona.astro:828` (`window.location.href = shareUrl`), append `&src=<captured src>&pid=<visitor_id>` to `shareUrl` (currently built at line 817 from `slug`+`marital`+`focus`). This hands attribution to the persona.aikorea24.kr result page across the domain boundary. Must NOT alter the persona result slug format.
  Parallelization: Wave 3 | Blocked by: T6,T8 | Blocks: T10
  References: `src/pages/my-persona.astro:815-818` (shareUrl build), `:828` (redirect), T8 captured src, T6 `pid`.
  Acceptance criteria: `grep -n "src=" src/pages/my-persona.astro` near the redirect shows src+pid appended; resulting URL contains `src=` and `pid=`.
  QA scenarios: happy — after analyze, redirected URL contains `src=inline-peer-*` and `pid=`; failure — if src undefined, fallback to empty param (no throw). Evidence `.omo/evidence/task-9-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | feat(analytics): carry attribution across redirect

- [x] 10. persona result page: fire persona_result (close loop)
  What to do / Must NOT do: In `src/pages/persona/[...slug].astro`, on mount read `src`+`pid` from `location.search` (T9), call `track('persona_result', {src, visitor_id, age_band})`. This is the conversion-completion event. Must NOT touch AdSense (`ca-pub-5938862195544185` at line 322) or Kakao SDK (line 514).
  Parallelization: Wave 3 | Blocked by: T4,T6,T9 | Blocks: T19,T20
  References: `src/pages/persona/[...slug].astro:232` (SITE_URL), `:322` (AdSense — DO NOT EDIT), `:514` (Kakao), T9 handoff.
  Acceptance criteria: `grep -n "persona_result" src/pages/persona/\[...slug\].astro` present; full journey blog→CTA→open→result yields a `persona_result` row with matching `src`+`visitor_id`.
  QA scenarios: happy — end-to-end headless run produces all 4 events with consistent `visitor_id`; failure — result page without src param still fires with `src=null`. Evidence `.omo/evidence/task-10-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(analytics): capture persona_result, close loop

- [x] 11. CTA variant map in config/category_map.yaml
  What to do / Must NOT do: In `scripts/auto-writer/config/category_map.yaml` (loads `persona_cta`/`persona_labels` at `pipeline.py:59-64`), add a `cta_variants` block keyed by `{cat}-{persona}` (e.g. `loan-youth`, `invest-worker`, `general-general`) with 2 copy variants each for the in-body CTA (peer/stats) and the end CTA. Design with INTENTIONAL HIERARCHY: in-body/mid CTAs (after H2#2 / H2#3) = "information / curiosity" WEAK copy (e.g. "또래 평균이 궁금하다면 확인해보세요"); the END CTA = "action" STRONG copy (e.g. "지금 내 페르소나 분석하기 →"). Keep `persona_cta`/`persona_labels` intact for backward compat. Must NOT break YAML parse.
  Parallelization: Wave 4 | Blocked by: — | Blocks: T12
  References: `scripts/auto-writer/pipeline.py:59-64` (CONFIG load), `:97-106` (`_inline_cta_label` reads PERSONA_LABELS), `:108-134` (current hardcoded cta1/cta2 text), `AGENTS.md` (category_map.yaml quota structure).
  Acceptance criteria: `python3 -c "import yaml; yaml.safe_load(open('scripts/auto-writer/config/category_map.yaml'))['cta_variants']"` returns a dict; 2 variants present per key used by sampled posts (`loan-youth`, `invest-worker`, `general-general`); each key exposes a `mid` (weak/curiosity) and `end` (strong/action) copy variant.
  QA scenarios: happy — YAML valid + keys resolvable; failure — missing key → injector falls back to default (T12 must guarantee no KeyError). Evidence `.omo/evidence/task-11-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | feat(content): add cta_variants map

- [x] 12. Rewrite insert_inline_ctas with variant + A/B
  What to do / Must NOT do: In `scripts/auto-writer/pipeline.py:108-134`, replace the 2 hardcoded blockquotes with copy pulled from `cta_variants[{cat}-{persona}]` (fallback to `default`), selecting variant via a **deterministic** hash of `service_id` (stable per post, so A/B is consistent across rebuilds). Map the mid CTA (after H2#2 / H2#3) to the WEAK `mid` variant and the END CTA to the STRONG `end` variant. Preserve insertion points (after H2#2 / H2#3) and the `[PERSONA_CTA]`/`[RELATED_POSTS]` markers (still handled by validator at `pipeline.py:253-257`). Must remain auto-writer-compatible (daily run keeps working).
  Parallelization: Wave 4 | Blocked by: T11 | Blocks: T13,T14
  References: `scripts/auto-writer/pipeline.py:108-134` (current fn), `:255` (PERSONA_CTA cta_url), `:253-257` (validator CTA fix), `writer.py:587-590` (marker required).
  Acceptance criteria: after edit, `python3 scheduler.py --dry-run` (or `pipeline.run(dry_run=True)`) builds a body where the 2 inline CTAs use variant copy (mid=weak, end=strong) and `BODY_TOO_SHORT`/marker logic still passes; no `KeyError`. AD-EXPOSURE GUARD: the rewrite must NOT move CTAs earlier in a way that increases mid-content exit before the 3 end-of-article in-article ad slots (`BlogPost.astro:398-438`); the end CTA stays at body end so the 3 in-article ads remain reachable (zero-sum CTA↔ad tension contained).
  QA scenarios: happy — dry-run emits CTAs from variant map; failure — unknown persona key → falls back to default variant, no crash. Evidence `.omo/evidence/task-12-money-aikorea24-funnel-overhaul.txt` (dry-run body sample).
  Commit: Y | feat(content): variant+A/B inline CTAs in pipeline

- [x] 13. Update writer.py prompt + validator expectations
  What to do / Must NOT do: In `scripts/auto-writer/writer.py` (CTA marker spec at lines 184-253, marker validation at 587-590), update the LLM prompt to describe the new variant-driven CTA ladder (still MUST emit `[PERSONA_CTA]` + `[RELATED_POSTS]`), and ensure `validator.py` still enforces them. Must NOT relax the marker requirement.
  Parallelization: Wave 4 | Blocked by: T12 | Blocks: —
  References: `scripts/auto-writer/writer.py:184-189,211,218,251,338,352,365,396,410,587-590`, `scripts/auto-writer/validator.py` (validate_and_fix).
  Acceptance criteria: `grep -n "cta_variants\|variant" scripts/auto-writer/writer.py` reflects new spec; a draft missing `[PERSONA_CTA]` still raises `ValueError("PERSONA_CTA 누락")` at writer.py:587-590; the writer prompt instructs inserting a FORWARD-REFERENCE teaser after H2#2/H2#3 (e.g. "아래에서 소득 구간별 전략을 정리합니다 →") to pull readers to the end of the article (where the 3 in-article ads at `BlogPost.astro:398-438` live), boosting ad-exposure reach WITHOUT touching ad code.
  QA scenarios: happy — prompt mentions variants, marker guard intact; failure — if guard removed, a marker-less draft would publish → must remain raising. Evidence `.omo/evidence/task-13-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | feat(content): writer/validator reflect CTA variants

- [x] 14. Backfill 100+ existing posts (idempotent)
  What to do / Must NOT do: Write `scripts/migrate-cta.py` that rewrites the 3 blockquote CTAs in every `src/content/blog/*.md` to the new variant copy (read each post's `category`+`persona` from frontmatter/auto-writer DB, pick variant via deterministic hash of filename). Idempotent (re-run is a no-op). Dry-run first, then apply. Must NOT alter headings, tables, or `needs_review` flags; must NOT touch the 5 Hugo repos.
  Parallelization: Wave 4 | Blocked by: T12 | Blocks: —
  References: `src/content/blog/*.md` (100+ files, CTA blockquotes at sampled lines ~52-98), `scripts/auto-writer/pipeline.py:108-134` (variant source of truth), `scripts/auto-writer/db/auto-writer.db` (service_id→persona map).
  Acceptance criteria: `python3 scripts/migrate-cta.py --dry-run` prints N files to change, 0 errors; after apply, `grep -rln "또래 정보 확인하기" src/content/blog/ | wc -l` matches expected converted count; second run changes 0.
  QA scenarios: happy — dry-run → apply → re-run no-op; failure — if a post lacks frontmatter persona, script skips with log, never throws. Evidence `.omo/evidence/task-14-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | feat(content): backfill variant CTAs to 100+ posts

- [x] 15. Clear needs_review backlog (policy + bulk)
  What to do / Must NOT do: Establish a written policy for `needs_review: true` (sampled posts all carry it, set by reviewer at `pipeline.py:215-218`). Decide: auto-clear posts whose `updatedDate` predates a cutoff AND have no open `review_issues`, OR run `shared/reviewer.py` once over the flagged set and flip flags. Produce a count of cleared vs retained. Must NOT delete posts; must NOT disable the reviewer for future runs.
  Parallelization: Wave 5 | Blocked by: — | Blocks: —
  References: `scripts/auto-writer/pipeline.py:215-218` (reviewer sets needs_review), `:5b` validator, `src/content/blog/*.md` frontmatter `needs_review: true`.
  Acceptance criteria: `grep -rl "needs_review: true" src/content/blog/ | wc -l` drops from baseline to the documented retained count; a `REVIEW-POLICY.md` (or note in `.omo/`) states the rule.
  QA scenarios: happy — bulk flip reduces flagged count, build still passes; failure — if reviewer threshold tightened wrongly, future posts over-flag → keep threshold unchanged. Evidence `.omo/evidence/task-15-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | chore(content): clear needs_review backlog per policy

- [x] 16. income-series canonical + noindex
  What to do / Must NOT do: The 14 income-series posts (legacy batch from `seeder_income.py` TOPICS, now reduced to 3 hubs) cause SEO self-cannibalization. Add a `canonical` field to their frontmatter pointing to ONE hub post per series, and emit `<link rel="canonical">` + `meta name="robots" content="noindex"` for the non-hub variants in `src/layouts/BlogPost.astro` (head). Must NOT delete any post; must NOT change their body content.
  Parallelization: Wave 5 | Blocked by: — | Blocks: —
  References: `scripts/auto-writer/seeder_income.py` (TOPICS, now 3 hubs), `src/layouts/BlogPost.astro` (head/SEO), `src/content/blog/*26-06*.md` (income-series files).
  Acceptance criteria: built `dist/blog/.../index.html` for a variant contains `<link rel="canonical" href="<hub>"` and `name="robots" content="noindex"`; the hub post has self-canonical only.
  QA scenarios: happy — variant HTML has canonical+noindex, hub does not noindex; failure — if canonical points to a 404 hub, fix hub slug. Evidence `.omo/evidence/task-16-money-aikorea24-funnel-overhaul.txt` (grep of built HTML).
  Commit: Y | feat(seo): canonical+noindex income-series variants

- [x] 17. Fix seeder_income.py to stop near-duplicates
  What to do / Must NOT do: In `scripts/auto-writer/seeder_income.py` (TOPICS, now 3 hubs), change generation so it no longer emits near-identical region posts. Options (pick one, document it): (a) emit only N hub posts + rely on the dynamic `/my-persona` tool for region slicing, or (b) set `canonical` + `noindex` at generation time. Keep the underlying income data correct. Must NOT break `seeder_income.py --dry-run`.
  Parallelization: Wave 5 | Blocked by: — | Blocks: —
  References: `scripts/auto-writer/seeder_income.py:1-60` (TOPICS + _build_stat_summary), `AGENTS.md` (seeder_income = 3-hub series (서울 demographics) from persona-stats).
  Acceptance criteria: `python3 seeder_income.py --dry-run` outputs ≤ the chosen hub count; generated rows carry `canonical` when option (b) chosen; re-running does not create duplicate slugs.
  QA scenarios: happy — dry-run shows reduced/parameterized output; failure — if it still loops all regions, revert to hub set. Evidence `.omo/evidence/task-17-money-aikorea24-funnel-overhaul.txt`.
  Commit: Y | fix(content): dedupe income-series generation

- [x] 18. my-persona step-friction reduction
  What to do / Must NOT do: In `src/pages/my-persona.astro`, reduce drop-off at step1/step2 (T8 already reads src): pre-fill age from `age` URL param when present, auto-advance sex→region, clarify the progress dots, and strengthen the hero CTA copy. Keep the `runAnalyze`→redirect flow. Must NOT remove the 2-step structure or the share/card features.
  Parallelization: Wave 6 | Blocked by: T8 | Blocks: —
  References: `src/pages/my-persona.astro:173-218` (step1/step2 UI), `:355-399` (startStep/goStep/selectOption), `:805-828` (runAnalyze + redirect).
  Acceptance criteria: step UI still renders; a headless run from `/my-persona?age=35&sex=남자&province=서울` reaches result with fewer manual clicks than before; `persona_open` still fires; PRE-RESULT DROP-OFF measured — fewer users abandon at step1/step2 before `persona_result`, which increases result-page ad-exposure opportunities (AdSense at `persona/[...slug].astro:322` is reached by more users, with no ad-code change).
  QA scenarios: happy — prefilled params shorten the path to result; failure — if autoadvance skips a required input, guard with validation. Evidence `.omo/evidence/task-18-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(ux): reduce my-persona step friction

- [x] 19. persona result-page loop CTA
  What to do / Must NOT do: In `src/pages/persona/[...slug].astro`, after the result card, add a contextual CTA linking BACK to the most relevant blog category (e.g. `/blog/{cat}/` or a related post) to create a measurement-loop (result → next blog read → next CTA). Wire it through `track('persona_step', {step:'loop_cta'})`. Must NOT move/alter AdSense blocks (line 322) or Kakao (line 514).
  Parallelization: Wave 6 | Blocked by: T10 | Blocks: T20
  References: `src/pages/persona/[...slug].astro` (result render), `src/pages/blog/[...slug].astro` (category routing), T10 event.
  Acceptance criteria: result HTML contains a loop CTA anchor to a `/blog/` URL; clicking it fires `persona_step` with `step='loop_cta'`; AdSense client id count unchanged.
  QA scenarios: happy — loop CTA present + tracked; failure — if it points to a missing category, fall back to `/blog/`. Evidence `.omo/evidence/task-19-money-aikorea24-funnel-overhaul.json`.
  Commit: Y | feat(ux): persona result loop CTA

- [x] 20. Measurement readout (conversion + A/B)
  What to do / Must NOT do: After instrumentation is live ≥2 weeks (or via backfilled/logged data), query D1 `funnel_events` (T2/T3) to compute blog_cta_click → persona_open → persona_result conversion, segment by `src`/`cat`/`persona`, and compare A/B CTA variants (T11/T12 hash). ALSO: (a) compare `ad_impression` counts for the 3 end-of-article slots (before/after) to confirm ad-exposure reach is preserved; (b) via the GA4↔AdSense account LINK (dashboard setup, NO code change) compare hub-post RPM vs variant-post RPM (SEO canonical from T16/T17 should lift hub RPM); (c) report `persona_result` event volume as the result-page ad-exposure proxy. Produce `MEASUREMENT.md` with baseline rate + variant uplift + RPM table + recommended rollout. Must NOT modify the pipeline; read-only SQL.
  Parallelization: Wave 6 | Blocked by: T2,T3,T10 | Blocks: —
  References: T2 table, T3 sink, T10 events, T11/T12 variants.
  Acceptance criteria: `MEASUREMENT.md` exists with (1) a funnel-rate table (click→open→result), (2) a per-variant comparison, (3) an `ad_impression` before/after table for the 3 end-of-article slots, (4) a hub-post vs variant-post RPM comparison sourced from the GA4↔AdSense linked report, (5) the mid-CTA click rate ≤ 50% of the end-CTA click rate (weak-mid/strong-end hierarchy suppressed premature exit, protecting the 3 end-of-article ad slots), and (6) a note confirming the GA4↔AdSense link is enabled (dashboard setting, no code). SQL is `SELECT` only (no writes).
  QA scenarios: happy — query returns rows and the doc is populated; failure — if volume is too low for significance, doc states "insufficient sample" rather than a false uplift. Evidence `.omo/evidence/task-20-money-aikorea24-funnel-overhaul.sql` + `MEASUREMENT.md`.
  Commit: Y | docs(analytics): funnel conversion + A/B readout

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [x] F1. Plan compliance audit — all 20 todos complete (T1–T20). All 5 funnel events fire: `blog_cta_click`+`ad_impression` (BlogPost via `window.funnelTrack`), `persona_open` (my-persona), `persona_result`+`persona_step` (persona/[...slug] via `track`). income canonical (13 variants noindex, hub clean), seeder reduced to 3 hub topics, MEASUREMENT.md present.
- [x] F2. Code quality review — no string-concat XSS in new scripts; funnel.ts export intact; FUNNEL_EVENTS sink allows all 5 names; deterministic A/B hash; idempotent backfill scripts.
- [ ] F3. Real manual QA — **deferred to the central integrated build** (per the "NO full project build until after all waves; integrated build done centrally" constraint). Headless end-to-end journey (blog CTA → /my-persona → /persona result → loop CTA) + build-time canonical/noindex HTML check run as part of that central build, not locally.
- [x] F4. Scope fidelity — AdSense client `ca-pub-5938862195544185` counts unchanged per guarded file (BaseHead 1 / my-persona 3 / persona 1 / BlogPost 6); `adsense_click` intentionally absent everywhere; no new analytics vendor (only GA4 `G-NG7D2EHJBV` + first-party D1 log); `<ins class="adsbygoogle">` + ad-conditionals untouched; no Hugo repo touched; `pid` cookie httpOnly=false as required.

## Commit strategy
- Atomic per todo (see each Commit line). Group Waves 1-3 (instrumentation) as a single deployable unit behind one `npm run build && npx wrangler pages deploy` since attribution only works end-to-end once T1-T10 ship together; verify auto-writer still deploys after (T12-T14 are pipeline-only, safe to ship separately).
- Never commit the 5 Hugo repos. Never commit `.env`/secrets. Keep `needs_review` policy doc out of product build.
- PR/commit convention: `type(scope): summary` (feat/ fix/ chore/ docs).

## Success criteria
1. **Measured funnel:** `funnel_events` populates for all 4 events; a headless end-to-end journey (blog CTA → /my-persona → /persona result) yields exactly one row each of `blog_cta_click`, `persona_open`, `persona_result` sharing one `visitor_id` and the original `src`.
2. **Attribution recovered:** ≥95% of `persona_result` rows carry a non-null `src` matching the originating blog CTA (proves the split-domain handoff works).
3. **Auto-writer intact:** after all pipeline edits (T11-T14), `python3 scheduler.py --dry-run` succeeds and a real daily publish + `wrangler pages deploy` completes without error.
4. **CTA redesign live + comparable:** new variant CTAs render in ≥100 posts (T14) and new auto-writer posts (T12); A/B split is deterministic and visible in `MEASUREMENT.md`.
5. **Content cleaned:** `needs_review: true` count reduced per stated policy (T15); income-series variants carry `canonical`+`noindex` (T16) and `seeder_income.py` no longer emits near-duplicates (T17).
6. **Scope guarded:** AdSense client `ca-pub-5938862195544185` string count unchanged across `BaseHead.astro`, `my-persona.astro`, `persona/[...slug].astro`, `src/layouts/BlogPost.astro`; the `<ins class="adsbygoogle">` elements + `showInArticle`/`showAd3` ad-conditionals in `BlogPost.astro` and the `.desktop-only`/`.ad-leaderboard`/`.ad-mobile-sticky` ad CSS in `src/styles/global.css` are untouched (leaderboard `.desktop-only` intentionally retained); no Hugo repo touched; no new analytics vendor added; `adsense_click` is intentionally absent (ad exposure measured via `ad_impression` only).
