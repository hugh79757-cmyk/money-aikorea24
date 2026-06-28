#!/bin/bash
set -e

# .env 로드
if [ -f /Users/twinssn/Projects/5000/.env ]; then
  export $(grep -E '^(CLOUDFLARE_API_TOKEN|CLOUDFLARE_ACCOUNT_ID)' /Users/twinssn/Projects/5000/.env | xargs)
else
  echo "[ERROR] .env 파일 없음: /Users/twinssn/Projects/5000/.env"
  exit 1
fi

echo "=== [0/4] 환경변수 사전 체크 ==="
MISSING_LOCAL=0
for var in PUBLIC_KAKAO_REST_KEY; do
  if ! grep -q "^${var}=" /Users/twinssn/Projects/money-aikorea24/.env 2>/dev/null; then
    echo "  [FAIL] 로컬 .env에 ${var} 없음"
    MISSING_LOCAL=1
  else
    echo "  [OK]   로컬 .env: ${var}"
  fi
done

MISSING_CF=0
SECRETS=$(npx wrangler pages secret list --project-name money-aikorea24 2>/dev/null)
for var in KAKAO_REST_KEY KAKAO_CLIENT_SECRET SESSION_SECRET; do
  if echo "$SECRETS" | grep -q "^  - ${var}:"; then
    echo "  [OK]   Cloudflare secret: ${var}"
  else
    echo "  [FAIL] Cloudflare secret 누락: ${var}"
    MISSING_CF=1
  fi
done

if [ $MISSING_LOCAL -eq 1 ] || [ $MISSING_CF -eq 1 ]; then
  echo ""
  echo "[ERROR] 필수 환경변수가 누락되었습니다. 배포를 중단합니다."
  echo "  - 로컬 .env 변수 추가: /Users/twinssn/Projects/money-aikorea24/.env"
  echo "  - Cloudflare secret 추가: npx wrangler pages secret put <NAME> --project-name money-aikorea24"
  exit 1
fi

echo ""
echo "=== [1/4] 빌드 ==="
npm run build

echo "=== [2/4] git push ==="
git add -A
git diff --cached --quiet || git commit -m "content: update $(date '+%Y-%m-%d')"
git push origin main

echo "=== [3/4] Cloudflare Pages 배포 ==="
rm -f dist/persona-stats.json
npx wrangler pages deploy dist \
  --project-name money-aikorea24 \
  --branch main \
  --commit-dirty=true

echo ""
echo "=== [4/4] 배포 완료: https://money.aikorea24.kr ==="
echo "팁: 새 deployment 로그 확인 → npx wrangler pages deployment tail --project-name money-aikorea24 --environment production"
