import { createSessionToken } from '../../_shared/session.js';

function generateNickname() {
  const regions = ['서울','부산','대구','인천','광주','대전','울산','경기','강원','충북','충남','전북','전남','경북','경남','제주'];
  const animals = ['냥이','멍이','토끼','사슴','여우','곰돌','판다','너구리','다람쥐','햄찌','펭귄'];
  const r = regions[Math.floor(Math.random() * regions.length)];
  const a = animals[Math.floor(Math.random() * animals.length)];
  const n = Math.floor(1000 + Math.random() * 9000);
  return `${r}${a}${n}`;
}

export async function onRequestGet({ request, env }) {
  const url  = new URL(request.url);
  const code = url.searchParams.get('code');

  /* ── CSRF: OAuth state 검증 ───────────────────────────── */
  const receivedState = url.searchParams.get('state') || '';
  const cookieHeader  = request.headers.get('Cookie') || '';
  const stateMatch    = cookieHeader.match(/oauth_state=([^;]+)/);
  const storedState   = stateMatch ? decodeURIComponent(stateMatch[1]) : '';

  if (!storedState || receivedState !== storedState) {
    return Response.redirect(new URL('/?error=csrf_failed', url.origin), 302);
  }

  /* ── 리다이렉트 대상 (Open Redirect 방어) ──────────────── */
  const nextMatch = cookieHeader.match(/oauth_next=([^;]+)/);
  const rawNext   = nextMatch ? decodeURIComponent(nextMatch[1]) : '/community';
  // 상대 경로만 허용, 프로토콜 상대 경로(//) 차단
  const safeNext  = (rawNext.startsWith('/') && !rawNext.startsWith('//')) ? rawNext : '/community';

  const mktMatch        = cookieHeader.match(/pending_marketing=([01])/);
  const marketingConsent = mktMatch && mktMatch[1] === '1' ? 1 : 0;

  if (!code) return Response.redirect(new URL('/?error=no_code', url.origin), 302);

  /* ── 환경 변수 ──────────────────────────────────────────── */
  if (!env.KAKAO_REST_KEY) throw new Error('KAKAO_REST_KEY env var is required');
  const KAKAO_REST_KEY = env.KAKAO_REST_KEY;
  const KAKAO_SECRET   = env.KAKAO_CLIENT_SECRET || '';
  if (!env.SESSION_SECRET) throw new Error('SESSION_SECRET env var is required');
  const SESSION_SECRET = env.SESSION_SECRET;
  const REDIRECT_URI   = 'https://persona.aikorea24.kr/api/auth/callback/kakao';

  /* ── 카카오 토큰 교환 ───────────────────────────────────── */
  const tokenBody = new URLSearchParams({
    grant_type:   'authorization_code',
    client_id:    KAKAO_REST_KEY,
    redirect_uri: REDIRECT_URI,
    code,
  });
  if (KAKAO_SECRET) tokenBody.set('client_secret', KAKAO_SECRET);

  const tokenRes  = await fetch('https://kauth.kakao.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: tokenBody,
  });
  const tokenData = await tokenRes.json();
  if (!tokenData.access_token) {
    return Response.redirect(new URL('/?error=token_failed', url.origin), 302);
  }

  /* ── 카카오 사용자 정보 ─────────────────────────────────── */
  const userRes   = await fetch('https://kapi.kakao.com/v2/user/me', {
    headers: { Authorization: `Bearer ${tokenData.access_token}` },
  });
  const kakaoUser = await userRes.json();
  const kakaoId   = String(kakaoUser.id);
  const email     = kakaoUser.kakao_account?.email || `${kakaoId}@kakao.local`;
  const realName  = kakaoUser.kakao_account?.profile?.nickname || '카카오사용자';
  const avatar    = kakaoUser.kakao_account?.profile?.profile_image_url || null;

  /* ── DB 사용자 조회 / 생성 ──────────────────────────────── */
  const db = env.DB;
  let dbUser = await db.prepare(
    'SELECT id, name, nickname, email, avatar FROM users WHERE kakao_id = ?'
  ).bind(kakaoId).first();

  if (!dbUser) {
    let nickname = generateNickname();
    for (let i = 0; i < 5; i++) {
      const dup = await db.prepare('SELECT id FROM users WHERE nickname = ?').bind(nickname).first();
      if (!dup) break;
      nickname = generateNickname();
    }
    await db.prepare(
      'INSERT INTO users (kakao_id, email, name, nickname, avatar, provider, marketing_consent, agreed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    ).bind(kakaoId, email, realName, nickname, avatar, 'kakao', marketingConsent, new Date().toISOString()).run();
    dbUser = await db.prepare(
      'SELECT id, name, nickname, email, avatar FROM users WHERE kakao_id = ?'
    ).bind(kakaoId).first();
  } else if (!dbUser.nickname) {
    let nickname = generateNickname();
    for (let i = 0; i < 5; i++) {
      const dup = await db.prepare('SELECT id FROM users WHERE nickname = ?').bind(nickname).first();
      if (!dup) break;
      nickname = generateNickname();
    }
    await db.prepare('UPDATE users SET nickname = ? WHERE id = ?').bind(nickname, dbUser.id).run();
    dbUser.nickname = nickname;
  }

  /* ── HMAC-SHA256 서명 세션 토큰 생성 ───────────────────── */
  const sessionPayload = {
    id:     dbUser.id,
    name:   dbUser.nickname,
    email:  dbUser.email,
    avatar: dbUser.avatar,
  };
  const sessionToken = await createSessionToken(sessionPayload, SESSION_SECRET);

  /* ── 클라이언트 UI용 non-HttpOnly 쿠키 (이름 표시용) ──── */
  function base64Encode(str) {
    const bytes = new TextEncoder().encode(str);
    let binary = '';
    bytes.forEach(b => binary += String.fromCharCode(b));
    return btoa(binary);
  }
  const uiPayload = base64Encode(JSON.stringify({ id: dbUser.id, name: dbUser.nickname }));

  /* ── 응답: 302 리다이렉트 + Set-Cookie ─────────────────── */
  const cookieMaxAge = 60 * 60 * 24;
  const headers = new Headers({
    'Location': safeNext,
  });
  headers.append('Set-Cookie', 'oauth_state=; Path=/; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'oauth_next=; Path=/; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'pending_marketing=; Path=/; Max-Age=0; Secure; SameSite=Lax');
  // 구식 Domain=.aikorea24.kr 쿠키 무력화 (마이그레이션)
  headers.append('Set-Cookie', 'session=; Path=/; Domain=.aikorea24.kr; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', 'session_ui=; Path=/; Domain=.aikorea24.kr; Max-Age=0; Secure; SameSite=Lax');
  headers.append('Set-Cookie', `session=${sessionToken}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=${cookieMaxAge}`);
  headers.append('Set-Cookie', `session_ui=${uiPayload}; Path=/; Secure; SameSite=Strict; Max-Age=${cookieMaxAge}`);
  return new Response(null, { status: 302, headers });
}
