function generateNickname() {
  const regions = ['서울','부산','대구','인천','광주','대전','울산','경기','강원','충북','충남','전북','전남','경북','경남','제주'];
  const animals = ['냥이','멍이','토끼','사슴','여우','곰돌','판다','너구리','다람쥐','햄찌','펭귄'];
  const r = regions[Math.floor(Math.random() * regions.length)];
  const a = animals[Math.floor(Math.random() * animals.length)];
  const n = Math.floor(1000 + Math.random() * 9000);
  return `${r}${a}${n}`;
}

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');
  const cookieHeader = request.headers.get('Cookie') || '';
  const mktMatch = cookieHeader.match(/pending_marketing=([01])/);
  const marketingConsent = mktMatch && mktMatch[1] === '1' ? 1 : 0;
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
  const realName = kakaoUser.kakao_account?.profile?.nickname || '카카오사용자';
  const avatar  = kakaoUser.kakao_account?.profile?.profile_image_url || null;

  const db = env.DB;
  let dbUser = await db.prepare(
    'SELECT id, name, nickname, email, avatar FROM users WHERE kakao_id = ?'
  ).bind(kakaoId).first();

  if (!dbUser) {
    // 닉네임 중복 회피 (최대 5회 재시도)
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
    // 기존 사용자 중 닉네임 없는 경우 부여
    let nickname = generateNickname();
    for (let i = 0; i < 5; i++) {
      const dup = await db.prepare('SELECT id FROM users WHERE nickname = ?').bind(nickname).first();
      if (!dup) break;
      nickname = generateNickname();
    }
    await db.prepare('UPDATE users SET nickname = ? WHERE id = ?').bind(nickname, dbUser.id).run();
    dbUser.nickname = nickname;
  }

  // 세션에는 닉네임만 노출 (본명 제거)
  const sessionUser = {
    id: dbUser.id,
    name: dbUser.nickname,
    email: dbUser.email,
    avatar: dbUser.avatar,
  };

  const json = JSON.stringify(sessionUser);
  const sessionData = btoa(encodeURIComponent(json).replace(/%([0-9A-F]{2})/g, (_, p1) => String.fromCharCode(parseInt(p1, 16))));

  const headers = new Headers({ Location: next });
  headers.append('Set-Cookie',
    `session=${sessionData}; Path=/; Secure; SameSite=Lax; Max-Age=${60*60*24*7}`
  );
  return new Response(null, { status: 302, headers });
}
