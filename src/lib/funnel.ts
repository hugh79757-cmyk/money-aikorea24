// Funnel telemetry client (Wave 1, T4)
// Wraps the global window.trackFunnel helper (BaseHead.astro, T1) and beacons
// the event to the D1 sink at /api/funnel-log.js (T3).
// visitor_id is read from the `pid` first-party cookie set in Wave 2 (T6).

interface FunnelParams {
  [key: string]: string | number | null;
}

declare global {
  interface Window {
    gtag?: (command: string, eventName: string, params?: Record<string, unknown>) => void;
    trackFunnel?: (event: string, params?: Record<string, unknown>) => void;
  }
}

function readCookie(name: string): string {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[2]) : '';
}

export function track(event: string, params: FunnelParams = {}): void {
  const visitorId = readCookie('pid');

  const trackFunnel = window.trackFunnel;
  if (typeof trackFunnel === 'function') {
    trackFunnel(event, params);
  }

  try {
    const payload = JSON.stringify({ event, ...params, visitor_id: visitorId });
    const blob = new Blob([payload], { type: 'application/json' });
    navigator.sendBeacon('/api/funnel-log', blob);
  } catch {
    /* beacon is best-effort */
  }
}
