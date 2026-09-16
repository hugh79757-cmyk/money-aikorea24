---
date: 2026-09-14
type: config
status: resolved
---

# deploy.sh 5000 의존성 제거 + 재배포

## What
배포 막힘 원인(npm 미설치) 해소 후, deploy.sh가 5000/.env 참조하던 구조를 money-aikorea24 독립 구조로 전환. 재배포 성공.

## Why
- 빌드 실패 원인: node_modules 미설치 (UNMET DEPENDENCY 10건)
- 5000 프로젝트 이관 작업 중이라 money-aikorea24가 5000/.env에 의존하면 안 됨

## Files changed
- scripts/deploy.sh — .env 로드 헤더 교체 (로컬 .env > ~/.env.common, 5000 참조 0건)
- .env — CLOUDFLARE_ACCOUNT_ID 1줄 추가 (값은 ~/.env.common과 동일 md5 확인)
- node_modules/ — npm install 368 packages (환경, git 미추적)

## How
- `npm install`로 의존성 복구
- CLOUDFLARE_ACCOUNT_ID를 ~/.env.common에서 로컬 .env Cloudflare 섹션으로 복사 (값 출력 없이 python 삽입)
- deploy.sh 헤더를 `source ~/.env.common` + `source 로컬 .env` 구조로 교체, 기존 `export $(grep ... 5000/.env)` 제거
- `bash scripts/deploy.sh` 실행 → [0/5]→[5/5] 진행

## Verification
- `npm ls` EXIT 0, UNMET 0건
- `bash -n scripts/deploy.sh` SYNTAX_OK, `grep -c 5000` = 0
- `check-blog-issues.py --ci` → 441 posts clean
- 빌드 2722 pages, 커밋 4ddfa70 (17 files), wrangler Uploaded 2665 files, Deployment complete (b5cb545f)
- Cloudflare secret 3종 (KAKAO_REST_KEY, KAKAO_CLIENT_SECRET, SESSION_SECRET) 존재 확인
- 잔존: money.aikorea24.kr 실접속 미확인 (preview URL만 확인)
