#!/bin/bash
set -e

# M1 전용 배포 스크립트
# M4에서 실행 시 차단 (architecture 체크)
ARCH=$(uname -m)
NODE=$(node -e "console.log(os.cpus()[0].model)" 2>/dev/null || sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "unknown")

if echo "$NODE" | grep -q "M4"; then
  echo "============================================="
  echo "  [차단] M4에서는 배포할 수 없습니다!"
  echo "  M1에서 실행하세요."
  echo "============================================="
  exit 1
fi

# .env 로드
if [ -f /Users/twinssn/Projects/5000/.env ]; then
  export $(grep -E '^(CLOUDFLARE_API_TOKEN|CLOUDFLARE_ACCOUNT_ID)' /Users/twinssn/Projects/5000/.env | xargs)
else
  echo "[ERROR] .env 파일 없음: /Users/twinssn/Projects/5000/.env"
  exit 1
fi

echo "=== [1/3] 빌드 ==="
npm run build

echo "=== [2/3] git push ==="
git add -A
git diff --cached --quiet || git commit -m "content: update $(date '+%Y-%m-%d')"
git push origin main

echo "=== [3/3] Cloudflare Pages 배포 ==="
npx wrangler pages deploy dist \
  --project-name money-aikorea24 \
  --branch main \
  --commit-dirty=true

echo ""
echo "배포 완료: https://money.aikorea24.kr"
