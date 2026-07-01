# Codebase Structure

**Analysis Date:** 2026-07-01

## Directory Layout

```
money-aikorea24/
├── src/                          # Astro source (SSG pages, components, styles)
│   ├── pages/                    # Route definitions (.astro, .md, .xml.js, .json.js)
│   ├── components/               # Reusable Astro components
│   │   └── ui/                   # Primitive UI components (Badge, Button, Card)
│   ├── layouts/                  # Page layout wrappers (BlogPost)
│   ├── lib/                      # Build-time utility functions
│   ├── data/                     # Static JSON data (wage tables, job maps)
│   ├── content/                  # Content collections (blog, nomad)
│   │   ├── blog/                 # ~169 blog posts (.md)
│   │   └── nomad/                # Digital nomad guides (.md)
│   ├── styles/                   # CSS (tailwind.css, design-tokens.css, global.css)
│   ├── content.config.ts         # Zod schemas for content collections
│   ├── consts.ts                 # App-wide constants (SITE_TITLE, COLLECTIONS)
│   └── assets/                   # Static images (blog placeholders, fonts)
├── functions/                    # Cloudflare Pages Functions (runtime API)
│   ├── api/
│   │   ├── _shared/session.js    # HMAC-SHA256 session token helpers
│   │   ├── auth/
│   │   │   ├── callback/kakao.js # Kakao OAuth callback handler
│   │   │   └── logout.js         # Session destruction
│   │   ├── community/
│   │   │   ├── posts.js          # Community post CRUD (list/create/delete)
│   │   │   ├── posts/[id].js     # Single post get/delete
│   │   │   ├── comments.js       # Comment CRUD
│   │   │   └── like.js           # Like/unlike toggle
│   │   └── benefit-click.js      # Benefit click tracking (D1)
│   ├── community/[id].js         # Community SPA passthrough router
│   └── og/index.js               # OG image redirect → cards subdomain
├── scripts/                      # Python/Node.js automation and pipelines
│   ├── auto-writer/              # AI blog content generation pipeline
│   │   ├── pipeline.py           # Main pipeline orchestrator (12-step)
│   │   ├── scheduler.py          # CLI entry point (--dry-run, --status, --fetch)
│   │   ├── writer.py             # LLM article generation + proofreading
│   │   ├── validator.py          # Content validation, slug gen, frontmatter
│   │   ├── fetcher.py            # Gov24 data fetcher
│   │   ├── fetcher_loan_fin.py   # Finlife loan/financial product fetcher
│   │   ├── fetcher_invest.py     # data.go.kr investment data fetcher
│   │   ├── seeder_income.py      # Income series seed post generator
│   │   ├── config/
│   │   │   └── category_map.yaml # Category quotas, persona CTAs, labels
│   │   ├── db/
│   │   │   └── auto-writer.db    # SQLite state DB (services, publish_ledger)
│   │   └── shared/
│   │       ├── db_utils.py       # SQLite CRUD for pipeline state
│   │       ├── thumbnail_gen.py  # Pillow-based 800x800 card thumbnail gen
│   │       ├── reviewer.py       # LLM content review (Qwen2.5 14B)
│   │       ├── build_deploy.py   # npm build + wrangler deploy
│   │       ├── notifier.py       # Telegram error notifications
│   │       └── persona_stats.py  # Persona stats JSON reader
│   ├── manual-publisher/         # User-inbox blog publishing pipeline
│   │   ├── publisher.py          # Main pipeline (12-step)
│   │   ├── watcher.py            # inbox/ file watcher + done.json tracking
│   │   ├── transformer.py        # Frontmatter extraction + transformation
│   │   ├── classifier.py         # Keyword-based category classification
│   │   ├── validator.py          # Content validation + normalize slug
│   │   ├── thumbnail.py          # 1024x1024 thumbnail gen + R2 upload
│   │   ├── entity_injector.py    # Persona-entity markers + related posts
│   │   ├── deployer.py           # Build + deploy with auto-fix retry logic
│   │   ├── filter.py             # Dead code (imported but never called)
│   │   └── r2_upload.py          # R2 file upload utility
│   ├── deploy.sh                 # CLI deploy script (build → git push → wrangler)
│   ├── generate-decade-stats.mjs # Prebuild: extract 204 decade keys from full JSON
│   ├── load_env.py               # .env → .env.common fallback loader
│   └── [other utilities]         # Card generators, data fetch scripts, etc.
├── public/                       # Static assets (served as-is to dist/)
│   ├── persona-stats.json        # Full 2,244-key persona dataset (~25 MiB)
│   ├── persona-stats-decade.json # 204-key decade subset (~4 MiB)
│   ├── benefits-clean.json       # All government benefits data
│   ├── benefits-curated.json     # Curated benefit picks (25 items)
│   ├── welfare-central.json      # Central government welfare programs
│   ├── welfare-local.json        # Local government welfare programs
│   ├── blog-match.json           # Blog-to-persona matching data
│   ├── bg_img/                   # 38 background images for card thumbnails
│   ├── cards/                    # Persona card JPGs (desktop)
│   ├── cards-mobile/             # Persona card JPGs (mobile)
│   └── blog-thumbnails/          # Blog OG thumbnail images
├── astro.config.mjs              # Astro config (static output, sitemap, MDX)
├── wrangler.toml                 # Cloudflare config (D1 binding)
├── package.json                  # Node.js dependencies & scripts
├── tsconfig.json                 # TypeScript configuration
└── _headers                      # Cloudflare Pages custom headers
```

