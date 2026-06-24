function b64urlEncode(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}
function b64urlDecode(str) {
  return atob(str.replace(/-/g, '+').replace(/_/g, '/'));
}
async function hmacSign(data, secret) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(data));
  return b64urlEncode(sig);
}
function timingSafeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
export async function createSessionToken(payload, secret) {
  const data = b64urlEncode(new TextEncoder().encode(JSON.stringify(payload)));
  const sig  = await hmacSign(data, secret);
  return `${data}.${sig}`;
}
export async function verifySessionToken(token, secret) {
  if (!token || typeof token !== 'string') return null;
  const dot = token.lastIndexOf('.');
  if (dot === -1) return null;
  const data = token.slice(0, dot);
  const sig  = token.slice(dot + 1);
  const expected = await hmacSign(data, secret);
  if (!timingSafeEqual(sig, expected)) return null;
  try { return JSON.parse(b64urlDecode(data)); } catch { return null; }
}
export async function getSession(request, env) {
  const cookie = request.headers.get('Cookie') || '';
  const match  = cookie.match(/(?:^|;\s*)session=([^;]+)/);
  if (!match) return null;
  if (!env.SESSION_SECRET) throw new Error('SESSION_SECRET env var is required');
  const secret = env.SESSION_SECRET;
  return verifySessionToken(decodeURIComponent(match[1]), secret);
}
