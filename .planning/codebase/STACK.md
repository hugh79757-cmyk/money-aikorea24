# Technology Stack

**Analysis Date:** 2026-07-01

## Languages

**Primary:**
- TypeScript (Node.js runtime) — Astro frontend, Cloudflare Pages Functions (`functions/`), `src/lib/` utilities, build scripts (`scripts/*.mjs`)
- Python 3.14.5 — AI content pipeline (`scripts/auto-writer/`), manual publisher (`scripts/manual-publisher/`), data fetching scripts

**Secondary:**
- JavaScript (ESM) — Cloudflare Pages Functions (`functions/api/**/*.js`)
- Astro (`.astro`) — Component and page templates (`src/pages/`, `src/components/`)

## Runtime

**Environment:**
- Node.js >=22.12.0 (enforced via `package.json` `engines`)
- Python 3.14.5

**Package Manager:**
- npm (v25.2.1)
- Lockfile: `package-lock.json` (present)

## Frameworks

**Core:**
- **Astro 6.1.8** — SSG (static site generation, `output: 'static'`). All frontmatter runs at build time, not on-request. Config: `astro.config.mjs`
- **@astrojs/cloudflare ^13.5.2** — Cloudflare Pages adapter (deploys static output to Pages)
- **@astrojs/mdx ^5.0.3** — MDX support for content collections
- **@astrojs/sitemap ^3.7.2** — XML sitemap generation (filters out 1-year granular persona pages)
- **@astrojs/rss ^4.0.18** — RSS feed generation

**Styling:**
- **Tailwind CSS v4** with `@tailwindcss/vite` plugin (PostCSS-free, Vite-native)
- Utility-first approach, dark mode via `src/styles/` (no `tailwind.config.*` — v4 uses CSS-based config)

**Build/Dev:**
- **Vite** (Astro-internal) — Build tooling
- **sharp ^0.34.3** — Image processing (Astro uses for optimization)
- **remark-gfm ^4.0.1** — GitHub Flavored Markdown support in Astro markdown pipeline

## Databases

**Cloudflare D1:**
- **Binding name:** `DB` (configured in `wrangler.toml`)
- **Database name:** `persona-db`
- **Database ID:** `476a89e1-4e2b-4b45-a2f8-e195127e5d32`
- Used by: Cloudflare Pages Functions for community CRUD, auth, benefit-click analytics
- Tables: `users`, `persona_posts`, `persona_comments`, `persona_likes`, `benefit_clicks`

**SQLite (Local):**
- **Location:** `scripts/auto-writer/db/auto-writer.db`
- Used by: auto-writer AI pipeline (3 tables: `services`, `publish_ledger`, `fetch_meta`)
- Not deployed to production

## Static Data Files

**JSON files in `public/` (served as static assets):**
| File | Size | Purpose |
|------|------|---------|
| `persona-stats.json` | 25 MiB (2,244 keys) | Full persona statistics, **build-time only** — removed before Cloudflare deploy (25 MiB file limit) |
| `persona-stats-decade.json` | 4.3 MiB (204 keys) | Decade-aggregated subset, fetched at runtime by `my-persona.astro` |
| `benefits-clean.json` | 3.4 MiB | Curated benefit data from gov24 |
| `benefits-curated.json` | 22 KiB | Top 25 curated benefits |
| `welfare-central.json` | 313 KiB | Central government welfare data |
| `welfare-local.json` | 3.3 MiB | Local government welfare data |
| `blog-match.json` | 10 KiB | Blog-to-persona matching index |

**Source data files in `src/data/`:**
| File | Purpose |
|------|---------|
| `wage-table.json` | Wage table by occupation with gender/age adjustment coefficients |
| `job-category-map.json` | Job name → 10 category mappings |
| `decision-cards.json` | Persona decision card data |

## Key Dependencies

**Frontend (package.json dependencies):**
| Package | Version | Purpose |
|---------|---------|---------|
| `astro` | ^6.1.8 | Core framework |
| `@astrojs/cloudflare` | ^13.5.2 | Cloudflare Pages deployment |
| `@astrojs/mdx` | ^5.0.3 | MDX content |
| `@astrojs/rss` | ^4.0.18 | RSS feed generation |
| `@astrojs/sitemap` | ^3.7.2 | Sitemap generation |
| `tailwindcss` | ^4.3.0 | Utility CSS |
| `@tailwindcss/vite` | ^4.3.0 | Tailwind v4 Vite plugin |
| `sharp` | ^0.34.3 | Image processing |
| `remark-gfm` | ^4.0.1 | GFM markdown support |

