# Coding Conventions

**Analysis Date:** 2026-07-01

## Naming Patterns

**Files:**
- **TypeScript/JavaScript**: `kebab-case.ts` / `kebab-case.js` — e.g. `benefitMatcher.ts`, `deadlineExtractor.ts`, `welfareMatcher.ts`, `benefit-click.js`
- **Astro components**: `PascalCase.astro` — e.g. `BaseHead.astro`, `Header.astro`, `Button.astro`, `FormattedDate.astro`
- **Python**: `snake_case.py` — e.g. `pipeline.py`, `db_utils.py`, `thumbnail_gen.py`, `fetcher_loan_fin.py`
- **API routes (Cloudflare Pages Functions)**: nested under `functions/` with `[param].js` for dynamic params — e.g. `functions/api/community/posts/[id].js`
- **Blog content**: `slug-{service_id[-6:]}.md` pattern — e.g. `30대-직장인-코스피-200-ETF로-시장-평균-수익에-투자하는-법-총정리-260622.md`

**Functions:**
- **TypeScript**: `camelCase` — e.g. `matchBenefit()`, `extractDeadlineFromContent()`, `getBenefitMatches()`, `ageToLifeStage()`, `selectBlogCards()`.
- **JavaScript (CF Functions)**: `camelCase` — e.g. `onRequestGet()`, `onRequestPost()`, `createSessionToken()`, `verifySessionToken()`, `getSession()`, `generateNickname()`.
- **Python**: `snake_case` — e.g. `generate_article()`, `proofread()`, `make_slug()`, `build_user_prompt()`, `extract_title_from_draft()`, `remove_fake_links()`, `validate_and_fix()`.
- **Astro component exports**: Only `Props` interface is exported; no function exports from `.astro` files.

**Variables:**
- **TypeScript/JavaScript**: `camelCase` — `const canonicalURL`, `const ogImage`, `const REGION_MAP`, `const bSex`, `const catBonus`.
- **Constants in TypeScript**: `UPPER_SNAKE_CASE` for module-level constants with `as const` — `REGION_MAP`, `CATEGORY_PERSONA_MAP`, `CATEGORY_LABEL_KO`, `FAKE_LINK_PATTERNS`, `REQUIRED_HEADINGS`. Also seen at module level in `src/consts.ts`: `SITE_TITLE`, `SITE_DESCRIPTION`, `SITE_URL`, `COLLECTIONS`.
- **Python**: `snake_case` — `NIM_API_KEY`, `DEEPSEEK_API_KEY`, `FALLBACK_MODELS`, `SYSTEM_PROMPT`. Module-level constants in `UPPER_SNAKE_CASE`.
- **Environment variables**: `UPPER_SNAKE_CASE` with optional `PUBLIC_` prefix for client-exposed vars — `KAKAO_REST_KEY`, `SESSION_SECRET`, `PUBLIC_KAKAO_REST_KEY`, `DATA_GO_KR_API_KEY`, `NVIDIA_API_KEY`, `DEEPSEEK_API_TOKEN`.

**Types:**
- **TypeScript**: `PascalCase` interfaces — `PersonaInput`, `Benefit`, `BenefitMatch`, `WelfareRaw`, `WelfareMatch`, `BlogPostMeta`, `PersonaCardTarget`, `CategoryId`.
- **TypeScript type exports**: Always exported with `export type` — `export type Benefit = { ... }`.
- **Zod schemas in `content.config.ts`**: `camelCase` with `Schema` suffix — `personaCardTargetSchema`, `targetPersonaSchema`, `sharedSchema`.

**CSS:**
- **Global classes**: `kebab-case` — `.btn-primary`, `.btn-full`, `.btn-disabled`, `.sr-only`, `.skip-link`, `.prose`, `.footer-inner`, `.footer-links`, `.sns-icon-link`.
- **CSS custom properties**: `--kebab-case` under `:root` — `--color-primary`, `--font-sans`, `--text-base`, `--space-4`, `--radius-lg`, `--shadow-md`.
- **BEM not used**: classes are flat (`kebab-case` with no `__` or `--` element/modifier separators).

## Code Style

**Formatting:**
- **No formatter detected** — no `.prettierrc`, `biome.json`, `ruff.toml`, or `pyproject.toml` exists in the project.
- **TypeScript/JS**: 2-space indentation consistently across all source files (`src/`, `functions/`).
- **Python**: 4-space indentation consistently (`scripts/auto-writer/`, `scripts/manual-publisher/`). No PEP8 enforcement tool detected.
- **Astro frontmatter (`---`)**: 2-space indent for JS/TS code, no semicolons in simple expressions.
- **CSS**: 2-space indentation, single-line rules for simple declarations.

