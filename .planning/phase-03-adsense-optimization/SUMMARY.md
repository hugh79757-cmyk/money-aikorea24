# SUMMARY — Phase 03: AdSense Revenue Optimization

**Status:** Complete ✅ — with divergences (verified against code 2026-07-09)
**Plans:** T1–T7 (original PLAN.md) + separate funnel-overhaul plan
**Verification method:** file/function existence + import wiring in `BlogPost.astro` / `BaseHead.astro` / `global.css` / `consts.ts`

---

## Original PLAN.md tasks — code reality

| Task | Plan intent | Code reality | Verdict |
|------|-------------|----------------|---------|
| T1 | Extract `ADSENSE_CLIENT` const, replace 12+ inline `ca-pub` refs | `consts.ts:5` has `ADSENSE_CLIENT`. **But 12 live `src/` files still hardcode `ca-pub-5938862195544185`** (incl. the 3 `adsense/*.html` partials, `BlogPost.astro`×6, `my-persona.astro`, `persona/[...slug].astro`, community pages). | ⚠️ PARTIAL — const created, centralization incomplete (plan verify = `grep` returns 0; actual = 12) |
| T2 | `in-article.html` partial | `src/components/adsense/in-article.html` exists | ✅ |
| T3 | `leaderboard.html` partial | `src/components/adsense/leaderboard.html` exists | ✅ |
| T4 | `mobile-sticky.html` partial | `src/components/adsense/mobile-sticky.html` exists | ✅ |
| T5 | Marker-based in-article insertion (`<!--AD1/2/3-->`) in `BlogPost.astro` | Ad slots present via **existing template `<!-- 광고 1/2/3 -->` placeholders** (BlogPost.astro:511 `querySelectorAll('ins.adsbygoogle.lazyad')`), NOT the plan's `AD1/2/3` markers. Result-page 4 ad slots added separately via funnel plan. | 🔀 DIVERGENT — slots work, mechanism differs from plan |
| T6 | `BaseHead.astro` global `IntersectionObserver` lazy-load | `IntersectionObserver` present in `BlogPost.astro` + `persona/[...slug].astro` (NOT `BaseHead.astro` as planned). `ins.adsbygoogle.lazyad` elements exist. | ✅ (location diverged) |
| T7 | `global.css` ad styles + dark-mode + responsive | `global.css:23,419,424,431,443,455` — `.ad-inarticle` / `.ad-leaderboard` / `.ad-mobile-sticky` / `ins.adsbygoogle` / dark-mode / `data-ad-status="unfilled"` all present | ✅ |

---

## Separate funnel-overhaul plan (superceded execution)

`.omo/plans/money-aikorea24-funnel-overhaul.md` drove work NOT in the original PLAN.md:
- Result-page 4 ad slots + `ad_impression` tracking (`1d73e1a`)
- CTA attribution tokens — `&src=entity-card-{cat}` / `&src=inline-component-{cat}` (`0c638fd`)
- Loop CTA deterministic diversity — hashed persona-key selection (`14f8328`)
- Commits `7ebe34d` (GA4+D1 telemetry, CTA redesign, income canonical cleanup) + `4cc7945` (funnel plan doc)

These are committed and build-clean (2459 pages, 0 errors as of 2026-07-09).

---

## Notes / open items

- **T1 incomplete:** 12 files still hardcode the publisher ID. Functionally fine (single value), but the plan's single-source-of-truth goal is unmet. The 3 `adsense/*.html` partials cannot easily consume the TS `const` (raw HTML fragments) — acceptable, but `BlogPost.astro` and page `.astro` files could interpolate `ADSENSE_CLIENT` and don't.
- **tax category deleted** (this session, 2026-07-09): was 0 posts / no data source mapped to it. Not a Phase-03 task — separate data-source gap. Build verified clean after removal.
- Phase-03 has **no prior SUMMARY** until this file; original PLAN.md `## Verification` (8 numbered items) reflects intent, not the funnel divergence above.
