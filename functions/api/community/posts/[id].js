export async function onRequestGet({ request, env, params }) {
  const H = { 'Content-Type': 'application/json' };
  const postId = parseInt(params.id);
  if (isNaN(postId)) return new Response(JSON.stringify({ error: 'invalid id' }), { status: 400, headers: H });

  await env.DB.prepare('UPDATE persona_posts SET views = views + 1 WHERE id = ?').bind(postId).run();
  const post = await env.DB.prepare(`
    SELECT pp.*, COALESCE(u.nickname, u.name, '익명') as author_name
    FROM persona_posts pp JOIN users u ON u.id = pp.user_id
    WHERE pp.id = ?
  `).bind(postId).first();

  if (!post) return new Response(JSON.stringify({ error: 'not found' }), { status: 404, headers: H });
  return new Response(JSON.stringify(post), { headers: H });
}


function getSession(request) {
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/session=([^;]+)/);
  if (!match) return null;
  try {
    return JSON.parse(decodeURIComponent(atob(decodeURIComponent(match[1])).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')));
  } catch { return null; }
}

export async function onRequestDelete({ request, env, params }) {
  const H = { 'Content-Type': 'application/json' };
  const user = getSession(request);
  if (!user) return new Response(JSON.stringify({error:'unauthorized'}), {status:401, headers:H});
  const postId = parseInt(params.id);
  const row = await env.DB.prepare('SELECT user_id FROM persona_posts WHERE id = ?').bind(postId).first();
  if (!row) return new Response(JSON.stringify({error:'not_found'}), {status:404, headers:H});
  if (row.user_id !== user.id && user.id !== 1) return new Response(JSON.stringify({error:'forbidden'}), {status:403, headers:H});
  await env.DB.prepare('DELETE FROM persona_likes WHERE post_id = ?').bind(postId).run();
  await env.DB.prepare('DELETE FROM persona_comments WHERE post_id = ?').bind(postId).run();
  await env.DB.prepare('DELETE FROM persona_posts WHERE id = ?').bind(postId).run();
  return new Response(JSON.stringify({ok:true}), {headers:H});
}
