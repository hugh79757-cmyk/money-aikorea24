// Funnel event sink (Wave 1, T3)
// Modeled on functions/api/benefit-click.js (CORS + env.DB pattern).
// Receives funnel-analytics events via POST and writes them to D1.
// No PII is stored — only a truncated SHA-256 hash of cf-connecting-ip.

const ALLOWED_ORIGIN = 'https://persona.aikorea24.kr';

const FUNNEL_EVENTS = new Set([
  'blog_cta_click',
  'persona_open',
  'persona_step',
  'persona_result',
  'ad_impression',
]);

function corsHeadersFor(request) {
  const origin = request && request.headers ? request.headers.get('Origin') : null;
  const allow = origin === ALLOWED_ORIGIN ? origin : ALLOWED_ORIGIN;
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

export async function onRequestOptions(context) {
  return new Response(null, { status: 204, headers: corsHeadersFor(context && context.request) });
}

export async function onRequestPost({ request, env }) {
  const H = { 'Content-Type': 'application/json', ...corsHeadersFor(request) };
  try {
    const body = await request.json();
    const { event, src, cat, persona, step, age_band, visitor_id } = body || {};

    if (!event || !FUNNEL_EVENTS.has(event)) {
      return new Response(JSON.stringify({ error: 'invalid event' }), { status: 400, headers: H });
    }

    const ip = request.headers.get('cf-connecting-ip') || '';
    const ua_hash = ip ? (await sha256(ip)).slice(0, 16) : '';

    await env.DB.prepare(
      `INSERT INTO funnel_events (event, src, cat, persona, step, age_band, visitor_id, ua_hash)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(event, src ?? null, cat ?? null, persona ?? null, step ?? null, age_band ?? null, visitor_id ?? null, ua_hash)
      .run();

    return new Response(null, { status: 204, headers: H });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: H });
  }
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}
