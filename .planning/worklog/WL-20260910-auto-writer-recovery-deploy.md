# Worklog: WL-20260910-auto-writer-recovery-deploy

## Operation
auto-writer 파이프라인 장애 복구 + 미배포분 재배포 (b1 참조: 원인분석·writer.py 회전큐 전환 완료)

## Pre-Count
- 미커밋: 신규 블로그 md 20건 + 수정 6건 (build_deploy.py, writer.py, 테스트 2건, db, fallback_state.json)
- 현 Production 배포: e591109f (commit b4b0ea4, 4일 전)

## Backup
- 롤백 대상: Production 배포 e591109f (wrangler pages deployment list 기록)

## Execution
1. deploy.sh 실행 → [0/5]에서 EXIT=1 무출력 종료. 원인: 스크립트 6행에서 export한
   CLOUDFLARE_API_TOKEN이 24행 wrangler secret list 호출의 OAuth 인증을 깨뜨림 (set -e + 2>/dev/null이라 침묵 실패)
2. 수동 단계 실행: secret 3종 확인(전부 존재) → check-blog-issues 427건 clean →
   npm build 2708 pages 성공 → commit c50a38b → push → wrangler deploy 1f525434
3. deploy.sh 근본 수정: wrangler 호출 2곳에 `env -u CLOUDFLARE_API_TOKEN` 추가 → commit 57522b1 → push
   (57522b1은 dist에 영향 없어 재배포 불필요)

## Post-Verification
- Production: 1f525434 @ c50a38b (deployment list 확인)
- https://1f525434.money-aikorea24.pages.dev/ → 200, RSS에 신규 글 노출
- custom 도메인 curl 000: 로컬망/DNS 이슈로 판단 (배포 무관, pages.dev 정상)

## Logs
- logs/destructive_2026-09-10.log (gitignore로 로컬 전용)
