# Testing Patterns

**Analysis Date:** 2026-07-01

## Test Framework

**Runner:**
- **None detected** — No test runner is configured in `package.json`. No `vitest.config.*`, `jest.config.*`, or `pytest.ini` exists.
- `package.json` lists only `dev`, `build`, `preview`, `astro`, and `deploy` scripts — no `test` script.

**Assertion Library:**
- None detected.

**Run Commands:**
- Not applicable — no test commands exist.

## Test File Organization

**Location:**
- No test files found anywhere in the repository. No `__tests__/`, `test/`, or `*.test.*` / `*.spec.*` files exist.

**Naming:**
- No test naming convention established.

## Test Structure

**Suite Organization:**
- Not applicable — zero test files.

## Mocking

**Framework:**
- None detected.

**Patterns:**
- Not applicable.

## Fixtures and Factories

**Test Data:**
- No test fixtures exist.

**Location:**
- Not applicable.

## Coverage

**Requirements:**
- **0% — no coverage enforcement, no coverage tooling, no coverage requirements.**

**Current State:**
- **Entire codebase is untested.** This includes:
  - `src/lib/` — 4 TypeScript modules (`benefitMatcher.ts`, `welfareMatcher.ts`, `deadlineExtractor.ts`, `personaMatcher.ts`)
  - `functions/` — 8 Cloudflare Functions files
  - `src/components/` — ~20 Astro components
  - `scripts/auto-writer/` — 6 Python modules + 6 `shared/` modules
  - `scripts/manual-publisher/` — 10 Python modules
  - `scripts/` root — 6 standalone Python scripts

## Test Types

**Unit Tests:**
- Not implemented.

**Integration Tests:**
- Not implemented.

**E2E Tests:**
- Not implemented.

## CI/CD Integration

**Continuous Integration:**
- **No CI system.** No `.github/` directory, no GitLab CI, no Jenkins, no CircleCI config.
- All testing and validation is ad-hoc manual.

**Pre-deployment Validation:**
- `scripts/deploy.sh` performs a **pre-check** verifying Cloudflare Pages Secrets exist (`KAKAO_REST_KEY`, `KAKAO_CLIENT_SECRET`, `SESSION_SECRET`) before building and deploying.
- No automated test gate exists before deployment.

## Python Testing

**No pytest, unittest, or any Python test framework detected.**

- `scripts/auto-writer/` has `__pycache__/` directories suggesting code has been run but never tested.
- `scripts/manual-publisher/.venv/` exists for dependencies but no test dependencies are installed.

## Common Patterns for Adding Tests

No existing test patterns to follow. If tests are added, the following would need to be established from scratch:

**Priority candidates for testing (by fragility/criticality):**
1. `src/lib/benefitMatcher.ts` — scoring algorithm with multiple filtering criteria
2. `src/lib/deadlineExtractor.ts` — date parsing with multiple regex patterns
3. `src/lib/welfareMatcher.ts` — region matching + scoring
4. `src/lib/personaMatcher.ts` — persona-post matching + shuffle logic
5. `scripts/auto-writer/validator.py` — slug generation, frontmatter generation, link removal
6. `functions/api/_shared/session.js` — HMAC token creation/verification (security-critical)
7. `functions/api/community/*.js` — CRUD operations with D1 SQL

**Recommended test framework additions:**
- **TypeScript**: Vitest (compatible with Astro/Vite ecosystem)
- **Python**: pytest (standard for Python projects)
- **Cloudflare Functions**: `wrangler pages functions` testing or `vitest-environment-miniflare`

---

*Testing analysis: 2026-07-01*
