---
date: 2026-09-10
type: fix
status: resolved
---

# auto-writer 장애 복구 + 미배포분 재배포 (Production 1f525434)

## What
auto-writer 스케줄러 크래시([Errno 2] dist/persona-stats.json) + GPT 실패 2건(귀농인 농가주택 수리비·정착금) 복구.
writer.py 순수 회전 큐 전환 후 재배포, Production 1f525434 라이브 확인.

## Why
1. shared/build_deploy.py:41 os.remove() strict → public 원본 부재 시 FileNotFoundError, 배포 직전 크래시 (미배포 2건 적체)
2. 무료티어 quota 고갈 후 구 쿨다운 설계 붕괴 (최조만료 1개 티어만 시도→429→실패)
3. deploy.sh가 export한 CLOUDFLARE_API_TOKEN이 wrangler OAuth 인증 깨뜨림 (auth 10000, 침묵 실패)

## Files changed
- scripts/auto-writer/shared/build_deploy.py (존재가드)
- scripts/auto-writer/writer.py (쿨다운 제거 → {front,queue} 회전, paid-last, budget 600s)
- scripts/auto-writer/tests/test_llm_fallback.py, test_fallback_chain.py (회전계약으로 교체)
- scripts/deploy.sh (wrangler 호출 2곳 env -u 추가)
- 신규 블로그 md 20건 + DB/state 포함 commit c50a38b, 57522b1

## How
systematic-debugging 4단계 → llm-fallback-chain-management 스킬 적용 →
destructive-ops 프로토콜 (사전배포 e591109f 기록 → 수동 단계 배포 → 사후검증)

## Verification
- 테스트 8/8 + 5그룹 통과 (prod+test 동시수정이라 순환검증 → 부분검증)
- build 2708 pages, blog check 427건 clean
- 1f525434 Production, pages.dev 200 + RSS 신규 글 노출
- 잔존: GPT 실패 2건 error 유지(지시), 무료 TPD 상한 여전, custom도메인 curl 000(로컬망 이슈 추정)
