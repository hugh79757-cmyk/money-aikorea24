export async function onRequestPost({ request, env, waitUntil }) {
  const { kakao_id, name, avatar } = await request.json();
  if (!kakao_id) return new Response(JSON.stringify({ error: 'no kakao_id' }), { status: 400, headers: { 'Content-Type': 'application/json' } });

  const db = env.DB;
  let dbUser = await db.prepare('SELECT id, name, email, avatar FROM users WHERE kakao_id = ?').bind(kakao_id).first();
  if (!dbUser) {
    await db.prepare('INSERT INTO users (kakao_id, google_id, email, name, avatar, provider) VALUES (?, ?, ?, ?, ?, ?)').bind(kakao_id, '', `${kakao_id}@kakao.local`, name, avatar, 'kakao').run();
    dbUser = await db.prepare('SELECT id, name, email, avatar FROM users WHERE kakao_id = ?').bind(kakao_id).first();
  }

  const sessionData = btoa(JSON.stringify(dbUser));
  const headers = new Headers({ 'Content-Type': 'application/json' });
  headers.append('Set-Cookie', `session=${sessionData}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${60*60*24*7}`);
  return new Response(JSON.stringify({ ok: true, name: dbUser.name }), { headers });
}
