"""Deterministic tests for LLM fallback chain — no live calls. 순수 회전 큐 계약 검증."""
import os, json, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["FALLBACK_STATE_PATH"] = tempfile.mktemp(prefix="fallback_test_")
import writer as w

w.FALLBACK_STATE_PATH = Path(os.getenv("FALLBACK_STATE_PATH"))


class _Delta:
    def __init__(self, content=None):
        self.content = content

class _Choice:
    def __init__(self, delta, finish=None):
        self.delta = delta
        self.finish_reason = finish

class _Chunk:
    def __init__(self, delta, finish=None):
        self.choices = [_Choice(delta, finish)]

class FakeClient:
    def __init__(self, behavior):
        self.behavior = behavior
        self.calls = []

    def _create(self, **kw):
        self.calls.append(kw["model"])
        b = self.behavior() if callable(self.behavior) else self.behavior
        if isinstance(b, Exception):
            raise b
        return iter([_Chunk(_Delta(b), "stop")])

    @property
    def chat(self):
        outer = self
        class _Chat:
            completions = type("C", (), {"create": staticmethod(lambda **kw: outer._create(**kw))})()
        return _Chat()


def valid_body():
    return ("# 유효 본문입니다. " * 40 + "\n[PERSONA_CTA]\n[RELATED_POSTS]\n").ljust(850, "x")


def setup(models_behavior):
    models = [{"provider": f"p{i}", "model": f"m{i}", "timeout": 5, "note": f"t{i}"}
              for i in range(len(models_behavior))]
    clients = {f"p{i}": b if isinstance(b, FakeClient) else FakeClient(b)
               for i, b in enumerate(models_behavior)}
    orig = (w.FALLBACK_MODELS, w._clients, w.FALLBACK_STATE_PATH)
    w.FALLBACK_MODELS = models
    w._clients = clients
    w.FALLBACK_STATE_PATH = Path(tempfile.mktemp(prefix="fallback_test_"))
    return orig


def restore(orig):
    w.FALLBACK_MODELS, w._clients, w.FALLBACK_STATE_PATH = orig


def svc():
    return {"service_id": "T", "title": "테스트", "category": "general",
            "persona": "", "persona_hint": "{}"}


def test_success_becomes_front():
    orig = setup([valid_body(), valid_body()])
    r = w.generate_article(svc())
    assert r and r["model"] == "m0"
    st = w._load_state()
    assert st["front"] == "p0/m0", st
    assert st["queue"][0] == "p0/m0", st
    # 새 프로세스 흉내: 재로드해도 m0 최우선
    assert w._tier_id(w._ordered_tiers(st)[0]) == "p0/m0"
    restore(orig)
    print("✓ success_becomes_front")


def test_any_failure_rotates_to_back():
    class QuotaErr(Exception):
        def __init__(self):
            self.response = type("R", (), {"status_code": 429})()
    orig = setup([QuotaErr(), valid_body()])
    r = w.generate_article(svc())
    assert r and r["model"] == "m1", r
    st = w._load_state()
    # 실패 티어는 맨뒤로, 제외 아님. 성공 티어가 front.
    assert st["queue"][-1] == "p0/m0", st
    assert st["front"] == "p1/m1", st
    assert "quota_until" not in st and "structural_until" not in st, st
    restore(orig)
    print("✓ any_failure_rotates_to_back")


def test_uniform_rotation_each_tier_once():
    class FailErr(Exception):
        pass
    c0, c1 = FakeClient(FailErr()), FakeClient(valid_body())
    orig = setup([c0, c1])
    # setup wraps non-Fake into FakeClient; reach in via w._clients
    r = w.generate_article(svc())
    assert r and r["model"] == "m1"
    assert w._clients["p0"].calls == ["m0"], w._clients["p0"].calls
    assert w._clients["p1"].calls == ["m1"], w._clients["p1"].calls
    restore(orig)
    print("✓ uniform_rotation_each_tier_once")


def test_paid_pinned_last():
    orig = setup([valid_body(), valid_body()])
    # 두 번째 모델을 유료로 위장
    w.PAID_TIER_IDS.add("p1/m1")
    try:
        st = w._load_state()
        ordered = w._ordered_tiers(st)
        assert w._tier_id(ordered[-1]) == "p1/m1", [w._tier_id(c) for c in ordered]
        # front가 유료여도 맨뒤 유지
        st["front"] = "p1/m1"
        ordered = w._ordered_tiers(st)
        assert w._tier_id(ordered[-1]) == "p1/m1", [w._tier_id(c) for c in ordered]
    finally:
        w.PAID_TIER_IDS.discard("p1/m1")
        restore(orig)
    print("✓ paid_pinned_last")


def test_timeout_and_404_rotate_immediately():
    from unittest.mock import Mock
    import openai
    assert w._classify_error(openai.APITimeoutError(request=Mock())) == "timeout"
    e404 = Exception("nf")
    e404.response = type("R", (), {"status_code": 404})()
    assert w._classify_error(e404) == "notfound"
    orig = setup([openai.APITimeoutError(request=Mock()), valid_body()])
    r = w.generate_article(svc())
    assert r and r["model"] == "m1"
    assert w._clients["p0"].calls == ["m0"], "타임아웃 동일티어 재시도 금지"
    restore(orig)
    print("✓ timeout_and_404_rotate_immediately")


def test_state_survives_new_process():
    orig = setup([valid_body()])
    w._save_state({"front": "p0/m0", "queue": ["p0/m0"]})
    st2 = w._load_state()
    assert st2["front"] == "p0/m0" and st2["queue"] == ["p0/m0"]
    restore(orig)
    print("✓ state_survives")


def test_file_notfound_is_invalid_content():
    e = FileNotFoundError("persona-stats.json missing")
    assert w._classify_error(e) == "invalid_content"
    e2 = OSError(2, "No such file or directory")
    assert w._classify_error(e2) == "invalid_content"
    assert w._classify_error(w._ValidationError("PERSONA_CTA 누락")) == "invalid_content"
    print("✓ invalid_content_gate")


def test_full_pass_failure_touches_every_tier():
    class FailErr(Exception):
        pass
    orig = setup([FailErr(), FailErr()])
    r = w.generate_article(svc())
    assert r is None, "전부 실패 시 None"
    assert w._clients["p0"].calls == ["m0"], "제외 없이 전 티어 시도"
    assert w._clients["p1"].calls == ["m1"], "제외 없이 전 티어 시도"
    restore(orig)
    print("✓ full_pass_failure_touches_every_tier")


if __name__ == "__main__":
    for fn in [test_success_becomes_front, test_any_failure_rotates_to_back,
               test_uniform_rotation_each_tier_once, test_paid_pinned_last,
               test_timeout_and_404_rotate_immediately, test_state_survives_new_process,
               test_file_notfound_is_invalid_content, test_full_pass_failure_touches_every_tier]:
        fn()
    print("all 8 deterministic tests pass")
    try:
        os.remove(os.getenv("FALLBACK_STATE_PATH"))
    except Exception:
        pass
