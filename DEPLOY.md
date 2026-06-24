# Deploy Guide — persona.aikorea24.kr

## 배포 방법

```bash
npm run build
npx wrangler pages deploy dist --project-name money-aikorea24
```

---

## Cloudflare WAF Rate Limiting Rules (수동 설정 필요)

배포 후 Cloudflare Dashboard > Security > WAF > Rate Limiting에서 아래 규칙을 수동으로 등록해야 합니다.

| Rule 이름 | 경로 | 조건 | 액션 |
|-----------|------|------|------|
| Rate Limit - Login | /api/auth/* | 10 req/min 초과 | Block 1분 |
| Rate Limit - Post Write | /api/community/posts (POST) | 5 req/min 초과 | Block 5분 |
| Rate Limit - Benefit Click | /api/benefit-click | 30 req/min 초과 | Block 10분 |

### 설정 순서

1. Cloudflare Dashboard 접속
2. Security > WAF > Rate limiting rules
3. Create rate limiting rule
4. 위 표의 경로, 조건, 액션에 맞춰 등록
5. Rule 상태를 Deploy로 변경
