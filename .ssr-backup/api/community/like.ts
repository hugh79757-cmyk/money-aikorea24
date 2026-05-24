import type { APIRoute } from 'astro';
export const prerender = false;

export const POST: APIRoute = async ({ request, locals, cookies }) => {
  const H = { 'Content-Type': 'application/json' };
  const runtime = (locals as any).runtime;
  const db = runtime?.env?.DB;
  const session = cookies.get('session')?.value;
  if (!session) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  let user: any;
  try { user = JSON.parse(atob(session)); } catch {
    return new Response(JSON.stringify({ error: 'bad session' }), { status: 401, headers: H });
  }
  const { post_id } = await request.json() as any;
  const existing = await db.prepare(`SELECT id FROM persona_likes WHERE post_id = ? AND user_id = ?`)
    .bind(post_id, user.id).first();
  if (existing) {
    await db.prepare(`DELETE FROM persona_likes WHERE post_id = ? AND user_id = ?`).bind(post_id, user.id).run();
    await db.prepare(`UPDATE persona_posts SET likes = MAX(0, likes - 1) WHERE id = ?`).bind(post_id).run();
  } else {
    await db.prepare(`INSERT OR IGNORE INTO persona_likes (post_id, user_id) VALUES (?, ?)`).bind(post_id, user.id).run();
    await db.prepare(`UPDATE persona_posts SET likes = likes + 1 WHERE id = ?`).bind(post_id).run();
  }
  const updated = await db.prepare(`SELECT likes FROM persona_posts WHERE id = ?`).bind(post_id).first() as any;
  return new Response(JSON.stringify({ ok: true, likes: updated?.likes || 0 }), { headers: H });
};
