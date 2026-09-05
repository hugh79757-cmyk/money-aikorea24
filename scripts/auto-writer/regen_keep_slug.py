"""
일괄 재생성 — 슬러그 고정 (URL 유지)
- publish_ledger 기준으로 기존 slug 파일 overwrite
- pubDate/heroImage 원본 유지, slug 재생성 안함
- geo fix (COUNTY_TO_REGION) 반영된 writer 프롬프트로 LLM 재생성
- checkpoint: data/regen_checkpoint.json (resume)
"""
import os, re, sys, json, time, sqlite3, yaml
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
BLOG_DIR = ROOT / "src/content/blog"
DB_PATH = Path(__file__).resolve().parent / "db/auto-writer.db"
CKPT_PATH = Path(__file__).resolve().parent / "db/regen_checkpoint.json"
LOG_PATH = Path(__file__).resolve().parent / "logs/regen.log"

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from title_generator import refinish_title
from shared.db_utils import get_related_posts, increment_internal_link_count
from shared.thumbnail_gen import generate as gen_thumbnail
from shared.reviewer import review_article
from writer import generate_article, proofread
from validator import validate_and_fix, fill_related_posts, make_persona_cta_block, clean_prompt_leaks
# fix_bold is in pipeline, import inline
import pipeline as pl

# config
with open(Path(__file__).resolve().parent / "config/category_map.yaml", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)
PERSONA_CTA = CONFIG["persona_cta"]
CTA_VARIANTS = CONFIG.get("cta_variants", {})

