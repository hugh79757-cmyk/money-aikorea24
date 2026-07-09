import { getSession } from '../_shared/session.js';
import { checkRateLimit } from '../_shared/rate-limit.js';

// 단건 조회: GET /api/community/posts/123
export async function onRequestGet({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const url = new URL(request.url);
  const parts = url.pathname.split('/').filter(Boolean);
  const postId = parts[parts.length - 1];

  try {
    // 단건 조회
    if (postId && !isNaN(postId)) {
      await env.DB.prepare('UPDATE persona_posts SET views = views + 1 WHERE id = ?').bind(parseInt(postId)).run();
      const post = await env.DB.prepare(`
        SELECT pp.*, COALESCE(u.nickname, u.name, '익명') as author_name
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
      SELECT pp.*, COALESCE(u.nickname, u.name, '익명') as author_name,
        (SELECT COUNT(*) FROM persona_comments pc WHERE pc.post_id = pp.id) as comment_count
      FROM persona_posts pp JOIN users u ON u.id = pp.user_id
      ${where} ORDER BY pp.created_at DESC LIMIT ? OFFSET ?
    `).bind(...params, limit, offset).all();

    return new Response(JSON.stringify({ posts: r.results || [], total: cnt?.n || 0 }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'database_error', message: e.message }), { status: 500, headers: H });
  }
}

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const rate = await checkRateLimit({ request, env });
  if (rate) return rate;

  const user = await getSession(request, env);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });

  const { persona_slug, persona_type, region, sex, age, title, content, board_type } = await request.json();
  if (!title?.trim() || !content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });

  /* 입력 길이 제한 */
  if (title.trim().length > 100)    return new Response(JSON.stringify({ error: 'title_too_long' }),   { status: 400, headers: H });
  if (content.trim().length > 5000) return new Response(JSON.stringify({ error: 'content_too_long' }), { status: 400, headers: H });

  try {
    const r = await env.DB.prepare(`
      INSERT INTO persona_posts (user_id, persona_slug, persona_type, region, sex, age, title, content, board_type)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(user.id, persona_slug||'', persona_type||'', region||'', sex||'', age||'', title.trim(), content.trim()).run();

    return new Response(JSON.stringify({ ok: true, id: r.meta?.last_row_id }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'database_error', message: e.message }), { status: 500, headers: H });
  }
}

export async function onRequestDelete({ request, env }) {
  const H = { 'Content-Type': 'application/json' };
  const rate = await checkRateLimit({ request, env });
  if (rate) return rate;

  const user = await getSession(request, env);
  if (!user) return new Response(JSON.stringify({ error: 'unauthorized' }), { status: 401, headers: H });
  const id = new URL(request.url).searchParams.get('id');
  if (!id) return new Response(JSON.stringify({ error: 'no_id' }), { status: 400, headers: H });
  
  try {
    const row = await env.DB.prepare('SELECT user_id FROM persona_posts WHERE id = ?').bind(id).first();
    if (!row) return new Response(JSON.stringify({ error: 'not_found' }), { status: 404, headers: H });
    /* 본인 or 관리자(env.ADMIN_USER_IDS) */
    const admins = (env.ADMIN_USER_IDS || '').split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
    if (row.user_id !== user.id && !admins.includes(user.id)) {
      return new Response(JSON.stringify({ error: 'forbidden' }), { status: 403, headers: H });
    }
    await env.DB.prepare('DELETE FROM persona_likes WHERE post_id = ?').bind(id).run();
    await env.DB.prepare('DELETE FROM persona_comments WHERE post_id = ?').bind(id).run();
    await env.DB.prepare('DELETE FROM persona_posts WHERE id = ?').bind(id).run();
    return new Response(JSON.stringify({ ok: true }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'database_error', message: e.message }), { status: 500, headers: H });
  }
}
