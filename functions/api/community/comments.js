import { getSession } from '../_shared/session.js';

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const user = await getSession(request, env);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  const { post_id, content } = await request.json();
  if (!content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });

  /* 입력 길이 제한 */
  if (content.trim().length > 2000) return new Response(JSON.stringify({ error: 'content_too_long' }), { status: 400, headers: H });

  await env.DB.prepare('INSERT INTO persona_comments (post_id, user_id, content) VALUES (?, ?, ?)').bind(post_id, user.id, content.trim()).run();
  return new Response(JSON.stringify({ ok: true }), { headers: H });
}

export async function onRequestGet({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const url = new URL(request.url);
  const post_id = url.searchParams.get('post_id');
  if (!post_id) return new Response(JSON.stringify({ comments: [] }), { headers: H });
  const r = await env.DB.prepare(`
    SELECT pc.*, COALESCE(u.nickname, u.name, '익명') as author_name
    FROM persona_comments pc JOIN users u ON u.id = pc.user_id
    WHERE pc.post_id = ? ORDER BY pc.created_at ASC
  `).bind(parseInt(post_id)).all();
  return new Response(JSON.stringify({ comments: r.results || [] }), { headers: H });
}

export async function onRequestDelete({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const user = await getSession(request, env);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  const id = new URL(request.url).searchParams.get('id');
  if (!id) return new Response(JSON.stringify({ error: 'no_id' }), { status: 400, headers: H });
  const row = await env.DB.prepare('SELECT user_id FROM persona_comments WHERE id = ?').bind(id).first();
  if (!row) return new Response(JSON.stringify({ error: 'not_found' }), { status: 404, headers: H });
  const admins = (env.ADMIN_USER_IDS || '1').split(',').map(s => parseInt(s.trim(), 10));
  if (row.user_id !== user.id && !admins.includes(user.id)) {
    return new Response(JSON.stringify({ error: 'forbidden' }), { status: 403, headers: H });
  }
  await env.DB.prepare('DELETE FROM persona_comments WHERE id = ?').bind(id).run();
  return new Response(JSON.stringify({ ok: true }), { headers: H });
}
