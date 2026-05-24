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

export async function onRequestGet({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const url = new URL(request.url);
  const post_id = url.searchParams.get('post_id');
  if (!post_id) return new Response(JSON.stringify({ comments: [] }), { headers: H });
  const r = await env.DB.prepare(`
    SELECT pc.*, u.name as author_name
    FROM persona_comments pc JOIN users u ON u.id = pc.user_id
    WHERE pc.post_id = ? ORDER BY pc.created_at ASC
  `).bind(parseInt(post_id)).all();
  return new Response(JSON.stringify({ comments: r.results || [] }), { headers: H });
}
