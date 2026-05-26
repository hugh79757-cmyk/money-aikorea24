import { getSession } from '../_shared/session.js';

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const user = await getSession(request, env);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  const { post_id } = await request.json();
  const existing = await env.DB.prepare('SELECT id FROM persona_likes WHERE post_id = ? AND user_id = ?').bind(post_id, user.id).first();
  if (existing) {
    await env.DB.prepare('DELETE FROM persona_likes WHERE post_id = ? AND user_id = ?').bind(post_id, user.id).run();
    await env.DB.prepare('UPDATE persona_posts SET likes = MAX(0, likes - 1) WHERE id = ?').bind(post_id).run();
  } else {
    await env.DB.prepare('INSERT OR IGNORE INTO persona_likes (post_id, user_id) VALUES (?, ?)').bind(post_id, user.id).run();
    await env.DB.prepare('UPDATE persona_posts SET likes = likes + 1 WHERE id = ?').bind(post_id).run();
  }
  const updated = await env.DB.prepare('SELECT likes FROM persona_posts WHERE id = ?').bind(post_id).first();
  return new Response(JSON.stringify({ ok: true, likes: updated?.likes || 0 }), { headers: H });
}
