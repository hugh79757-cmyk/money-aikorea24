-- persona-db (Cloudflare D1) — 리포지토리에 마이그레이션 파일 없음.
-- Functions SQL + scripts/generate-seed-posts.mjs 출력을 역추론한 스키마 (2026-05-25).
-- 프로덕션 실제 DDL 확인:
--   wrangler d1 execute persona-db --remote --command \
--     "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"

-- ── users ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  kakao_id          TEXT UNIQUE,
  google_id         TEXT DEFAULT '',
  email             TEXT,
  name              TEXT,
  nickname          TEXT UNIQUE,
  avatar            TEXT,
  provider          TEXT NOT NULL DEFAULT 'kakao',  -- 'kakao' | 'seed' 등
  marketing_consent INTEGER DEFAULT 0,
  agreed_at         TEXT,                           -- ISO8601
  created_at        TEXT DEFAULT (datetime('now'))
);

-- ── persona_posts ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS persona_posts (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id       INTEGER NOT NULL REFERENCES users(id),
  persona_slug  TEXT DEFAULT '',
  persona_type  TEXT DEFAULT '',
  region        TEXT DEFAULT '',
  sex           TEXT DEFAULT '',
  age           TEXT DEFAULT '',
  title         TEXT NOT NULL,
  content       TEXT NOT NULL,
  board_type    TEXT NOT NULL DEFAULT 'persona',  -- 'persona' | 'benefit'
  views         INTEGER NOT NULL DEFAULT 0,
  likes         INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_posts_board_created
  ON persona_posts (board_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_slug
  ON persona_posts (persona_slug);

-- ── persona_comments ──────────────────────────────────
CREATE TABLE IF NOT EXISTS persona_comments (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id    INTEGER NOT NULL REFERENCES persona_posts(id) ON DELETE CASCADE,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  content    TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_comments_post
  ON persona_comments (post_id, created_at ASC);

-- ── persona_likes ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS persona_likes (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES persona_posts(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id),
  UNIQUE (post_id, user_id)
);

-- ── benefit_clicks (혜택 카드 클릭 집계) ───────────────
CREATE TABLE IF NOT EXISTS benefit_clicks (
  benefit_id  TEXT PRIMARY KEY,
  count       INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT DEFAULT (datetime('now'))
);

-- 시드 전용 사용자 (generate-seed-posts.mjs)
-- INSERT OR IGNORE INTO users (id, kakao_id, name, provider) VALUES (0, 'seed-0', 'AI페르소나', 'seed');
