---
slug: dawn-google-auth
title: 새벽 구글 인증 시도 제거
objective: auto-blog writer가 새벽에 시도하는 불필요한 구글 인증 원인 파악 및 제거
mode: quick
created: 2026-09-05
---

## Goal
새벽(dawn) 시간대에 auto-blog writer 관련 프로세스가 구글 인증을 시도하는 현상 제거. 수동 실행이라 인증 팝업/Browser flow가 의미 없고 버그로 판단됨.

## Context
- 사용자 보고: 새벽마다 auto-blog writer가 구글 인증 시도, 수동 실행이라 성공 불가
- money-aikorea24 auto-writer는 launchd daily 09:00 (kr.aikorea24.auto-writer) + Monday 06:00 fetch (com.aikorea24.auto-writer-fetch) 만 존재
- 코드베이스 내 interactive google auth (InstalledAppFlow, google.oauth2, gspread) 는 money-aikorea24에는 없음 → 다른 dawn 잡이나 잔존 plist/스크립트 의심
- 이전 조사에서 dawn(04-07시)에 실행되는 launchd 잡 18개 식별 (network-refresh, pipeline-runner, blog-draft 등)
- fetcher_invest가 매일 401 Unauthorized 로그 남김 (data.go.kr) — 구글 아님, 오인 가능성 있음

## Tasks
- [ ] T1: Dawn 시간대(04-07시) launchd 전체 인벤토리 + 각 스크립트의 google/import/인증 코드 유무 전수 조사
- [ ] T2: money-aikorea24 auto-writer 코드 전수 검사 (scheduler.py, pipeline.py, writer.py, fetcher*, shared/*) — interactive auth 존재 여부 확정
- [ ] T3: 실제 dawn 로그 검증 (launchd_stdout/stderr, scheduler.log, system log) — 구글 인증 시도 timestamp / 프로세스 식별
- [ ] T4: 원인 확정 후 불필요 코드/launchd 제거 또는 수정, 재발 방지 (관련 문서 업데이트)
- [ ] T5: 검증 — 수정 후 launchctl list 및 grep으로 잔존 google auth 제거 확인 + 빌드 테스트

## Verification
- `grep -r "InstalledAppFlow\|google.oauth2\|gspread\|google_auth" /Users/twinssn/Projects/money-aikorea24 --include="*.py" | grep -v .venv` 결과 0건
- `launchctl list` 에서 불필요 dawn google 인증 잡 제거 확인
- `grep -r "google" money-aikorea24 --include="*.plist"` 잔존 없음
- `npm run build` 0 에러 유지
