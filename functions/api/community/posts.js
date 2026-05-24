
// 단건 조회: GET /api/community/posts/123
export async function onRequestGet({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const url = new URL(request.url);
  const parts = url.pathname.split('/').filter(Boolean);
  const postId = parts[parts.length - 1];

  // 단건 조회
  if (postId && !isNaN(postId)) {
    await env.DB.prepare('UPDATE persona_posts SET views = views + 1 WHERE id = ?').bind(parseInt(postId)).run();
    const post = await env.DB.prepare(`
      SELECT pp.*, u.name as author_name
      FROM persona_posts pp JOIN users u ON u.id = pp.user_id
      WHERE pp.id = ?
    `).bind(parseInt(postId)).first();
    if (!post) return new Response(JSON.stringify({ error: 'not found' }), { status: 404, headers: H });
    return new Response(JSON.stringify(post), { headers: H });
  }

  // 목록 조회
  const slug  = url.searchParams.get('slug') || '';
  const q     = url.searchParams.get('q') || '';
  const board = url.searchParams.get('board') || 'persona';
  const page  = Math.max(1, parseInt(url.searchParams.get('page') || '1'));
  const limit = 20, offset = (page - 1) * limit;

  let where = 'WHERE pp.board_type = ?';
  const params = [board];
  if (slug) { where += ' AND pp.persona_slug = ?'; params.push(slug); }
  if (q)    { where += ' AND (pp.title LIKE ? OR pp.content LIKE ?)'; params.push(`%${q}%`, `%${q}%`); }

  const cnt = await env.DB.prepare(`SELECT COUNT(*) as n FROM persona_posts pp ${where}`).bind(...params).first();
  const r = await env.DB.prepare(`
    SELECT pp.*, u.name as author_name,
      (SELECT COUNT(*) FROM persona_comments pc WHERE pc.post_id = pp.id) as comment_count
    FROM persona_posts pp JOIN users u ON u.id = pp.user_id
    ${where} ORDER BY pp.created_at DESC LIMIT ? OFFSET ?
  `).bind(...params, limit, offset).all();

  return new Response(JSON.stringify({ posts: r.results || [], total: cnt?.n || 0 }), { headers: H });
}

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

  const { persona_slug, persona_type, region, sex, age, title, content, board_type } = await request.json();
  if (!title?.trim() || !content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });

  const r = await env.DB.prepare(`
    INSERT INTO persona_posts (user_id, persona_slug, persona_type, region, sex, age, title, content, board_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(user.id, persona_slug||'', persona_type||'', region||'', sex||'', age||'', title.trim(), content.trim()).run();

  return new Response(JSON.stringify({ ok: true, id: r.meta?.last_row_id }), { headers: H });
}
