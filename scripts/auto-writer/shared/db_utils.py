import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/auto-writer.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS services (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id      TEXT UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    category        TEXT,
    field           TEXT,
    summary         TEXT,
    detail          TEXT,
    target          TEXT,
    apply_method    TEXT,
    contact         TEXT,
    org_name        TEXT,
    detail_url      TEXT,
    persona         TEXT,
    persona_hint    TEXT,
    source          TEXT DEFAULT 'gov24',
    status          TEXT DEFAULT 'pending',
    collected_at    TEXT,
    published_at    TEXT,
    modified_at     TEXT
);

CREATE TABLE IF NOT EXISTS publish_ledger (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id       TEXT NOT NULL,
    slug             TEXT NOT NULL,
    title            TEXT NOT NULL,
    category         TEXT,
    persona          TEXT,
    internal_link_count INTEGER DEFAULT 0,
    published_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fetch_meta (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    last_fetched  TEXT NOT NULL,
    total_fetched INTEGER DEFAULT 0
);
"""

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn

def get_last_fetched():
    conn = get_conn()
    row = conn.execute(
        "SELECT last_fetched FROM fetch_meta ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["last_fetched"] if row else "20260101000000"

def update_fetch_meta(total):
    conn = get_conn()
    conn.execute(
        "INSERT INTO fetch_meta (last_fetched, total_fetched) VALUES (?,?)",
        (datetime.now().strftime("%Y%m%d%H%M%S"), total)
    )
    conn.commit()
    conn.close()

def get_pending_count():
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM services WHERE status='pending'"
    ).fetchone()
    conn.close()
    return row["cnt"]

def get_today_published_count():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM publish_ledger WHERE published_at LIKE ?",
        (f"{today}%",)
    ).fetchone()
    conn.close()
    return row["cnt"]

def pick_next_service(category_quota: dict):
    """카테고리 가중치 기반으로 다음 발행할 서비스 선택"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM publish_ledger GROUP BY category"
    ).fetchall()
    published = {r["category"]: r["cnt"] for r in rows}
    total_pub = sum(published.values()) or 1

    deficit = {
        cat: quota - (published.get(cat, 0) / total_pub)
        for cat, quota in category_quota.items()
    }
    priority_cats = sorted(deficit, key=deficit.get, reverse=True)

    for cat in priority_cats:
        row = conn.execute(
            """SELECT * FROM services
               WHERE status='pending' AND category=?
               ORDER BY collected_at ASC LIMIT 1""",
            (cat,)
        ).fetchone()
        if row:
            conn.close()
            return dict(row)

    row = conn.execute(
        "SELECT * FROM services WHERE status='pending' ORDER BY collected_at ASC LIMIT 1"
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_related_posts(category, exclude_slug, limit=3):
    """내부 링크 적은 글 우선 추출 (편중 방지)"""
    conn = get_conn()
    rows = conn.execute(
        """SELECT slug, title, category FROM publish_ledger
           WHERE category=? AND slug!=?
           ORDER BY internal_link_count ASC, published_at DESC
           LIMIT ?""",
        (category, exclude_slug, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def increment_internal_link_count(slug):
    conn = get_conn()
    conn.execute(
        "UPDATE publish_ledger SET internal_link_count = internal_link_count + 1 WHERE slug=?",
        (slug,)
    )
    conn.commit()
    conn.close()

def mark_published(service_id, slug, title, category, persona, model_used=""):
    conn = get_conn()
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE services SET status='published', published_at=? WHERE service_id=?",
        (now, service_id)
    )
    conn.execute(
        """INSERT INTO publish_ledger
           (service_id, slug, title, category, persona, model_used, published_at)
           VALUES (?,?,?,?,?,?,?)""",
        (service_id, slug, title, category, persona, model_used, now)
    )
    conn.commit()
    conn.close()

def mark_error(service_id, reason=""):
    conn = get_conn()
    conn.execute(
        "UPDATE services SET status='error' WHERE service_id=?",
        (service_id,)
    )
    conn.commit()
    conn.close()
