# STATE.md — Project State

## Project
money-aikorea24 (`persona.aikorea24.kr`)
Last resumed: 2026-07-02

## Phase: 01-security-portability (43% complete)

### Plans
| # | Plan | Status | Summary |
|---|------|--------|---------|
| 01 | Security-Critical & Git Hygiene | ✅ COMPLETE | R2 creds removal, git rm .ssr-backup/__pycache__, dead code cleanup |
| 02 | Absolute Path Portability | ✅ COMPLETE | scripts/paths.py + 19 files migrated |
| 03 | Configuration Extraction | ⏳ PENDING | AdSense → consts.ts, Kakao key → env, OAuth redirect → dynamic |
| 04 | Font + API Hardening | ⏳ PENDING | Noto Sans font, D1 error handling, rate limiting |
| 05 | XSS Mitigation | ⏳ PENDING | innerHTML → escapeHtml sanitization |

### Blocking Prerequisites for Wave 2
- **P-2**: Add `localhost` + `*.pages.dev` redirect URIs to Kakao Dev Console
- **P-3**: Download `NotoSansCJK-Regular.otf` → `fonts/`

### Recent Commits (top of main)
| Hash | Description |
|------|-------------|
| `17f3c11` | fix: deploy fail → Telegram details |
| `c266cc5` | docs: PLAN.md + manual-publisher log |
| `51671c3` | docs: Plan 01 summary |
| `d8a5565` | docs: Plan 02 summary |
| `b2c13e0` | refactor: manual-publisher paths |
| `2b09480` | chore: dead code + TODOs |
| `8796c15` | refactor: auto-writer paths |
| `e0221ae` | feat: scripts/paths.py |
| `1f2f93b` | feat: R2 public URL env var |
| `a97ef0a` | feat: remove R2 credential fallbacks |

## Site Health
- persona.aikorea24.kr: ✅ 200 OK
- Working tree: clean (only log files modified)