## Directory Purposes

**`src/pages/`:**
- Purpose: All route definitions for the Astro SSG site
- Contains: `.astro` page components, `.xml.js` RSS endpoints, `.json.js` search index
- Key files:
  - `index.astro` — Homepage (persona hero, urgent benefits, blog feed, persona index hub for 204 decade pages)
  - `my-persona.astro` — Multi-step SPA input → persona result (client-side rendered)
  - `persona/[...slug].astro` — 2,244 static persona pages generated by `getStaticPaths()`
  - `blog/[...slug].astro` — Individual blog post pages
  - `blog/index.astro` — Blog listing by category
  - `blog/category/[category]/[...slug].astro` — Category-filtered blog list
  - `community/index.astro` — Community board (client-rendered SPA shell)
  - `community/[id].astro` — Community post detail (client-rendered SPA shell)
  - `community/write.astro` — Community post creation page
  - `benefits/index.astro` — Benefits search page
  - `auth/login.astro` — Kakao OAuth login page
  - `nomad/[...slug].astro`, `nomad/index.astro` — Digital nomad guides
  - `rss.xml.js` — RSS feed endpoint
  - `search.json.js` — Search index JSON endpoint

**`src/components/`:**
- Purpose: Reusable Astro components used across pages
- Contains: UI-specific `.astro` components
- Key files:
  - `BaseHead.astro` — Global `<head>` (OG tags, GA4, AdSense, Pretendard font, canonical URL)
  - `Header.astro` — Top navigation (parses `session_ui` cookie for login state)
  - `Footer.astro` — Site footer
  - `BenefitCards.astro` — Benefit matching cards display
  - `WelfareCards.astro` — Welfare matching cards display
  - `DecisionCards.astro` — Top-3 suitable benefits cards
  - `PersonaBlogRecommend.astro` — Blog recommendations per persona
  - `InlinePersonaCTA.astro` — Inline CTA for blog posts (→ my-persona)
  - `FormattedDate.astro` — Date formatting utility
  - `JsonLd.astro` — JSON-LD structured data injection
  - `SearchBar.astro` — Client-side search widget
  - `ThemeToggle.astro` — Dark/light mode toggle
  - `FloatingFab.astro` — Floating action button
  - `AiTip.astro` — AI tip component
  - `HeaderLink.astro` — Navigation link component
  - `Disclaimer.astro` — Disclaimer display
  - `ui/Badge.astro` — Primitive badge component
  - `ui/Button.astro` — Primitive button component
  - `ui/Card.astro` — Primitive card component
  - `ui/index.ts` — Re-export barrel file

**`src/lib/`:**
- Purpose: Build-time utility functions used in Astro frontmatter
- Contains: TypeScript modules with no runtime dependencies (all executed at build time)
- Key files:
  - `benefitMatcher.ts` — Score-based benefit eligibility matching
  - `welfareMatcher.ts` — Region/life-stage welfare matching
  - `personaMatcher.ts` — Persona matching utilities
  - `deadlineExtractor.ts` — Deadline date extraction from benefit data

