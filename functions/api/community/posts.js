function getSession(request) {
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/session=([^;]+)/);
  if (!match) return null;
  try { return JSON.parse(atob(match[1])); } catch { return null; }
}

export async function onRequestGet({ request, env }) {
  const db = env.DB;
  const url = new URL(request.url);
  const slug = url.searchParams.get('slug') || '';
  const q    = url.searchParams.get('q') || '';
  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1'));
  const limit = 20, offset = (page - 1) * limit;
  const H = { 'Content-Type': 'application/json' };

  let where = 'WHERE 1=1';
  const params = [];
  if (slug) { where += ' AND pp.persona_slug = ?'; params.push(slug); }
  if (q)    { where += ' AND (pp.title LIKE ? OR pp.content LIKE ?)'; params.push(`%${q}%`, `%${q}%`); }

  const cnt = await db.prepare(`SELECT COUNT(*) as n FROM persona_posts pp ${where}`).bind(...params).first();
  const r = await db.prepare(`
    SELECT pp.*, u.name as author_name,
      (SELECT COUNT(*) FROM persona_comments pc WHERE pc.post_id = pp.id) as comment_count
    FROM persona_posts pp JOIN users u ON u.id = pp.user_id
    ${where} ORDER BY pp.created_at DESC LIMIT ? OFFSET ?
  `).bind(...params, limit, offset).all();

  return new Response(JSON.stringify({ posts: r.results || [], total: cnt?.n || 0 }), { headers: H });
}

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const user = getSession(request);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });

  const { persona_slug, persona_type, region, sex, age, title, content } = await request.json();
  if (!title?.trim() || !content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });

  const r = await env.DB.prepare(`
    INSERT INTO persona_posts (user_id, persona_slug, persona_type, region, sex, age, title, content)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(user.id, persona_slug||'', persona_type||'', region||'', sex||'', age||'', title.trim(), content.trim()).run();

  return new Response(JSON.stringify({ ok: true, id: r.meta?.last_row_id }), { headers: H });
}
