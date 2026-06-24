# Rate Limiting — Cloudflare WAF 설정 가이드

## 권장 Rate Limiting Rule

Cloudflare Dashboard > Security > WAF > Rate limiting rules 에서 아래 규칙을 생성하세요.

### Rule 1: 로그인 엔드포인트

| 항목 | 값 |
|------|-----|
| Rule name | `Login Rate Limit` |
| When request matches | URI Path equals `/api/auth/*` |
| And | Method equals `POST` or `GET` |
| Rate | 10 requests / 1 minute |
| Action | Block |
| Duration | 10 minutes |

### Rule 2: 게시글 작성

| 항목 | 값 |
|------|-----|
| Rule name | `Post Creation Rate Limit` |
| When request matches | URI Path equals `/api/community/posts` |
| And | Method equals `POST` |
| Rate | 5 requests / 1 minute |
| Action | Block |
| Duration | 10 minutes |

### Rule 3: 혜택 클릭 집계

| 항목 | 값 |
|------|-----|
| Rule name | `Benefit Click Rate Limit` |
| When request matches | URI Path equals `/api/benefit-click` |
| And | Method equals `POST` |
| Rate | 30 requests / 1 minute |
| Action | Challenge (CAPTCHA) |
| Duration | 5 minutes |

### Rule 4: 커뮤니티 전체 (기본 보호)

| 항목 | 값 |
|------|-----|
| Rule name | `Community API Rate Limit` |
| When request matches | URI Path starts with `/api/community/` |
| Rate | 60 requests / 1 minute |
| Action | Challenge (CAPTCHA) |
| Duration | 5 minutes |

---

## Bot Fight Mode

Cloudflare Dashboard > Security > Bots 에서 Bot Fight Mode를 활성화하세요.

- **Enable Bot Fight Mode**: ON
- **Definitely Automated**: Block
- **Likely Automated**: Managed Challenge

---

## 확인 방법

1. Cloudflare Dashboard > Security > Events 에서 차단 이력 확인
2. `curl` 테스트:
```bash
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code}" https://persona.aikorea24.kr/api/auth/callback/kakao
done
# 10회 초과 시 429 응답 기대
```
