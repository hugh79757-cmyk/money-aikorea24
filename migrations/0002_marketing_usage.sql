-- Marketing Persona Studio: daily usage counter (Phase 7, Task A)
-- One row per user per UTC day; count incremented BEFORE LLM call (reserve, R-3).
CREATE TABLE IF NOT EXISTS marketing_usage (
  user_id TEXT NOT NULL,
  day     TEXT NOT NULL,
  count   INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);
