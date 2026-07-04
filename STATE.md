# STATE.md — Project State

## Project
money-aikorea24 (`persona.aikorea24.kr`)
Last resumed: 2026-07-04

## Phase: Content Quality & Revenue (COMPLETE)

### Plans
| # | Plan | Status | Summary |
|---|------|--------|---------|
| 02 | Content Freshness & Data Validation | ✅ COMPLETE | year_validator, url_checker, naver_validator, status_reason column |
| 03 | AdSense Revenue Optimization | ✅ COMPLETE | marker-based ads, IntersectionObserver, conditional placement |

### Deployed
| Commit | Date | Description |
|--------|------|-------------|
| `eb06813` | 2026-07-04 | Phase 02 + Phase 03: content freshness + AdSense optimization |
| `84b34c7` | 2026-07-04 | auto-writer build_deploy.py import fix |
| `f174eab` | 2026-07-01 | deploy.sh persona-stats.json removal |

### Auto-Writer Pipeline Status
- DB: ~5,266 services (pending), 158 published, 53 error
- Last deploy: Phase 02+03 content deployed (2,438 files)
- Auto-writer runs daily via launchd

### AdSense Configuration
- Client: `ca-pub-5938862195544185`
- Slot: `8107272066` (all in-article + leaderboard + mobile-sticky)
- Conditional: <800 chars = 0 ads; >=800 + high-rpm + h2>=3 = 3 ads; else = 2
- Lazy-loaded via IntersectionObserver (400px rootMargin)

### Site Health
- persona.aikorea24.kr: ✅ 200 OK
- Deploy: Cloudflare Pages (wrangler pages deploy)
- Build: `npm run build` → `dist/`
- Deploy command: `rm -f dist/persona-stats.json && wrangler pages deploy dist --project-name money-aikorea24 --branch main --commit-dirty=true`
