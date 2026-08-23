# scripts/auto-writer/test_fallback_chain.py
"""폴백 체인 결정론적 테스트 — 라이브 API 호출 없음.
스킬(llm-fallback-chain-management) 검증 항목:
  1. 성공 티어가 다음 요청에서 최우선 정렬
  2. 타임아웃 → 동일 티어 재시도 없이 즉시 다음 티어
  3. 429 → 실패 티어만 쿨다운 (글로벌 서킷브레이커 없음)
  4. 성공 시 해당 티어 쿨다운 해제
  5. 상태가 파일로 지속 (새 프로세스에서 생존)
  6. 전체 쿨다운 시 최조 만료 티어만 1회 시도
  7. 무효 콘텐츠(마커 누락)는 반환되지 않음

실행: python3 test_fallback_chain.py
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import writer


# ── 페이크 스트리밍 인프라 ──────────────────────────────────
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
    """behavior: 'ok' | Exception 인스턴스 | callable(model)->str"""
    def __init__(self, behavior):
        self.behavior = behavior
        self.calls = []

    def _create(self, **kw):
        model = kw["model"]
        self.calls.append(model)
        b = self.behavior
        if isinstance(b, Exception):
            raise b
        if callable(b):
            b = b(model)
        body = b if isinstance(b, str) else "본문"
        return iter([_Chunk(_Delta(body), "stop")])

    @property
    def chat(self):
        outer = self
        class _Chat:
            completions = type("C", (), {"create": staticmethod(lambda **kw: outer._create(**kw))})()
        return _Chat()


def valid_body():
    m = "유효 본문입니다. "
    return ("#" + m * 40 + "\n[PERSONA_CTA]\n[RELATED_POSTS]\n").ljust(850, "x")


def setup_chain(tmpdir, behaviors):
    """FALLBACK_MODELS를 behaviors 순서대로 재구성하고 모듈 상태 교체."""
    models = [{"provider": f"p{i}", "model": f"m{i}", "timeout": 5,
               "max_retries": cfg.get("retries", 2), "note": f"t{i}"}
              for i, cfg in enumerate(behaviors)]
    clients = {}
    for i, cfg in enumerate(behaviors):
        c = cfg["client"]
        clients[f"p{i}"] = c if isinstance(c, FakeClient) else FakeClient(c)
    state_path = Path(tmpdir) / "fallback_state.json"
    orig = (writer.FALLBACK_MODELS, writer._clients, writer.FALLBACK_STATE_PATH)
    writer.FALLBACK_MODELS = models
    writer._clients = clients
    writer.FALLBACK_STATE_PATH = state_path
    return models, clients, state_path, orig


def restore(orig):
    writer.FALLBACK_MODELS, writer._clients, writer.FALLBACK_STATE_PATH = orig


def service():
    return {"service_id": "T", "title": "테스트", "category": "general",
            "persona": "", "persona_hint": "{}"}


def main():
    results = []
    tmpdir = tempfile.mkdtemp()

    # ── 1+5. 성공 → last_success_tier 저장, 다음 체인에서 최우선 ──
    _, clients, spath, orig = setup_chain(tempfile.mkdtemp(), [
        {"client": FakeClient(valid_body())},
        {"client": FakeClient(valid_body())},
    ])
    r = writer.generate_article(service())
    assert r and r["model"] == "m0", "test1: m0 성공해야 함"
    st = json.loads(spath.read_text())
    assert st["last_success_tier"] == "p0/m0", "test1: last_success_tier 기록"
    # 새 "프로세스" 흉내: 상태를 디스크에서 다시 로드해 정렬 확인
    st2 = writer._load_state()
    usable = writer._usable_tiers(st2)
    assert writer._tier_id(usable[0]) == "p0/m0", "test5: 재시작 후에도 m0 최우선"
    restore(orig); results.append("1,5 ✅ 성공티어 우선+상태 지속")

    # ── 2. 타임아웃 → 동일 티어 재시도 없이 즉시 다음 티어 ──
    _, clients, _, orig = setup_chain(tempfile.mkdtemp(), [
        {"client": writer.APITimeoutError("t/o"), "retries": 3},
        {"client": valid_body()},
    ])
    r = writer.generate_article(service())
    assert r and r["model"] == "m1", "test2: 타임아웃 후 m1 성공"
    assert clients["p0"].calls.count("m0") == 1, \
        f"test2: m0 재시도 없어야 함(1회), 실제={clients['p0'].calls}"
    restore(orig); results.append("2 ✅ 타임아웃 즉시 로테이션")

    # ── 3. 429 → 실패 티어만 쿨다운, 다음 실행에서 스킵 ──
    class QuotaErr(Exception):
        def __init__(self):
            self.response = type("R", (), {"status_code": 429})()
    _, clients, spath, orig = setup_chain(tempfile.mkdtemp(), [
        {"client": QuotaErr(), "retries": 3},
        {"client": valid_body()},
    ])
    r = writer.generate_article(service())
    assert r and r["model"] == "m1", "test3: 429 후 m1 성공"
    assert clients["p0"].calls.count("m0") == 1, "test3: 429 동일티어 재시도 금지"
    st = json.loads(spath.read_text())
    assert "p0/m0" in st["quota_until"], "test3: quota_until 기록"
    assert len(st["quota_until"]) == 1, "test3: 실패 티어만 쿨다운"
    # 다음 실행: p0 쿨다운 중 → 바로 m1 사용
    r2 = writer.generate_article(service())
    assert r2["model"] == "m1" and clients["p0"].calls.count("m0") == 1, \
        "test3: 쿨다운 티어 스킵 확인"
    restore(orig); results.append("3 ✅ 429 티어전용 쿨다운")

    # ── 4+6. 전체 쿨다운 → 최조 만료 티어 1회, 성공 시 쿨다운 해제 ──
    _, clients, spath, orig = setup_chain(tempfile.mkdtemp(), [
        {"client": valid_body()}, {"client": valid_body()},
    ])
    now = time.time()
    spath.write_text(json.dumps({
        "last_success_tier": None,
        "quota_until":      {"p0/m0": now + 100},
        "structural_until": {"p1/m1": now + 50},   # p1이 더 먼저 만료
    }))
    r = writer.generate_article(service())
    assert r and r["model"] == "m1", "test6: 최조 만료(p1)만 선택"
    assert clients["p1"].calls == ["m1"] and not clients["p0"].calls, "test6: p0 미시도"
    st = json.loads(spath.read_text())
    assert "p1/m1" not in st.get("structural_until", {}), "test4: 성공 시 쿨다운 해제"
    assert st["last_success_tier"] == "p1/m1", "test4: last_success 갱신"
    restore(orig); results.append("4,6 ✅ 쿨다운 해제+최조만료 선택")

    # ── 7. 마커 누락(무효 콘텐츠)은 절대 반환 안 됨 ──
    bad = "짧은 마커없는 본문"
    _, clients, _, orig = setup_chain(tempfile.mkdtemp(), [
        {"client": bad},
        {"client": valid_body()},
    ])
    r = writer.generate_article(service())
    assert r and "[PERSONA_CTA]" in r["body"], "test7: 무효 콘텐츠 반환 금지"
    assert r["model"] == "m1", "test7: 무효 후 다음 티어 사용"
    restore(orig); results.append("7 ✅ 무효콘텐츠 게이트")

    print("\n=== 폴백 체인 테스트 결과 ===")
    for line in results:
        print(" ", line)
    print(f"{len(results)}개 그룹 전원 통과")


if __name__ == "__main__":
    main()
