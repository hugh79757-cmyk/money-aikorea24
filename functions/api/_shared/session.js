/**
 * HMAC-SHA256 서명 세션 헬퍼
 * 토큰 형식: base64url(payload).base64url(hmac-sha256-sig)
 *
 * 사용 전 Cloudflare Pages Secret 설정 필요:
 *   npx wrangler pages secret put SESSION_SECRET
 */

function b64urlEncode(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function b64urlDecode(str) {
  return atob(str.replace(/-/g, '+').replace(/_/g, '/'));
}

async function hmacSign(data, secret) {
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(data));
  return b64urlEncode(sig);
}

/** 타이밍 공격 방어 비교 */
function timingSafeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/**
 * 세션 토큰 생성
 * @param {object} payload - 저장할 사용자 정보
 * @param {string} secret  - SESSION_SECRET
 * @returns {Promise<string>} 서명된 토큰
 */
export async function createSessionToken(payload, secret) {
  const data = b64urlEncode(new TextEncoder().encode(JSON.stringify(payload)));
  const sig  = await hmacSign(data, secret);
  return `${data}.${sig}`;
}

/**
 * 세션 토큰 검증
 * @param {string} token  - 세션 쿠키 값
 * @param {string} secret - SESSION_SECRET
 * @returns {Promise<object|null>} payload 또는 null (검증 실패)
 */
export async function verifySessionToken(token, secret) {
  if (!token || typeof token !== 'string') return null;
  const dot = token.lastIndexOf('.');
  if (dot === -1) return null;
  const data = token.slice(0, dot);
  const sig  = token.slice(dot + 1);
  const expected = await hmacSign(data, secret);
  if (!timingSafeEqual(sig, expected)) return null;
  try {
    return JSON.parse(b64urlDecode(data));
  } catch { return null; }
}

/**
 * 요청에서 세션 파싱 + 검증
 * @param {Request} request
 * @param {object}  env      - Cloudflare env (env.SESSION_SECRET 사용)
 * @returns {Promise<object|null>}
 */
export async function getSession(request, env) {
  const cookie = request.headers.get('Cookie') || '';
  const match  = cookie.match(/session=([^;]+)/);
  if (!match) return null;
  const secret = env.SESSION_SECRET || 'dev-secret-CHANGE-IN-PRODUCTION';
  return verifySessionToken(decodeURIComponent(match[1]), secret);
}
