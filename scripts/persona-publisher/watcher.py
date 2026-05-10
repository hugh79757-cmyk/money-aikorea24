import os
import json
from datetime import datetime

BLOGSMITH_OUTPUT = "/Users/twinssn/Projects/blogsmith/output/persona.aikorea24"
DONE_JSON = os.path.join(os.path.dirname(__file__), "done.json")

def load_done():
    if os.path.exists(DONE_JSON):
        with open(DONE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_done(done: dict):
    with open(DONE_JSON, "w", encoding="utf-8") as f:
        json.dump(done, f, ensure_ascii=False, indent=2)

def get_new_files() -> list[str]:
    done = load_done()
    result = []
    if not os.path.isdir(BLOGSMITH_OUTPUT):
        print(f"[watcher] 경로 없음: {BLOGSMITH_OUTPUT}")
        return result
    for fname in sorted(os.listdir(BLOGSMITH_OUTPUT)):
        if not fname.endswith(".md"):
            continue
        if fname in done:
            continue
        result.append(os.path.join(BLOGSMITH_OUTPUT, fname))
    return result

def mark_done(fname: str, status: str, **kwargs):
    done = load_done()
    done[fname] = {"status": status, "recorded_at": datetime.now().isoformat(), **kwargs}
    save_done(done)