def log(msg):
    print(msg, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as lf:
            lf.write(f"{datetime.now().isoformat()} {msg}\n")
    except: pass

def load_ckpt():
    if CKPT_PATH.exists():
        try: return json.loads(CKPT_PATH.read_text())
        except: return {}
    return {}

def save_ckpt(ckpt):
    tmp = CKPT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(ckpt, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CKPT_PATH)

def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    fm = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm_text = text[3:end]
            body = text[end+4:]
            try:
                fm = yaml.safe_load(fm_text) or {}
            except:
                fm = {}
    return fm, body

def main(limit=None, dry_run=False, offset=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT slug, service_id, title, category FROM publish_ledger ORDER BY id").fetchall()
    log(f"ledger {len(rows)} entries, limit={limit} dry_run={dry_run} offset={offset}")
    ckpt = load_ckpt()
    done = set(ckpt.get("done", []))
    failed = ckpt.get("failed", {})
    # resume
    todo = [r for r in rows[offset:] if r["slug"] not in done]
    if limit:
        todo = todo[:limit]
    log(f"todo {len(todo)} after resume")

    for idx, r in enumerate(todo):
        slug = r["slug"]
        service_id = r["service_id"]
        md_path = BLOG_DIR / f"{slug}.md"
        if not md_path.exists():
            log(f"[SKIP] file missing {slug}")
            done.add(slug)
            ckpt["done"] = sorted(done)
            save_ckpt(ckpt)
            continue
        svc = conn.execute("SELECT * FROM services WHERE service_id=?", (service_id,)).fetchone()
        if not svc:
            log(f"[SKIP] service not found {service_id}")
            done.add(slug)
            ckpt["done"] = sorted(done)
            save_ckpt(ckpt)
            continue
        service = dict(svc)
        # original frontmatter preserve
        orig_fm, _ = parse_frontmatter(md_path)
        orig_pub = orig_fm.get("pubDate")
        orig_hero = orig_fm.get("heroImage")

        log(f"[{idx+1}/{len(todo)}] regen {slug[:60]} | {service['title'][:30]}")
        if dry_run:
            # just check geo fix: what region would be used now
            from shared.persona_stats import resolve_region
            from writer import build_user_prompt
            region = resolve_region(service)
            prompt = build_user_prompt(service)
            log(f"  [dry] region={region} prompt_has_region={region in prompt}")
            continue

        result = generate_article(service)
        if not result:
            log(f"  ❌ GPT 실패 {slug}")
            failed[slug] = "GPT 실패"
            ckpt["failed"] = failed
            save_ckpt(ckpt)
            time.sleep(2)
            continue
        body = result["body"]
        model_used = result.get("model","unknown")
        body = proofread(body)
        # title extract
        m = re.match(r'^#\s+(.+)$', body.split('\n')[0].strip())
        extracted = m.group(1).strip() if m else None
        if extracted:
            body = re.sub(r'^#\s+.*?\n?', '', body, count=1).strip()
        final_title = extracted or service["title"]
        final_title = refinish_title(final_title)
        # inline CTA
        body = pl.insert_inline_ctas(body, service)
        # reviewer
        body, review_issues, needs_review = review_article(body, model_used)
        # validator
        persona = service.get("persona","default")
        cat = service.get("category","general")
        cta_url = PERSONA_CTA.get(persona, PERSONA_CTA.get("default","https://persona.aikorea24.kr/my-persona"))
        vkey = f"{cat}-{persona}"
        v = CTA_VARIANTS.get(vkey, CTA_VARIANTS.get("default", {}))
        end_list = v.get("end", ["내 또래는 어떤 혜택을 받고 있을까?"]*2)
        import hashlib
        sidx = int(hashlib.md5(str(service_id).encode()).hexdigest(),16)%2
        end_text = end_list[sidx % len(end_list)]
        cta_block = make_persona_cta_block(cta_url, persona=persona, end_text=end_text)
        body, issues = validate_and_fix(body, cta_url, cta_block=cta_block)
        if "BODY_TOO_SHORT" in issues:
            log(f"  ❌ BODY_TOO_SHORT {slug}")
            failed[slug] = "BODY_TOO_SHORT"
            ckpt["failed"]=failed
            save_ckpt(ckpt)
            continue
        body = pl.fix_bold_decimal_percent(body)
        # RELATED_POSTS - use fixed slug (current)
        related = get_related_posts(service["category"], slug)
        body = fill_related_posts(body, related)
        for p in related:
            try: increment_internal_link_count(p["slug"])
            except: pass
        # thumbnail - reuse same slug
        hero_image = orig_hero
        try:
            new_hero = gen_thumbnail(slug, final_title, service["category"])
            if new_hero: hero_image = new_hero
        except Exception as e:
            log(f"  thumb fail {e}")

        # frontmatter - keep orig pubDate, update title/desc but slug unchanged
        description = service.get("summary","")[:120]
        tags = [cat, service.get("persona","")] + (["투자","ETF"] if cat=="invest" else ["지원금","혜택"])
        tags = [t for t in tags if t]
        # build frontmatter with preserved pubDate
        from validator import make_frontmatter
        fm_new = make_frontmatter(final_title, description, cat, hero_image, tags, slug, needs_review=needs_review)
        # replace pubDate with orig
        if orig_pub:
            # orig_pub may be datetime, convert to string
            pub_str = str(orig_pub)
            # make_frontmatter uses now, replace
            fm_new = re.sub(r'pubDate:.*\n', f'pubDate: {pub_str}\n', fm_new)
            fm_new = re.sub(r'updatedDate:.*\n', f'updatedDate: {pub_str}\n', fm_new)

        final_md = fm_new + body
        # overwrite same path — slug unchanged
        md_path.write_text(final_md, encoding="utf-8")
        log(f"  ✅ overwrite {slug} ({len(body)}자) model={model_used} needs_review={needs_review}")
        done.add(slug)
        ckpt["done"] = sorted(done)
        ckpt["failed"] = failed
        save_ckpt(ckpt)
        # interval to avoid quota burst
        time.sleep(1)

    log(f"regen done. total done={len(done)} failed={len(failed)}")
    conn.close()

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()
    main(limit=args.limit, dry_run=args.dry_run, offset=args.offset)