**Linting:**
- **No linter detected** — no ESLint, no `eslint.config.*`, no Biome, no Ruff, no Flake8.
- The project relies entirely on manual/editor-level formatting with no automated enforcement.

**Semicolons:**
- **TypeScript/JavaScript**: Semicolons **required** consistently — every statement ends with `;`.
- **Python**: No semicolons (standard Python).

**Quotes:**
- **TypeScript/JavaScript**: Double quotes `"` for strings — `import { SITE_TITLE } from '../consts'`, `const regions = ['서울','부산',...]`.
- **Python**: Double quotes `"` for strings — `os.getenv("NVIDIA_API_KEY")`, `print("  [writer] ⚠️ ...")`.

## Import Organization

**Order (TypeScript/JS):**
1. Astro / framework imports first (e.g. `import { defineConfig } from 'astro/config'`)
2. Astro integration imports (e.g. `import mdx from '@astrojs/mdx'`)
3. Local component imports (e.g. `import Header from './Header.astro'`)
4. Local lib/utils imports (e.g. `import { SITE_TITLE } from '../consts'`)
5. Style imports (e.g. `import '../styles/tailwind.css'`)
6. No blank line separators between groups consistently — groups are logically ordered but not visually separated.

**Order (Python):**
1. Standard library imports first — `import os, re, json, sys`
2. Third-party imports — `from openai import OpenAI`, `from dotenv import load_dotenv`
3. Local module imports — `from shared.db_utils import get_pending_count`

**Path Aliases:**
- None detected. All imports use relative paths (`../../components/BaseHead.astro`). No `@/` or other path alias configured in `tsconfig.json`.

## Error Handling

**TypeScript/Cloudflare Functions:**
- Early returns with error responses — check condition, return `new Response(JSON.stringify({ error: '...' }), { status: 4xx })`.
- `try/catch` with `throw new Error('...')` for unrecoverable errors in CF Functions — `throw new Error('SESSION_SECRET env var is required')`.
- Functions use a `H` shorthand for JSON headers: `const H = { 'Content-Type': 'application/json' }`.
- Common error pattern:
  ```typescript
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  ```

**Python:**
- `try/except Exception as e` with `print(f"  [writer] ❌ 시도 {attempt+1} 실패: {e}")` logging.
- Fallback chain pattern — try multiple models/providers in sequence with exponential backoff: `wait = 2 ** attempt`.
- `raise ValueError("...")` for validation failures within fallback attempts.

**Astro frontmatter:**
- No explicit error handling in frontmatter (static generation, errors surface at build time).
- `?.` optional chaining used for nullable access: `(benefit.target || '') + (benefit.content || '')`.

## Logging

**Framework:**
- **TypeScript/JS (CF Functions)**: No logging framework — zero `console.log` calls in `functions/`.
- **Python (auto-writer)**: Python `logging` module with `RotatingFileHandler` — `pipeline.log` at `scripts/auto-writer/logs/`.
  ```python
  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(message)s",
      handlers=[RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3), logging.StreamHandler()]
  )
  ```
- **Python (manual-publisher)**: `print()` statements with step labels — `[step3]`, `[step4]`, `[publisher]`.
- **Python (writer module)**: `print(f"  [writer] ...")` with emoji indicators — `✅`, `⚠️`, `❌`.

**Patterns:**
- Auto-writer logs to file + stdout for monitoring.
- Manual-publisher uses stdout `print()` for launchd logging.
- Production functions (`functions/`) use no logging at all.

## Comments

**When to Comment:**
- Section headers in source code — `/* ── CSRF: OAuth state 검증 ── */`, `# ── NVIDIA NIM 폴백 체인 ───`.
- Inline explanations for complex logic — `// 큐레이션 먼저`, `// 패턴 B: 회계연도 말일 (12/31)`.
- TypeScript type definitions typically have brief JSDoc above the block `export type ...`.
- Python module-level docstrings explaining purpose and usage — see `scripts/load_env.py`.
- Korean comments in business logic — `// 소득/재산 경고`, `# ── 로컬 로그 설정 ──`.

**JSDoc/TSDoc:**
- Minimal usage. Found in `deadlineExtractor.ts` — `/** ... */` on major functions.
- Astro component frontmatter uses `/** @prop ... */` style (see `Button.astro`).
- No TSDoc linting or enforcement.

## Function Design

**Size:**
- TypeScript utility functions: small and focused (typically 5-50 lines).
- Python pipeline functions: larger (some 100-200 lines like `generate_article()` in `writer.py`, `build_user_prompt()`).
- `matchBenefit()`: ~80 lines, `matchWelfare()`: ~50 lines, `generate_article()`: ~80 lines.