**`src/data/`:**
- Purpose: Static JSON data files loaded at build time
- Contains: Structured data for wage estimation, job categorization, decision cards
- Key files:
  - `wage-table.json` — Job category wages + age/sex/region correction factors
  - `job-category-map.json` — Job name → 10 categories mapping
  - `decision-cards.json` — Per-persona decision card data

**`src/content/`:**
- Purpose: Astro content collections (Zod-validated markdown)
- Contains: `blog/` (~169 posts) and `nomad/` (6 guides)
- Key files:
  - `blog/*.md` — Blog posts in categories (insurance, invest, loan, tax, general)
  - `nomad/*.md` — Digital nomad guides

**`src/layouts/`:**
- Purpose: Page layout templates
- Contains: `BlogPost.astro` — Layout wrapper for blog post pages (TOC, related posts, content)

**`src/styles/`:**
- Purpose: CSS files
- Contains:
  - `tailwind.css` — Tailwind CSS v4 imports
  - `design-tokens.css` — Design token CSS variables
  - `global.css` — Global base styles
  - `utilities.css` — Additional utility classes

**`functions/`:**
- Purpose: Cloudflare Pages Functions (runtime API)
- Contains: One `.js` file per route, following Cloudflare's `onRequest[Method]` export pattern
- Key files:
  - `api/_shared/session.js` — `createSessionToken()`, `verifySessionToken()`, `getSession()` HMAC-SHA256 helpers
  - `api/auth/callback/kakao.js` — Kakao OAuth 2.0 token exchange, user upsert, session creation
  - `api/auth/logout.js` — Clear session cookies (both host and domain variants)
  - `api/community/posts.js` — `onRequestGet` (list), `onRequestPost` (create), `onRequestDelete`
  - `api/community/posts/[id].js` — `onRequestGet` (single), `onRequestDelete`
  - `api/community/comments.js` — `onRequestGet`, `onRequestPost`, `onRequestDelete`
  - `api/community/like.js` — `onRequestPost` (toggle)
  - `api/benefit-click.js` — `onRequestGet`, `onRequestPost` (track benefit clicks in D1)
  - `community/[id].js` — Passthrough router: serves `community/_/index.html` for dynamic IDs
  - `og/index.js` — Redirect `/og/?region=&sex=&age=` → card image URL

**`scripts/`:**
- Purpose: Automation scripts and content pipelines
- Contains: Two independent Python blog generation systems + Node.js utilities
- See "Key File Locations" below for detail

**`public/`:**
- Purpose: Static files copied verbatim to `dist/` during build
- Contains: Large JSON datasets, persona card images, blog thumbnails, background images
- **Critical:** `persona-stats.json` (~25 MiB) exceeds Cloudflare's 25 MiB per-file limit and is deleted from `dist/` before deployment

## Key File Locations

**Entry Points:**
- `src/pages/index.astro`: Homepage — renders blog feed, persona hero, benefits urgency section, persona index hub (204 decade links)
- `src/pages/persona/[...slug].astro`: Persona detail pages — 2,244 routes via `getStaticPaths()`. Reads persona-stats.json at build time
- `src/pages/my-persona.astro`: Interactive SPA — multi-step form → client-side fetch of `persona-stats-decade.json` → display results
- `src/pages/community/index.astro`: Community board — client-rendered SPA (JS fetches `/api/community/posts`)
- `scripts/auto-writer/scheduler.py`: Auto-writer entry (CLI or launchd 09:00 daily)
- `scripts/manual-publisher/publisher.py`: Manual-publisher entry (launchd every 30 min)
- `scripts/deploy.sh`: Full deploy script (build → git commit → wrangler deploy)

**Configuration:**
- `astro.config.mjs`: Astro config — static output, sitemap (filters 1-year persona pages), MDX, Tailwind
- `wrangler.toml`: Cloudflare Pages config — D1 database binding (`persona-db`)
- `package.json`: Node.js — `>=22.12.0`, scripts: `dev`, `build`, `prebuild` (generate-decade-stats), `deploy`
- `tsconfig.json`: TypeScript configuration
- `src/content.config.ts`: Zod schema for blog/nomad collections (title, description, draft, category, tags)
- `src/consts.ts`: Site constants — `SITE_TITLE`, `SITE_DESCRIPTION`, `SITE_URL`, `COLLECTIONS` (5 categories)

