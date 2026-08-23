// Marketing Persona Studio API — auth gate + D1 daily limit + LLM proxy (Phase 7, Task A)
// Precedents: benefit-click.js (corsHeaders + upsert), _shared/session.js (getSession).
import { getSession } from '../_shared/session.js';
import { generateScenario } from './_shared/llm.js';

const ALLOWED_ORIGIN = 'https://persona.aikorea24.kr';
const corsHeaders = { 'Access-Control-Allow-Origin': ALLOWED_ORIGIN, 'Access-Control-Allow-Methods': 'POST, OPTIONS' };
const H = { 'Content-Type': 'application/json', ...corsHeaders };

const DAILY_LIMIT = 5; // A-3
const PERSONA_KEY_RE = /^.{1,20}_(남자|여자)_(10|20|30|40|50|60|70|80)대$/u;

export function onRequestOptions() {
  return new Response(null, { status: 204, headers: corsHeaders });
}

function validateBody(body) {
  if (!body || typeof body !== 'object') return 'bad_request';
  const { mode, product, personaKey } = body;
  if (mode === 'product') {
    if (typeof product !== 'string' || !product.trim() || product.length > 2000) return 'bad_request';
    return null;
  }
  if (mode === 'persona') {
    if (typeof personaKey !== 'string' || !PERSONA_KEY_RE.test(personaKey)) return 'bad_request';
    return null;
  }
  return 'bad_request';
}

export async function onRequestPost({ request, env }) {
  try {
    let body;
    try { body = await request.json(); } catch { 
      return new Response(JSON.stringify({ error: 'bad_request' }), { status: 400, headers: H });
    }
    const invalid = validateBody(body);
    if (invalid) return new Response(JSON.stringify({ error: invalid }), { status: 400, headers: H });

    // Auth gate (MKT-01): kakao session required — payload.id is the user id (callback/kakao.js).
    const session = await getSession(request, env);
    if (!session || !session.id) {
      return new Response(JSON.stringify({ error: 'login_required' }), { status: 401, headers: H });
    }
    const userId = String(session.id);

    // Daily reserve BEFORE LLM call (R-3): failed generations also consume quota. UTC day (R-5).
    const day = new Date().toISOString().slice(0, 10);
    const row = await env.DB.prepare(
      'SELECT count FROM marketing_usage WHERE user_id = ? AND day = ?'
    ).bind(userId, day).first();
    if ((row?.count ?? 0) >= DAILY_LIMIT) {
      return new Response(JSON.stringify({ error: 'rate_limited', remaining: 0 }), { status: 429, headers: H });
    }
    await env.DB.prepare(
      "INSERT INTO marketing_usage (user_id, day, count) VALUES (?, ?, 1) ON CONFLICT(user_id, day) DO UPDATE SET count = count + 1"
    ).bind(userId, day).run();

    try {
      const { scenario, model_used } = await generateScenario({
        mode: body.mode,
        product: typeof body.product === 'string' ? body.product : undefined,
        personaKey: typeof body.personaKey === 'string' ? body.personaKey : undefined,
        env,
      });
      return new Response(JSON.stringify({ ok: true, scenario, model_used }), { headers: H });
    } catch (e) {
      console.log('[marketing] generation_failed', e.message); // no keys/tokens logged
      return new Response(JSON.stringify({ error: 'generation_failed' }), { status: 502, headers: H });
    }
  } catch (e) {
    console.log('[marketing] internal', e.message);
    return new Response(JSON.stringify({ error: 'internal' }), { status: 500, headers: H });
  }
}
