export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
  try {
    const { benefit_id, seed } = await request.json();
    if (!benefit_id) return new Response(JSON.stringify({ error: 'benefit_id required' }), { status: 400, headers: H });

    // 초기 시드값이 있으면 INSERT, 없으면 +1
    if (seed && seed > 0) {
      await env.DB.prepare(
        'INSERT INTO benefit_clicks (benefit_id, count) VALUES (?, ?) ON CONFLICT(benefit_id) DO NOTHING'
      ).bind(benefit_id, seed).run();
    }

    await env.DB.prepare(
      'INSERT INTO benefit_clicks (benefit_id, count) VALUES (?, 1) ON CONFLICT(benefit_id) DO UPDATE SET count = count + 1, updated_at = datetime(\'now\')'
    ).bind(benefit_id).run();

    const row = await env.DB.prepare(
      'SELECT count FROM benefit_clicks WHERE benefit_id = ?'
    ).bind(benefit_id).first();

    return new Response(JSON.stringify({ ok: true, count: row?.count || 1 }), { headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: H });
  }
}

export async function onRequestGet({ request, env }) {
  const H = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
  const url = new URL(request.url);
  const benefit_id = url.searchParams.get('benefit_id');
  if (!benefit_id) return new Response(JSON.stringify({ error: 'benefit_id required' }), { status: 400, headers: H });

  const row = await env.DB.prepare(
    'SELECT count FROM benefit_clicks WHERE benefit_id = ?'
  ).bind(benefit_id).first();

  return new Response(JSON.stringify({ count: row?.count || 0 }), { headers: H });
}
