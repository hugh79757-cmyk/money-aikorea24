---
phase: 01-security-portability
plan: Plan02
subsystem: scripts
tags: ["portability", "paths", "auto-writer", "manual-publisher"]
requires: []
provides: ["scripts/paths.py", "dynamic-path-resolution"]
affects: ["scripts/auto-writer/**/*.py", "scripts/manual-publisher/**/*.py"]
tech-stack:
  added: ["pathlib", "scripts/paths.py"]
  patterns: ["dynamic-path-computation", "centralized-path-module"]
key-files:
  created: ["scripts/paths.py"]
  modified:
    - "scripts/auto-writer/pipeline.py"
    - "scripts/auto-writer/scheduler.py"
    - "scripts/auto-writer/writer.py"
    - "scripts/auto-writer/fetcher.py"
    - "scripts/auto-writer/fetcher_invest.py"
    - "scripts/auto-writer/fetcher_loan_fin.py"
    - "scripts/auto-writer/shared/thumbnail_gen.py"
    - "scripts/auto-writer/shared/build_deploy.py"
    - "scripts/auto-writer/shared/reviewer.py"
    - "scripts/auto-writer/shared/notifier.py"
    - "scripts/manual-publisher/publisher.py"
    - "scripts/manual-publisher/watcher.py"
    - "scripts/manual-publisher/entity_injector.py"
    - "scripts/manual-publisher/thumbnail.py"
    - "scripts/manual-publisher/deployer.py"
decisions:
  - "All paths derived from Path(__file__).resolve().parent.parent for portability"
  - "Exported as strings for compatibility with os.path APIs"
metrics:
  duration: ~10 min
  completed: 2026-07-01
  files-created: 1
  files-modified: 15

---

# Phase 01 Security & Portability — Plan 02: Absolute Path Portability Summary

Replaced all 17 hardcoded `/Users/twinssn/Projects/money-aikorea24/...` absolute paths in the Python codebase with dynamic path computation from `scripts/paths.py`, which derives `PROJECT_ROOT` from `Path(__file__).resolve().parent.parent`.

## Completed Tasks

### Task 2.1: Create `scripts/paths.py`
- **Commit:** `e0221ae`
- Created new shared module computing all project paths dynamically:
  - `PROJECT_ROOT`, `BLOG_DIR`, `INBOX_DIR`, `BG_IMG_DIR`, `THUMBNAIL_DIR`, `DOTENV_PATH`, `COMMON_ENV_PATH`, `SCRIPTS_DIR`
- All paths derived from `PROJECT_ROOT` (not hardcoded strings)
- All exported as strings for compatibility with `os.path.join()`, `load_dotenv()`, etc.

### Task 2.2: Replace all hardcoded paths in auto-writer (10 files)
- **Commit:** `8796c15`
- Modified files:
  - `pipeline.py`: `load_dotenv("/Users/twinssn/.../.env")` → `load_dotenv(paths.DOTENV_PATH)`, `BLOG_DIR` → `paths.BLOG_DIR`
  - `scheduler.py`, `writer.py`, `fetcher.py`, `fetcher_invest.py`, `fetcher_loan_fin.py`: `load_dotenv` replacements
  - `shared/thumbnail_gen.py`: `BG_DIR` fallback → `paths.BG_IMG_DIR`
  - `shared/build_deploy.py`: `PROJECT_DIR` → `paths.PROJECT_ROOT`
  - `shared/reviewer.py`, `shared/notifier.py`: `load_dotenv` replacements
- Each file adds `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` or `...parent.parent.parent` (for `shared/` subdirectory files) before importing `paths`

### Task 2.3: Replace all hardcoded paths in manual-publisher (5 files)
- **Commit:** `b2c13e0`
- Modified files:
  - `publisher.py`: `BLOG_DIR` → `from paths import BLOG_DIR` (already had `sys.path` for `scripts/`)
  - `watcher.py`: `BLOGSMITH_OUTPUT` → `from paths import INBOX_DIR`
  - `entity_injector.py`: `BLOG_DIR` → `from paths import BLOG_DIR`
  - `thumbnail.py`: `THUMBNAIL_DIR` + `BG_DIR` → `from paths import THUMBNAIL_DIR, BG_IMG_DIR`
  - `deployer.py`: `PROJECT_DIR` → `from paths import PROJECT_ROOT`

## Verifications

| Check | Result |
|-------|--------|
| `grep -c 'Users/twinssn' scripts/auto-writer/**/*.py` | All 0 |
| `grep -c 'Users/twinssn' scripts/manual-publisher/*.py` | All 0 |
| `grep -c 'projects/' scripts/manual-publisher/*.py` | All 0 |
| `python3 -c 'from paths import PROJECT_ROOT; print(PROJECT_ROOT)'` | `/Users/twinssn/Projects/money-aikorea24` |

## Deviations from Plan

None — plan executed exactly as written.

## Legacy Paths (not modified)

The following files retain hardcoded paths but are outside the scope of this plan:
- `com.aikorea24.auto-writer.plist` — macOS launchd config (needs user-specific paths)
- `scripts/auto-writer/com.aikorea24.auto-writer.plist` — same
- `scripts/auto-writer/logs/*.log` — log files (historical data, not source code)
- `scripts/manual-publisher/com.kr.aikorea24.manual-publisher.plist` — macOS launchd config
- `__pycache__/` — compiled bytecode (generated, not tracked)

## Self-Check: PASSED

- [x] `scripts/paths.py` exists and all assertions pass
- [x] All 3 commits exist in git log
- [x] Zero hardcoded `Users/twinssn` paths in any Python source file
- [x] Zero hardcoded `projects/money-aikorea24` paths in any Python source file
- [x] `PROJECT_ROOT` resolves to the correct project directory

## Rollback

To revert all Plan 02 changes:
```bash
git revert e0221ae 8796c15 b2c13e0
```
The old hardcoded paths will be restored, and `scripts/paths.py` will be removed.
