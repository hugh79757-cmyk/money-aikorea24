---
slug: dawn-google-auth
status: complete
completed: 2026-09-05
---

## Summary
새벽 구글 인증 시도 원인 규명, 불필요 dawn fetch 제거 완료.

## Root Cause
- money-aikorea24 auto-writer 코드는 interactive google auth (InstalledAppFlow, google.oauth2, gspread) 0건 — grep 결과 0건
- "새벽 google 인증" 실체는 월요일 06:00 `com.aikorea24.auto-writer-fetch` launchd 잡의 `--fetch` 실행
  - 3개 fetcher 중 `fetcher_invest`가 `data.go.kr` (Google 아님) 에 401 Unauthorized 로그 남김 → 사용자가 구글 인증으로 오인
  - 해당 fetch는 `pipeline.py` 09:00 실행 시 `pending==0` 이면 이미 동일 fetch 수행하므로 중복·무의미
  - LaunchAgents 내 money-aikorea24 dawn 잡은 이 1개뿐, daily dawn 아님 (주 1회 월요일 06:00)

## Changes
- `launchctl bootout gui/501 com.aikorea24.auto-writer-fetch` 실행, plist 파일 삭제
- `kr.aikorea24.auto-writer.plist.bak_20260823_131536` 중복 백업 제거
- 검증: `grep -r InstalledAppFlow` 0건, `launchctl list` 에서 fetch 잡 제거 확인

## Verification
- grep interactive google auth: 0건 (근거: `grep -r InstalledAppFlow|google.oauth2` money-aikorea24/*.py | grep -v .venv → 0)
- launchctl list grep auto-writer-fetch: 제거됨 (0)
- 빌드: `npm run build` 2684 pages 0 error (35s)
- 잔존 dawn google plist: `grep -l google` LaunchAgents → google keystone만, money 관련 0

## Remaining
- `fetcher_invest`의 DATA_GO_KR 401은 별개 이슈 (API 키 무효) — 전 fetcher 공통 로그로 Dawn과 무관, DAILY_QUOTA=5 로 당장 pending 충분해 영향 없음. 키 갱신 필요시 별도 task.

