export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const next = url.searchParams.get('state') || '/community';
  if (!code) return Response.redirect(new URL('/?error=no_code', url.origin), 302);

  const KAKAO_REST_KEY = 'fac8da4c0dd8911f025dce7bf2f76f0d';
  const KAKAO_SECRET   = env.KAKAO_CLIENT_SECRET || '';
  const REDIRECT_URI   = 'https://persona.aikorea24.kr/api/auth/callback/kakao';

  const tokenBody = new URLSearchParams({
    grant_type:   'authorization_code',
    client_id:    KAKAO_REST_KEY,
    redirect_uri: REDIRECT_URI,
    code,
  });
  if (KAKAO_SECRET) tokenBody.set('client_secret', KAKAO_SECRET);

  const tokenRes = await fetch('https://kauth.kakao.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: tokenBody,
  });
  const tokenData = await tokenRes.json();
  if (!tokenData.access_token) {
    return Response.redirect(new URL('/?error=token_failed', url.origin), 302);
  }

  const userRes = await fetch('https://kapi.kakao.com/v2/user/me', {
    headers: { Authorization: `Bearer ${tokenData.access_token}` },
  });
  const kakaoUser = await userRes.json();
  const kakaoId = String(kakaoUser.id);
  const email   = kakaoUser.kakao_account?.email || `${kakaoId}@kakao.local`;
  const name    = kakaoUser.kakao_account?.profile?.nickname || '카카오사용자';
  const avatar  = kakaoUser.kakao_account?.profile?.profile_image_url || null;

  const db = env.DB;
  let dbUser = await db.prepare(
    'SELECT id, name, email, avatar FROM users WHERE kakao_id = ?'
  ).bind(kakaoId).first();

  if (!dbUser) {
    await db.prepare(
      'INSERT INTO users (kakao_id, email, name, avatar, provider) VALUES (?, ?, ?, ?, ?)'
    ).bind(kakaoId, email, name, avatar, 'kakao').run();

    dbUser = await db.prepare(
      'SELECT id, name, email, avatar FROM users WHERE kakao_id = ?'
    ).bind(kakaoId).first();
  }

  // 한글 포함 JSON을 안전하게 base64 인코딩
  const json = JSON.stringify(dbUser);
  const sessionData = btoa(encodeURIComponent(json).replace(/%([0-9A-F]{2})/g, (_, p1) => String.fromCharCode(parseInt(p1, 16))));

  const headers = new Headers({ Location: next });
  headers.append('Set-Cookie',
    `session=${sessionData}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${60*60*24*7}`
  );
  return new Response(null, { status: 302, headers });
}
