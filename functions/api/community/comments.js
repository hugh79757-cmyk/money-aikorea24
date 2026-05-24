function getSession(request) {
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/session=([^;]+)/);
  if (!match) return null;
  try { return JSON.parse(atob(match[1])); } catch { return null; }
}

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const user = getSession(request);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  const { post_id, content } = await request.json();
  if (!content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });
  await env.DB.prepare('INSERT INTO persona_comments (post_id, user_id, content) VALUES (?, ?, ?)').bind(post_id, user.id, content.trim()).run();
  return new Response(JSON.stringify({ ok: true }), { headers: H });
}
