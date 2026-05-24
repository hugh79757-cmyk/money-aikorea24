import type { APIRoute } from 'astro';
export const prerender = false;

export const GET: APIRoute = async ({ request, locals }) => {
  const runtime = (locals as any).runtime;
  const db = runtime?.env?.DB;
  const url = new URL(request.url);
  const slug = url.searchParams.get('slug') || '';
  const q    = url.searchParams.get('q') || '';
  const page = Math.max(1, parseInt(url.searchParams.get('page') || '1'));
  const limit = 20;
  const offset = (page - 1) * limit;
  const H = { 'Content-Type': 'application/json' };

  if (!db) return new Response(JSON.stringify({ posts: [], total: 0 }), { headers: H });

  let where = 'WHERE 1=1';
  const params: any[] = [];
  if (slug) { where += ' AND pp.persona_slug = ?'; params.push(slug); }
  if (q)    { where += ' AND (pp.title LIKE ? OR pp.content LIKE ?)'; params.push(`%${q}%`, `%${q}%`); }

  const cnt = await db.prepare(`SELECT COUNT(*) as n FROM persona_posts pp ${where}`).bind(...params).first() as any;
  const r = await db.prepare(`
    SELECT pp.*, u.name as author_name,
      (SELECT COUNT(*) FROM persona_comments pc WHERE pc.post_id = pp.id) as comment_count
    FROM persona_posts pp JOIN users u ON u.id = pp.user_id
    ${where} ORDER BY pp.created_at DESC LIMIT ? OFFSET ?
  `).bind(...params, limit, offset).all();

  return new Response(JSON.stringify({ posts: r.results || [], total: cnt?.n || 0 }), { headers: H });
};

export const POST: APIRoute = async ({ request, locals, cookies }) => {
  const H = { 'Content-Type': 'application/json' };
  const runtime = (locals as any).runtime;
  const db = runtime?.env?.DB;
  const session = cookies.get('session')?.value;
  if (!session) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });

  let user: any;
  try { user = JSON.parse(atob(session)); } catch {
    return new Response(JSON.stringify({ error: 'invalid session' }), { status: 401, headers: H });
  }

  const body = await request.json() as any;
  const { persona_slug, persona_type, region, sex, age, title, content } = body;
  if (!title?.trim() || !content?.trim())
    return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });

  const r = await db.prepare(`
    INSERT INTO persona_posts (user_id, persona_slug, persona_type, region, sex, age, title, content)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(user.id, persona_slug||'', persona_type||'', region||'', sex||'', age||'', title.trim(), content.trim()).run();

  return new Response(JSON.stringify({ ok: true, id: r.meta?.last_row_id }), { headers: H });
};
