export async function onRequestGet({ request, env, params }) {
  const H = { 'Content-Type': 'application/json' };
  const postId = parseInt(params.id);
  if (isNaN(postId)) return new Response(JSON.stringify({ error: 'invalid id' }), { status: 400, headers: H });

  await env.DB.prepare('UPDATE persona_posts SET views = views + 1 WHERE id = ?').bind(postId).run();
  const post = await env.DB.prepare(`
    SELECT pp.*, u.name as author_name
    FROM persona_posts pp JOIN users u ON u.id = pp.user_id
    WHERE pp.id = ?
  `).bind(postId).first();

  if (!post) return new Response(JSON.stringify({ error: 'not found' }), { status: 404, headers: H });
  return new Response(JSON.stringify(post), { headers: H });
}
