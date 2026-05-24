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
  const { post_id, content } = await request.json() as any;
  if (!content?.trim()) return new Response(JSON.stringify({ error: 'empty' }), { status: 400, headers: H });
  await db.prepare(`INSERT INTO persona_comments (post_id, user_id, content) VALUES (?, ?, ?)`)
    .bind(post_id, user.id, content.trim()).run();
  return new Response(JSON.stringify({ ok: true }), { headers: H });
};