**Core Logic:**
- `src/lib/benefitMatcher.ts`: `matchBenefit()` + `getBenefitMatches()` — benefit eligibility scoring
- `src/lib/welfareMatcher.ts`: `matchWelfare()` — welfare region+life-stage matching
- `functions/api/_shared/session.js`: `createSessionToken()`, `verifySessionToken()`, `getSession()`
- `scripts/auto-writer/pipeline.py`: 12-step pipeline orchestrator (fetch → filter → generate → review → validate → thumbnail → deploy)
- `scripts/auto-writer/writer.py`: LLM text generation with 4-tier fallback chain
- `scripts/auto-writer/shared/db_utils.py`: SQLite CRUD for pipeline state management

**Testing:**
- No test framework configured. No `*.test.*` or `*.spec.*` files found.

## Naming Conventions

**Files:**
- `.astro` — Astro page/component files
- `.ts` — TypeScript (utilities, matchers)
- `.js` — Cloudflare Functions (ES modules), Node.js scripts
- `.py` — Python pipeline scripts
- `.mjs` — Node.js ESM scripts (utilities, generators)
- `.md` — Blog/content markdown
- `.json` — Static data files (both `src/data/` and `public/`)
- `.yml/.yaml` — Pipeline configuration
- `.toml` — Cloudflare/wrangler configuration

**Directories:**
- `src/pages/` mirrors the site URL structure (flat files = routes)
- `functions/` mirrors API URL paths (`api/community/posts.js` → `/api/community/posts`)
- `scripts/auto-writer/shared/` — shared modules between pipeline steps
- Component files use `PascalCase.astro` (e.g., `BaseHead.astro`, `BenefitCards.astro`)

## Where to Add New Code

**New Feature (Static Page):**
- Add `.astro` file in `src/pages/`
- If page needs data, use frontmatter to import from `src/lib/`, `src/data/`, or `public/`
- Components in `src/components/`
- Layout in `src/layouts/`

**New API Endpoint:**
- Add `.js` file under `functions/api/` following the file-path = URL-path pattern
- Export `onRequestGet`, `onRequestPost`, `onRequestDelete`, etc.
- Access D1 via `env.DB`
- Use `getSession()` from `../_shared/session.js` for auth

**New Blog Post (AI-generated):**
- Let `scripts/auto-writer/pipeline.py` handle it automatically
- Or drop `.md` file in `inbox/` for `scripts/manual-publisher` to process
- Manually: create `.md` in `src/content/blog/` with valid frontmatter matching `src/content.config.ts` schema

**New Component:**
- Add to `src/components/` with PascalCase name
- For primitive UI: add to `src/components/ui/` and export from `index.ts`
- Import into pages or other components

**Utilities:**
- Build-time helpers: `src/lib/` (TypeScript, imported in `---` frontmatter)
- Pipeline utilities: `scripts/auto-writer/shared/` or `scripts/manual-publisher/` (Python)

## Special Directories

**`dist/`:**
- Purpose: Astro build output (generated)
- Generated: Yes (by `astro build`)
- Committed: No (in `.gitignore`)
- Deployed to Cloudflare Pages

**`node_modules/`:**
- Purpose: npm dependencies
- Generated: Yes (by `npm install`)
- Committed: No (in `.gitignore`)

**`.venv/`:**
- Purpose: Python virtual environment (shared by auto-writer and manual-publisher)
- Generated: Yes
- Committed: No

**`inbox/`:**
- Purpose: Drop directory for manual-publisher — place `.md` files here to publish
- Generated: No
- Committed: No (user-managed)

**`scripts/auto-writer/db/`:**
- Purpose: SQLite database for auto-writer state
- Generated: Yes (by pipeline on first run)
- Committed: No

**`scripts/auto-writer/logs/`, `logs/`:**
- Purpose: Pipeline log files
- Generated: Yes
- Committed: No

**`.planning/`:**
- Purpose: Codebase planning documents (this file)
- Generated: Yes (by GSD commands)
- Committed: Yes

---

*Structure analysis: 2026-07-01*