**Parameters:**
- Functions take plain objects as parameters for complex inputs (e.g. `matchBenefit(persona: PersonaInput, benefit: Benefit)`).
- Default parameter values: `limit = 8`, `seed?: number`.

**Return Values:**
- TypeScript: typed return objects or unions with discriminated `matchStatus` field — `'eligible_likely' | 'needs_check' | 'not_eligible'`.
- Python: returns `dict | None` pattern — function returns `None` on failure, `dict` on success.
- CF Functions: return `new Response(...)` objects directly.

## Module Design

**Exports:**
- **TypeScript libs**: Named exports only — `export function matchBenefit()`, `export type Benefit = ...`.
- **CF Functions**: `export async function onRequestGet/Post/Put/Delete` — Cloudflare Pages Functions convention.
- **Python**: Module-level functions, no classes. Functions imported directly — `from validator import validate_and_fix, make_slug`.
- **Astro components**: Default export via file is the component template. Named interface `Props` export.

**Barrel Files:**
- `src/components/ui/index.ts` acts as barrel — re-exports `Button`, `Card`, `Badge`.
- `src/consts.ts` consolidates site-wide constants.

## Python Style Specifics

**Venv Management:**
- `scripts/manual-publisher/.venv/` — Python virtual environment for manual publisher.
- No `pyproject.toml` or `Pipfile` — dependency tracking via `scripts/manual-publisher/requirements.txt` only.
- `scripts/auto-writer/` shares the same venv as manual-publisher (common `.venv` or system install).

**Hardcoded Paths:**
- Multiple Python scripts hardcode paths: `"/Users/twinssn/Projects/money-aikorea24/.env"`, `/Users/twinssn/projects/money-aikorea24/src/content/blog` (note lowercase `projects`).
- This creates a portability concern (see CONCERNS.md).

**Config Files:**
- YAML for configuration — `scripts/auto-writer/config/category_map.yaml`.
- `.plist` files for launchd scheduling — `com.aikorea24.auto-writer.plist`, `com.aikorea24.manual-publisher.plist`.

## Astro Component Patterns

**File Structure:**
```
---
// JavaScript/TypeScript frontmatter
import ... from '...';
export interface Props { ... }
const { prop1, prop2 } = Astro.props;
---
<!-- HTML template -->
<tag {dynamicAttr}>
  <slot />
</tag>

<script>
// Client-side JS (runs in browser)
</script>

<style>
/* Scoped CSS */
</style>
```

**Props Pattern:**
- Always define an `export interface Props` at the top of the frontmatter.
- Destructure with defaults: `const { variant = 'primary', size = 'md' } = Astro.props;`
- Use `class?: string` in Props to allow consuming components to pass class overrides.

**Script Management:**
- `<script>` tags for client-side JS (default: bundled + scoped to component).
- `<script is:inline>` for inline scripts that must run immediately (e.g. `Footer.astro`'s `footerKakaoShare()`).
- ES module client scripts: IIFE pattern used in `Header.astro`'s `<script>` — `(function() { ... })()`.

**Style Management:**
- Scoped `<style>` per component (Astro default).
- Global styles in `src/styles/` — loaded via `@import` in `BaseHead.astro`.
- CSS custom properties (`--color-*`, `--space-*`, `--text-*`) from `design-tokens.css` used throughout.

## Commit Message Conventions

**Pattern:** `type: message` (Conventional Commits-like but informal)

| Type | Count (last 100) | Example |
|------|-------------------|---------|
| `publish:` | ~70 | `publish: 2026 연말정산 경정청구 누락 공제 환급으로 세금 부담 완화하기` |
| `content:` | ~12 | `content: update 2026-06-29` |
| `fix:` | ~9 | `fix: remove dist/persona-stats.json before wrangler deploy` |
| `feat:` | ~3 | `feat: proofread + thumbnail rewrite + article fixes` |
| `docs:` | 1 | `docs: AGENTS.md에 persona-stats.json 배포 버그 수정 기록` |
| `wip:` | 1 | `wip: .continue-here.md 핸드오프 파일 생성` |
| `reviewer:` | 1 | `reviewer: 마커 복원 버그 수정, CTA 문구 현행화, 프롬프트 누출 제거` |
| `writer:` | 1 | `writer: gemma-4-31b-it 추가, deepseek 제거, 퍼널 링크 3개 버그 수정` |

No formal commitlint, no scope in parentheses, Korean in commit bodies.

## Pre-commit / Automation

**No pre-commit hooks detected.** No `.pre-commit-config.yaml`, no husky, no `lint-staged`.

**Landing CI/CD:** None. Deploy is manual via `npm run deploy` → `scripts/deploy.sh` (3-step: build → git push → wrangler).

---

*Convention analysis: 2026-07-01*
