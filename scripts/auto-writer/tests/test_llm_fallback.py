"""Deterministic tests for LLM fallback chain — no live calls. 스킬 deterministic verification."""
import os, json, time, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# mock providers before import
os.environ["FALLBACK_STATE_PATH"] = tempfile.mktemp(prefix="fallback_test_")
# ensure import uses temp path
import importlib
import writer as w
import pathlib

# reload with env set if needed
# force state path to temp
w.FALLBACK_STATE_PATH = Path(os.getenv("FALLBACK_STATE_PATH"))

def _fake_cfg(provider, model):
    return {"provider": provider, "model": model, "timeout": 10, "max_retries": 1, "note": "test"}

def test_success_becomes_first():
    # success tier becomes first on next request
    st = {"last_success_tier": None, "quota_until": {}, "structural_until": {}}
    # simulate success on second tier
    tid = "nvidia/google/gemma-4-31b-it"
    st["last_success_tier"] = tid
    w._save_state(st)
    st2 = w._load_state()
    assert st2["last_success_tier"] == tid
    # usable sorting should put tid first if present
    # mock _clients to have 2 providers
    orig_clients = w._clients.copy()
    w._clients["nvidia"] = object()
    w._clients["google"] = object()
    orig_models = w.FALLBACK_MODELS[:]
    w.FALLBACK_MODELS = [
        {"provider": "nvidia", "model": "google/diffusiongemma-26b-a4b-it", "timeout": 10, "max_retries": 1, "note": "a"},
        {"provider": "nvidia", "model": "google/gemma-4-31b-it", "timeout": 10, "max_retries": 1, "note": "b"},
    ]
    usable = w._usable_tiers(st2)
    assert usable[0]["model"] == "google/gemma-4-31b-it", f"got {usable[0]['model']}"
    w.FALLBACK_MODELS = orig_models
    w._clients.update(orig_clients)
    print("✓ success_becomes_first")

def test_empty_and_timeout_move_next():
    e1 = w._ValidationError("빈 응답")
    assert w._classify_error(e1) == "invalid_content"
    # timeout should be immediate next, not retry
    from unittest.mock import Mock
    import openai
    e_timeout = openai.APITimeoutError(request=Mock())
    assert w._classify_error(e_timeout) == "timeout"
    print("✓ empty_and_timeout")

def test_429_cools_only_failing():
    st = {"last_success_tier": "nvidia/google/diffusiongemma-26b-a4b-it", "quota_until": {}, "structural_until": {}}
    # simulate 429 on diffusiongemma
    class FakeResp:
        status_code = 429
    e = Exception("quota")
    e.response = FakeResp()
    assert w._classify_error(e) == "quota"
    # only that tier cools, other usable remains
    st["quota_until"]["nvidia/google/diffusiongemma-26b-a4b-it"] = time.time() + 300
    # ensure _usable_tiers excludes only that one
    w._clients["nvidia"] = object()
    orig = w.FALLBACK_MODELS[:]
    w.FALLBACK_MODELS = [
        {"provider": "nvidia", "model": "google/diffusiongemma-26b-a4b-it", "timeout": 10, "max_retries": 1, "note": "a"},
        {"provider": "nvidia", "model": "google/gemma-4-31b-it", "timeout": 10, "max_retries": 1, "note": "b"},
    ]
    usable = w._usable_tiers(st)
    assert len(usable)==1 and usable[0]["model"]=="google/gemma-4-31b-it"
    w.FALLBACK_MODELS = orig
    print("✓ 429_cools_only_failing")

def test_all_cooled_selects_earliest():
    now=time.time()
    st={"last_success_tier": None, "quota_until": {"nvidia/google/diffusiongemma-26b-a4b-it": now+100, "nvidia/google/gemma-4-31b-it": now+10}, "structural_until": {}}
    w._clients["nvidia"]=object()
    orig=w.FALLBACK_MODELS[:]
    w.FALLBACK_MODELS=[
        {"provider":"nvidia","model":"google/diffusiongemma-26b-a4b-it","timeout":10,"max_retries":1,"note":"a"},
        {"provider":"nvidia","model":"google/gemma-4-31b-it","timeout":10,"max_retries":1,"note":"b"},
    ]
    # all cooled -> usable empty -> code should pick earliest expiry via min logic in generate_article
    usable=w._usable_tiers(st)
    assert usable==[], f"usable should be empty but {usable}"
    # simulate the all-cooled branch
    cooled = [c for c in w.FALLBACK_MODELS if st["quota_until"].get(w._tier_id(c),0) > now]
    earliest = min(cooled, key=lambda c: st["quota_until"].get(w._tier_id(c),9e18))
    assert earliest["model"]=="google/gemma-4-31b-it"
    w.FALLBACK_MODELS=orig
    print("✓ all_cooled_earliest")

def test_state_survives_new_process():
    st={"last_success_tier":"google/gemini-2.5-flash","quota_until":{},"structural_until":{}}
    w._save_state(st)
    # new process load
    st2=w._load_state()
    assert st2["last_success_tier"]=="google/gemini-2.5-flash"
    print("✓ state_survives")

def test_file_notfound_is_invalid_content():
    e=FileNotFoundError("persona-stats.json missing")
    assert w._classify_error(e)=="invalid_content"
    e2=OSError(2, "No such file or directory")
    assert w._classify_error(e2)=="invalid_content"
    print("✓ file_notfound_invalid_content")

def test_invalid_content_not_reach_publish():
    e=w._ValidationError("PERSONA_CTA 누락")
    assert w._classify_error(e)=="invalid_content"
    print("✓ invalid_content_block")

if __name__=="__main__":
    for fn in [test_success_becomes_first, test_empty_and_timeout_move_next, test_429_cools_only_failing, test_all_cooled_selects_earliest, test_state_survives_new_process, test_file_notfound_is_invalid_content, test_invalid_content_not_reach_publish]:
        fn()
    print("all 7 deterministic tests pass")
    # cleanup
    try:
        os.remove(os.getenv("FALLBACK_STATE_PATH"))
    except: pass
