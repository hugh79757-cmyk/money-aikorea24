/**
 * D1-based rate limiting middleware
 * Uses D1 table 'rate_limits' with columns: ip, endpoint, window_start, count
 * Primary key on (ip, endpoint, window_start)
 * Note: For production, Cloudflare WAF rate limiting is recommended (lower latency)
 */

const WINDOW_SECONDS = 60;

// Rate limits per endpoint (requests per window)
const LIMITS = {
  'POST:/api/community/posts': 10,
  'DELETE:/api/community/posts': 10,
  'POST:/api/community/comments': 10,
  'DELETE:/api/community/comments': 10,
  'POST:/api/community/like': 20,
};

export async function checkRateLimit({ request, env }) {
  const method = request.method;
  const url = new URL(request.url);
  const endpoint = `${method}:${url.pathname}`;
  const limit = LIMITS[endpoint];
  
  // No limit defined for this endpoint
  if (!limit) return null;

  // Get client IP (CF-Connecting-IP header from Cloudflare)
  const ip = request.headers.get('CF-Connecting-IP') || 
             request.headers.get('X-Forwarded-For')?.split(',')[0]?.trim() || 
             'unknown';

  const key = `${ip}:${endpoint}`;
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % WINDOW_SECONDS);

  try {
    // Check current count
    const row = await env.DB.prepare(
      'SELECT count FROM rate_limits WHERE ip = ? AND endpoint = ? AND window_start = ?'
    ).bind(ip, endpoint, windowStart).first();

    if (row) {
      if (row.count >= limit) {
        return new Response(
          JSON.stringify({ error: 'rate_limited', message: 'Too many requests' }),
          { status: 429, headers: { 'Content-Type': 'application/json', 'Retry-After': String(WINDOW_SECONDS) } }
        );
      }
      // Increment count
      await env.DB.prepare(
        'UPDATE rate_limits SET count = count + 1 WHERE ip = ? AND endpoint = ? AND window_start = ?'
      ).bind(ip, endpoint, windowStart).run();
    } else {
      // Insert new window
      await env.DB.prepare(
        'INSERT INTO rate_limits (ip, endpoint, window_start, count) VALUES (?, ?, ?, 1)'
      ).bind(ip, endpoint, windowStart).run();
    }
  } catch (e) {
    // On D1 error, allow request but log (fail-open for availability)
    console.warn('Rate limit check failed:', e.message);
  }

  return null; // No rate limit exceeded
}

// Helper to create the rate_limits table (run once via D1 migration)
export const createRateLimitTable = `
CREATE TABLE IF NOT EXISTS rate_limits (
  ip TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (ip, endpoint, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);
`;