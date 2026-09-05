---
date: 2026-09-05
type: fix
status: resolved
---

# Dawn 불필요 fetch 제거 (구글 인증 오인)

## What
새벽에 auto-blog writer가 구글 인증을 시도한다는 제보. 수동 실행이라 인증 팝업이 의미 없고 버그로 판단됨. 원인 파악 후 불필요 요소 제거.

## Why
- money-aikorea24 코드에 interactive google auth (InstalledAppFlow, google.oauth2, gspread) 0건 — `grep -r` 결과 0건
- 실체: 월요일 06:00 `com.aikorea24.auto-writer-fetch --fetch` launchd 잡
  - `fetcher_invest`가 data.go.kr에 401 Unauthorized 로그 남김 (Google 아님, 오인)
  - 09:00 daily `kr.aikorea24.auto-writer` pipeline이 `pending==0` 시 동일 fetch 3개 수행하므로 중복
  - launchd_fetch_stdout.log 75줄 전부 401 반복, 신규 0건

## Files changed
- `~/Library/LaunchAgents/com.aikorea24.auto-writer-fetch.plist` 삭제 (launchctl bootout gui/501)
- `~/Library/LaunchAgents/kr.aikorea24.auto-writer.plist.bak_20260823_131536` 중복 bak 삭제
- `.planning/quick/20250905-dawn-google-auth/PLAN.md` 생성
- `.planning/quick/20250905-dawn-google-auth/SUMMARY.md` 생성
- `.planning/STATE.md` Quick Tasks Completed 추가

## How
1. Dawn 04-07시 launchd 18개 인벤토리 전수 조사 → money-aikorea24 dawn 잡 1개 식별
2. 코드베이스 전수 grep으로 interactive google auth 없음 확정
3. pipeline.py 중복 fetch 로직 확인 후 redundant fetch 제거 결정 (ponytail: 삭제가 최소 수정)
4. `launchctl bootout` + plist 삭제, `npm run build` 2684p 검증
5. Quick task로 기록 후 triage에도 이관

## Verification
- `grep -r InstalledAppFlow|google.oauth2 --include=*.py | grep -v .venv` → 0건
- `launchctl list | grep auto-writer-fetch` → 0건 (제거됨)
- `grep -l google LaunchAgents/*.plist` → keystone만, money 관련 0
- `npm run build` → 2684 pages Complete 0에러
- 401은 DATA_GO_KR_API_KEY 별개 이슈로 분리, pending 충분해 즉시 영향 없음

