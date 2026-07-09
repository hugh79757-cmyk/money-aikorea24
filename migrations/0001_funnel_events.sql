-- Funnel instrumentation (Wave 1, T2)
-- Mirrors the schema consumed by functions/api/funnel-log.js (T3).
CREATE TABLE IF NOT EXISTS funnel_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT DEFAULT (datetime('now')),
  event       TEXT,
  src         TEXT,
  cat         TEXT,
  persona     TEXT,
  step        TEXT,
  age_band    TEXT,
  visitor_id  TEXT,
  ua_hash     TEXT
);

CREATE INDEX IF NOT EXISTS idx_funnel_event     ON funnel_events(event);
CREATE INDEX IF NOT EXISTS idx_funnel_visitor   ON funnel_events(visitor_id);