**Dev Dependency:**
| Package | Version | Purpose |
|---------|---------|---------|
| `fast-xml-parser` | ^5.8.0 | XML parsing (used by data fetch scripts) |

**Python Dependencies (auto-writer):**
| Package | Purpose |
|---------|---------|
| `openai` | OpenAI-compatible client for NVIDIA NIM / DeepSeek API |
| `requests` | HTTP client for data fetching, Telegram notifications |
| `boto3` / `botocore` | S3-compatible client for Cloudflare R2 uploads |
| `Pillow` | Thumbnail generation (800x800, category backgrounds) |
| `PyYAML` | Config file parsing (`config/category_map.yaml`) |
| `python-dotenv` | Environment variable loading |
| `boto3` | R2 uploads (also in manual-publisher) |

## Build & Deployment Pipeline

**Build Process:**
1. `npm run build` → triggers `prebuild` → `generate-decade-stats.mjs` → then `astro build`
2. Output: `./dist/` directory (static files + `_worker.js` for Pages Functions)

**Deploy Scripts:**

`scripts/deploy.sh` (manual deploy via `npm run deploy`):
1. Pre-check: verifies 3 Cloudflare Secrets (`KAKAO_REST_KEY`, `KAKAO_CLIENT_SECRET`, `SESSION_SECRET`)
2. `npm run build`
3. `rm -f dist/persona-stats.json` (25 MiB exceeds Cloudflare 25 MiB file limit)
4. `git add -A && git commit && git push origin main`
5. `wrangler pages deploy dist --project-name money-aikorea24 --branch main --commit-dirty=true`

`scripts/auto-writer/shared/build_deploy.py` (auto-writer pipeline):
1. `npm run build` (subprocess, 300s timeout)
2. `os.remove("dist/persona-stats.json")`
3. `wrangler pages deploy dist/ --project-name money-aikorea24 --commit-dirty=true`

`scripts/manual-publisher/deployer.py` (manual publisher):
1. `npm run build` (with auto-fix on content collection schema errors, 1 retry)
2. `wrangler pages deploy dist/ --project-name money-aikorea24 --commit-dirty=true`
3. Telegram notification on success/failure

**Deployment Target:**
- **Cloudflare Pages** — project `money-aikorea24`
- Domain: `https://persona.aikorea24.kr`
- Build output: `./dist`
- Compatibility date: `2024-12-01`

## Content Collections

**Astro Content Collections** (validated via Zod in `src/content.config.ts`):
- `blog` — from `src/content/blog/**/*.{md,mdx}`
- `nomad` — from `src/content/nomad/**/*.{md,mdx}`

**Collections categories** (`src/consts.ts`):
- `insurance` | `invest` | `loan` | `tax` | `general`

## Platform Requirements

**Development:**
- Node.js >=22.12.0
- npm
- Python 3.14+
- Cloudflare account (for D1, Pages, R2)
- Wrangler CLI (for local dev + deploy)

**Production:**
- Cloudflare Pages (static + Functions)
- Cloudflare D1 (`persona-db`)
- Cloudflare R2 (blog thumbnail storage)
- 3 required Cloudflare Pages Secrets: `KAKAO_REST_KEY`, `KAKAO_CLIENT_SECRET`, `SESSION_SECRET`

## Environment Configuration

**Fallback chain:** `~/.env.common` (global) → `.env` (project) — project values override global
- Python loader: `scripts/load_env.py` / `from load_env import env`
- Node.js loader: `lib/env-loader.ts` → `import './lib/env-loader.js'`
- Cloudflare Functions: Pages Secrets only (no `.env` access)

## CI/CD

**No GitHub Actions** — CI/CD is handled by:
- `launchd` on the developer machine:
  - `com.aikorea24.auto-writer.plist` — daily at 09:00
  - `com.aikorea24.manual-publisher.plist` — every 30 minutes
- Manual deploy: `npm run deploy` → `scripts/deploy.sh`

## Notable Absences

- **No test framework** — vitest/jest not configured; no test files found (`*.test.*`, `*.spec.*`)
- **No ESLint/Prettier/Biome** — no linting or formatting tools configured
- **No Docker** — no `Dockerfile` or `docker-compose.yml`
- **No CI/CD platform** — no GitHub Actions, no GitLab CI

---

*Stack analysis: 2026-07-01*
