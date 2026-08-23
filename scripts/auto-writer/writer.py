# scripts/auto-writer/writer.py
import os, sys, json, re, time, yaml
from pathlib import Path
from openai import OpenAI, APITimeoutError
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import paths

load_dotenv(paths.DOTENV_PATH)
load_dotenv(paths.COMMON_ENV_PATH)

# ── LLM 폴백 체인 (프로바이더별) ─────────────────────────────
# 무료 모델 우선, 유료(DeepSeek) 최후 예약.
# 모델명은 2026-08-11 실제 API 목록 검증 기준 (스킬 문서와 다를 수 있음).

PROVIDERS = {
    "nvidia": {
        "api_key_env": "NVIDIA_API_KEY",
        "base_url":    "https://integrate.api.nvidia.com/v1",
    },
    "deepseek": {
        "api_key_env": "DEEPSEEK_API_TOKEN",
        "base_url":    "https://api.deepseek.com/v1",
    },
    "google": {
        "api_key_env": "GOOGLE_API_KEY",
        "base_url":    "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "groq": {
        "api_key_env": "GROQ_API_KEY",
        "base_url":    "https://api.groq.com/openai/v1",
    },
    "cerebras": {
        "api_key_env": "CEREBRAS_API_KEY",
        "base_url":    "https://api.cerebras.ai/v1",
    },
}

def _make_client(provider: str):
    key = os.getenv(PROVIDERS[provider]["api_key_env"])
    if not key:
        return None
    return OpenAI(
        api_key=key,
        base_url=PROVIDERS[provider]["base_url"],
    )

# 프로바이더별 클라이언트 (키 없으면 None → 해당 모델 스킵)
_clients = {p: _make_client(p) for p in PROVIDERS}
NIM_API_KEY       = os.getenv("NVIDIA_API_KEY")
DEEPSEEK_API_KEY  = os.getenv("DEEPSEEK_API_TOKEN") or os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL    = "deepseek-chat"  # legacy reference (proofread 등에서 사용)

# diffusiongemma 메인 + 무료 폴백 체인, deepseek-v4-flash 최후 폴백
FALLBACK_MODELS = [
    {
        "provider":    "nvidia",
        "model":       "google/diffusiongemma-26b-a4b-it",
        "timeout":     120,
        "max_retries": 2,
        "note":        "메인 (실험모델)",
    },
    {
        "provider":    "nvidia",
        "model":       "google/gemma-4-31b-it",
        "timeout":     120,
        "max_retries": 1,
        "note":        "gemma-4 폴백",
    },
    {
        "provider":    "nvidia",
        "model":       "google/gemma-3n-e4b-it",
        "timeout":     90,
        "max_retries": 1,
        "note":        "gemma-3n 폴백",
    },
    {
        "provider":    "google",
        "model":       "gemini-3.1-flash-lite",
        "timeout":     90,
        "max_retries": 1,
        "note":        "Gemini 무료 (품질 우수)",
    },
    {
        "provider":    "google",
        "model":       "gemini-2.5-flash",
        "timeout":     90,
        "max_retries": 1,
        "note":        "Gemini 무료 (균형)",
    },
    {
        "provider":    "cerebras",
        "model":       "gemma-4-31b",
        "timeout":     90,
        "max_retries": 1,
        "note":        "Cerebras 무료 (빠른 추론)",
    },
    {
        "provider":    "groq",
        "model":       "llama-3.3-70b-versatile",
        "timeout":     60,
        "max_retries": 1,
        "note":        "Groq 무료 (대형 컨텍스트)",
    },
    {
        "provider":    "groq",
        "model":       "qwen/qwen3.6-27b",
        "timeout":     60,
        "max_retries": 1,
        "note":        "Groq 무료 (thinking 태그 제거 필요)",
        "strip_thinking": True,
    },
    {
        "provider":    "groq",
        "model":       "openai/gpt-oss-120b",
        "timeout":     90,
        "max_retries": 1,
        "note":        "Groq 무료 (오픈 가중치)",
    },
    {
        "provider":    "groq",
        "model":       "openai/gpt-oss-20b",
        "timeout":     60,
        "max_retries": 1,
        "note":        "Groq 무료 (소형·고속)",
    },
    {
        "provider":    "deepseek",
        "model":       "deepseek-v4-flash",
        "timeout":     180,
        "max_retries": 2,
        "note":        "deepseek v4 flash 최후 폴백 (유료)",
    },
]

client = _clients["nvidia"]
deepseek_client = _clients["deepseek"]

# ── 페르소나 통계 로더 ─────────────────────────────────────
from shared.persona_stats import resolve_keys as _resolve_stat_keys, get_stats as _get_stats, format_for_prompt as _fmt_stats, make_fomo_hook as _make_hook

# ── 시스템 프롬프트 (2026-06-23 v3: 품질 강화 + 퍼널 유지) ──
SYSTEM_PROMPT = """
# 역할

당신은 persona.aikorea24.kr의 금융 콘텐츠 에디터입니다.
사이트 독자는 20~40대 한국 직장인으로, 보험·투자·대출·세금·정부지원금에 관한
실생활 금융 정보를 실용적으로 얻고자 합니다.
당신의 임무는 수동으로 정성껏 작성된 글과 동일한 수준의 품질을 자동으로 구현하는 것입니다.

---

# 데이터 활용 기준 (사전 리서치)

User 메시지로 제공된 데이터를 기준으로 글을 작성하세요.

1. **제공된 데이터에서 날짜가 명시된 정보만** 사용합니다. 날짜 불명 정보는 사용하지 않습니다.
2. 모든 수치에는 반드시 기준 시점(YYYY년 MM월 기준)과 출처를 명시합니다.
3. 제공된 데이터의 기준 시점이 현재({datetime.now().year}년 {datetime.now().month}월)와 1년 이상 차이날 경우, 도입부 직후 ⚠️ 블록으로 독자에게 알립니다.
4. User 메시지 외부의 정보를 임의로 생성하거나 추측하지 마세요.

---

# 페르소나-수혜 대상 일치 검증 (글쓰기 전 필수)

글을 작성하기 전, 아래 질문에 반드시 답하세요.

**Q**: "이 사업/제도의 실제 수혜 대상이 제목에 들어갈 독자(페르소나)와 실질적으로 일치하는가?"

**판단 기준**:
- ✅ 통과: 페르소나가 직접 신청하거나 혜택을 받을 수 있는 경우
- ❌ 실패: 페르소나가 본문을 읽은 후 "나는 해당 없다"는 결론에 도달하는 경우

**❌ 실패 시 처리 (둘 중 하나 선택)**:
- 선택 A: 제목을 실제 수혜 대상에 맞게 변경
- 선택 B: 해당 페르소나에게 실질적으로 유용한 대안 정보를 본문에 충분히 담고,
  도입부에 "직접 해당되지 않더라도 알아두면 좋은" 맥락을 명시

---

# 글 구조 및 작성 기준

아래 ①~⑨는 포함해야 할 내용 요소이며, **반드시 이 순서를 따라야 하는 템플릿이 아닙니다.**
주제와 카테고리에 맞게 흐름을 유연하게 구성하세요.
- 예: 보험·지원금 글은 `조건→금액→신청방법` 순서가 자연스럽고, 투자 글은 `개념→비교→전략` 순서가 적합합니다.
- 모든 글에 ⑧ FAQ와 ⑨ 마무리는 필수입니다.
- **두 글 이상 연달아 읽었을 때 같은 템플릿처럼 느껴지지 않도록** 각 주제에 맞게 섹션 순서와 비중을 조정하세요.

## ① 제목
- 첫 줄은 `# {제목}` 형식 (h1 마크다운)
- 독자의 구체적인 상황을 반영합니다. (예: "만 34세 직장인, 슈퍼 ISA 청년형 막차 타는 법")
- 연도 또는 기준 시점을 포함합니다.
- 반드시 자연스러운 어미를 사용합니다. "총정리", "완벽정리", "한눈에", "필독" 등 흔한 마무리는 사용하지 마세요.
- 대신 행동 유도형("받는 법", "신청 방법"), 결과형("받을 수 있습니다", "아낄 수 있는 법"), 질문형 또는 검색 의도에 맞는 구체적 표현을 사용하세요.

## ② 도입부 (150~250자)
아래 3가지를 반드시 포함합니다.

- 독자가 실제로 겪는 고민이나 상황을 한 문장으로 짚기
- 이 글을 읽으면 알 수 있는 것 2~3가지를 명시
- ⚠️ 정보 기준 시점이 있다면 도입부 직후 경고 블록으로 표시

나쁜 도입부 예시 (이렇게 쓰지 말 것):
"국민성장펀드는 중요한 상품입니다. 장기 투자를 고려해야 합니다."

좋은 도입부 예시 (이렇게 쓸 것):
"슈퍼 ISA가 하반기에 출시된다는 건 알겠는데, 청년형과 국민성장형 중 어떤 걸 선택해야 할지 막막하신 분들을 위해 이 글을 씁니다. 가입 조건, 세제 혜택, 중복 가입 전략까지 한번에 비교합니다."

## ③ 핵심 개념 설명
- 초보자가 이해할 수 있는 언어로 설명합니다.
- 전문 용어는 반드시 괄호 안에 쉬운 말로 병기합니다.
- **"유리합니다", "좋습니다", "중요합니다"로만 끝나는 문장 금지.**
  → 반드시 "연 OO만원 절세", "수익률 OO% 차이" 처럼 구체적인 수치로 뒷받침합니다.

## ④ 비교표 (선택 항목이 2개 이상일 때 필수)
- 행: 비교 대상 상품/제도
- 열: 독자 관점에서 실제로 의미 있는 기준 (수익/세제혜택/조건/위험도/유동성 등)
- 표 아래에 "어떤 상황에 어떤 걸 선택해야 하는지" 1~2줄 해설 필수
- 표 아래 출처 각주: * {기관명} {YYYY년 MM월} 기준
- 표 직전에 1~2문장 설명 텍스트 필수

## ⑤ 조건 및 자격 요건
- 신청 자격, 소득 기준, 나이 조건, 한도를 표로 정리합니다.
- "조건 불충족 시 대안"도 함께 제시합니다.
- 출처와 기준 시점을 반드시 명시합니다. (예: "{datetime.now().year}년 {datetime.now().month}월 기준, 국세청")

## ⑥ 소득 구간별 또는 상황별 선택 가이드
아래 형식을 참고하여 독자 유형을 2~3가지로 분류하고 각각에게 맞는 전략을 제시합니다.

좋은 예시:
"연 소득 2,400~3,600만원 구간 청년 → 청년도약계좌 우선, 이유: 정부 매칭 효과로 타 상품 대비 실질 수익률이 가장 높음"
"연 소득 5,000만원 이상 → 청년재형적금, 이유: 비과세 혜택의 절세 가치가 소득세율에 비례해서 가장 높아짐"

나쁜 예시:
"본인의 상황에 맞는 상품을 선택하는 것이 중요합니다."

## ⑦ 주의사항 및 리스크 (생략 금지)
- 중도 해지 시 불이익을 구체적인 수치로 명시합니다.
- 조건 충족이 어려운 경우를 솔직하게 서술합니다.
- 아직 미확정된 내용은 반드시 "⚠️ OO 예정, 확정 후 업데이트 필요" 표시를 합니다.

## ⑧ FAQ (4개 이상)
- 독자가 실제로 가장 많이 묻는 질문 중심으로 구성합니다.
- 각 답변은 최소 3문장 이상, 수치나 실제 사례 포함 필수입니다.
- **"다를 수 있습니다", "전문가에게 문의하세요"로만 끝나는 답변 금지.**
- **독자가 FAQ를 읽고 추가로 궁금해할 만한 후속 질문을 미리 차단**해야 합니다. 예: "직장 다니면서 병원 다닐 수 있나요?", "아이한테 전염되나요?" 같은 실질적 궁금증을 답변에 포함하세요.
- 제목은 `## 자주 묻는 질문 (Q&A)` 형식, 각 질문은 `**Q1. ...**` `A1. ...` 형식

## ⑨ 마무리
- 글 전체 핵심을 2~3문장으로 요약합니다.
- 독자가 오늘 당장 취할 수 있는 행동 1가지를 제시합니다.
- 세법 개정 등 업데이트가 예정된 경우 "이 글에서 계속 보완할 예정입니다" 한 줄 추가합니다.

---

# 퍼널 마커 (필수 포함)

글 본문에 아래 2개의 플레이스홀더를 반드시 포함하세요. 이 마커들은 사이트에서 자동으로 실제 링크로 교체됩니다.

- `[PERSONA_CTA]` — 글末尾(FAQ와 마무리 사이)에 단독 줄로 삽입. "내 페르소나 통계 보기" CTA 블록으로 자동 교체됨.
- `[RELATED_POSTS]` — 마무리 직전에 단독 줄로 삽입. 관련 블로그 글 링크로 자동 교체됨.

**규칙**:
- 두 마커 모두 **반드시 H2 제목 밖, 단독 줄**에 위치할 것
- `## [PERSONA_CTA]` 또는 `## [RELATED_POSTS]` 형태 금지
- 마커 주변에 추가 텍스트를 붙이지 말 것

**CTA 사다리 (variant-driven)**: 본문 중간(H2#2·H2#3 뒤)에는 파이프라인이 자동으로 '약함/호기심' 복사의 인라인 CTA를 주입합니다(config/category_map.yaml의 `cta_variants` 참조 — 카테고리×페르소나 키별로 mid(약함)/end(강함) 2개 A/B 변인). 글말의 `[PERSONA_CTA]`는 '강함/행동' 복사로 자동 교체됩니다. 작성자는 복사문을 직접 쓰지 않고 **마커만 유지**하세요.

**전진 참조 티저 (forward-reference teaser)**: H2#2와 H2#3 바로 뒤에 독자를 글 끝(인라인 CTA와 본문 내 광고 슬롯이 있는 곳)으로 유도하는 한 줄 티저를 넣으세요. 예: "아래에서 소득 구간별 전략을 정리합니다 →", "글末尾에서 내 또래 평균과 비교해보세요 →". 이 티저는 중간 이탈을 줄이고 광고 노출 도달을 높입니다(광고 코드는 건드리지 않음).

---

# 어투 규칙
- 경어체: "~합니다", "~입니다" (존댓말, "~해요"체도 가능)
- 간결하고 명확한 문장, 한 문장은 2줄 이내
- 강조는 **볼드**만 사용, 이탤릭(`*기울임*`)과 취소선(`~~취소선~~`) 금지
- **이모지**: ⚠️(경고 표시) 외의 이모지(💡📌👉🎯 등)는 본문·제목·표 어디든 사용 금지
- 숫자: "165만원" 또는 "165만 원" 형식
- 마크다운 문법 정확히 준수

---

# 최종 출력 전 Self-Check (전부 통과해야 출력 가능)

아래 항목을 글 완성 후 반드시 점검하세요.
하나라도 실패하면 해당 부분을 수정한 뒤 출력합니다.

| 점검 항목 | 통과 기준 |
|---|---|
| 미완성 플레이스홀더 | `[OO]`, `example.com` 등이 0개 (`[PERSONA_CTA]`, `[RELATED_POSTS]`는 예외 — 필수 마커) |
| 수치 근거 | 모든 수치에 출처 기관명 또는 "YYYY년 MM월 기준" 명시 |
| 두루뭉술 표현 | "유리합니다", "중요합니다"만으로 끝나는 문장 0개 |
| 비교 관점 | 독자 상황별로 "무엇을 선택할지" 명확한 기준 제시 여부 |
| 주의사항 | 중도 해지, 조건 미충족 리스크를 수치로 명시 여부 |
| 미확정 정보 | ⚠️ 경고 블록으로 별도 표시 여부 |
| 글자 수 | 본문 기준 최소 1,500자 이상 |
| 퍼널 마커 | `[PERSONA_CTA]`와 `[RELATED_POSTS]`가 본문에 존재, H2 밖 단독 줄 |
| 맞춤법·문법 | 조사("이/가, 을/를, 은/는") 오류 0건, 오탈자 0건 |
| 노출 마크다운 | `*기울임*`, `~~취소선~~` 등 렌더링 시 기호가 노출될 문법 0건 |
| 테이블 구조 1 | 헤더 행과 구분선(|---|)이 각각 독립된 줄에 있음 |
| 테이블 구조 2 | 모든 행의 `|` 개수가 헤더 행과 동일함 |
| 테이블 구조 3 | 구분선(|---|)이 헤더 바로 다음 줄에 위치함 |
| 페르소나-대상 일치 | 제목의 페르소나가 실제 수혜 대상과 일치하거나, 불일치 시 대안 정보가 도입부에 명시됨 |

---

# 절대 금지 사항

- "장기적인 관점에서 중요합니다" 같은 **내용 없는 문장으로 분량 채우기**
- 근거 없는 수치 사용 (예: "최대 40% 절세" — 어떤 세율 기준인지 명시 없이 사용 금지)
- 상품의 장점만 나열하고 **단점·리스크·조건 불충족 케이스를 생략**하는 것
- 미확정 정보를 확정된 것처럼 서술하는 것
- FAQ 답변을 "관련 기관에 문의하세요"로만 마무리하는 것
- 상품코드, 서비스 ID, API 응답 원문 노출
- "본 상품은~", "당사에서는~" 같은 공급자 어투
- 근거 없는 수익률 예측
- `[PERSONA_CTA]`와 `[RELATED_POSTS]`를 H2 제목 안에 포함

---

# 입력 형식

아래 정보가 User 메시지로 제공됩니다. 위 기준에 따라 글을 작성하세요.

- **타겟 독자 라벨** (예: "무주택 직장인", "맞벌이 신혼부부")
- **서비스명 / 주제**
- **카테고리** (loan / insurance / invest / tax / general)
- **페르소나 통계** (참고: 같은 조건 한국인 데이터)
- **원본 데이터** (지원 조건, 대상, 상세 내용, 신청 방법 등)
- **persona_cta_url** (CTA 링크 — `[PERSONA_CTA]` 마커에 자동 적용됨)

User 메시지에 포함된 `[PERSONA_CTA]`와 `[RELATED_POSTS]` 표시를 반드시 출력에 포함하세요.
"""

def _strip_thinking(text: str) -> str:
    """DeepSeek R1 계열 thinking 태그 제거 (V4에서도 혹시 모를 경우 대비)"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def _resolve_product_type(service_id: str) -> str:
    """FINLIFE_정기예금_... → 정기예금"""
    if service_id.startswith("FINLIFE_"):
        rest = service_id[len("FINLIFE_"):]
        parts = rest.split("_", 1)
        return parts[0] if parts else "deposit"
    return "deposit"

def _resolve_persona_label(record: dict, labels: dict, product_type: str = "") -> str:
    """persona_labels 설정에서 독자 페르소나 라벨 해석"""
    source = record.get("source", "gov24")
    category = record.get("category", "general")

    if source == "finlife":
        pt = product_type or _resolve_product_type(record.get("service_id", ""))
        finlife_map = labels.get("finlife", {})
        return finlife_map.get(pt, "금융 상품 이용자")

    if source == "datagokr":
        return labels.get("invest", "ETF·지수 투자 입문자")

    cat_label = labels.get(category)
    if isinstance(cat_label, str):
        return cat_label
    if isinstance(cat_label, dict):
        db_persona = record.get("persona")
        if db_persona and db_persona in cat_label:
            return cat_label[db_persona]
        return cat_label.get("default", "30대 직장인")
    return "30대 직장인"

def build_user_prompt(service: dict) -> str:
    config_path = os.path.join(os.path.dirname(__file__), "config/category_map.yaml")
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    source = service.get("source", "gov24")
    category = service.get("category", "general")
    labels = config.get("persona_labels", {})
    product_type = _resolve_product_type(service.get("service_id", ""))
    persona_label = _resolve_persona_label(service, labels, product_type)

    cta_url = config["persona_cta"].get(
        service.get("persona", "general"),
        "/persona/전국-전체-전연령/"
    )

    # 통계 데이터 로드 (모든 source 공통)
    stat_keys = _resolve_stat_keys(service)
    stats_raw = _get_stats(stat_keys)
    stats_text = _fmt_stats(stats_raw)
    fomo_hook = _make_hook(stats_raw)

    if source == "gov24":
        hint = json.loads(service.get("persona_hint", "{}"))
        hint_str = ", ".join(f"{k}: {v}" for k, v in hint.items()) if hint else persona_label

        stats_block = f"\n[참고: 페르소나 통계]\n{stats_text}\n" if stats_text else ""
        fomo_block = f"\n[FOMO 훅 예시]\n{fomo_hook}\n" if fomo_hook else ""

        return f"""
{persona_label} 독자 관점의 정부 지원금 안내 아티클을 작성해 주세요.
{stats_block}{fomo_block}
서비스명: {service.get('title', '')}
카테고리: {category}
페르소나: {service.get('persona', '')}
페르소나 힌트: {hint_str}
서비스 분야: {service.get('field', '')}
서비스 목적: {service.get('summary', '')}
지원 대상: {service.get('target', '')}
지원 내용: {service.get('detail', '')}
신청 방법: {service.get('apply_method', '')}
전화 문의: {service.get('contact', '')}
소관 기관: {service.get('org_name', '')}
상세 URL: {service.get('detail_url', '')}
persona_cta_url: {cta_url}

위 정보로 SYSTEM PROMPT의 글 구조를 정확히 따라 작성하세요.
[PERSONA_CTA]와 [RELATED_POSTS] 플레이스홀더를 반드시 포함하세요.
"""
    elif source == "finlife":
        stats_block = f"\n[참고: 페르소나 통계]\n{stats_text}\n" if stats_text else ""
        return f"""
{persona_label} 독자 관점의 금리 비교 아티클을 작성해 주세요.
{stats_block}
상품 유형: {product_type}
금융사: {service.get('org_name', '')}
상품 정보: {service.get('detail', '')}
대상: {service.get('target', '')}
persona_cta_url: {cta_url}

위 금융 상품 데이터를 바탕으로 SYSTEM PROMPT의 글 구조를 정확히 따라 작성하세요.
[PERSONA_CTA]와 [RELATED_POSTS] 플레이스홀더를 반드시 포함하세요.
"""
    elif source == "datagokr":
        stats_block = f"\n[참고: 페르소나 통계]\n{stats_text}\n" if stats_text else ""
        return f"""
{persona_label} 독자 관점의 지수·투자 해설 아티클을 작성해 주세요.
{stats_block}
지수명: {service.get('org_name', '')}
데이터: {service.get('detail', '')}
대상: {service.get('target', '')}
persona_cta_url: {cta_url}

위 지수 데이터를 바탕으로 SYSTEM PROMPT의 글 구조를 정확히 따라 작성하세요.
[PERSONA_CTA]와 [RELATED_POSTS] 플레이스홀더를 반드시 포함하세요.
"""
    elif source == "income_series":
        stats_block = f"\n[참고: 페르소나 통계]\n{stats_text}\n" if stats_text else ""
        fomo_block = f"\n[FOMO 훅 예시]\n{fomo_hook}\n" if fomo_hook else ""
        # 안전한 통계 참조값
        ref_key = stat_keys[0].replace("_", " ") if stat_keys else "직장인"
        ref_inc = 0
        if stat_keys and stat_keys[0] in stats_raw:
            ref_inc = stats_raw[stat_keys[0]].get("income_est", 0)
        return f"""
다음 통계 데이터를 바탕으로 '내 또래 연봉' 비교 아티클을 작성해 주세요.

이 글의 목적: "나는 또래보다 얼마나 버나?" 독자의 궁금증을 해소
핵심 문장: "{ref_key}의 평균 월 소득은 {ref_inc}만원입니다"
{stats_block}{fomo_block}
지역: {service.get('org_name', '')}
대상 독자: {service.get('target', '')}
persona_cta_url: {cta_url}

## 작성 지침
- 첫 문단: "내 또래는 평균 얼마나 벌까?" 라는 독자의 궁금증으로 시작
- 두 번째 문단: 구체적인 통계 수치 제시 ("서울 35세 남성의 월 평균은 **404만원**입니다")
- 본문 구조 (H2):
  1. H2: {service.get('org_name', '')} {service.get('persona', '')} 평균 소득은?
  2. H2: 성별·연령별 소득 차이
  3. H2: 주거 형태와 생활비
  4. H2: 나는 어디쯤일까? (내 소득 비교 유도)
  5. H2: 자주 묻는 질문
- 도입부 '내 또래' 통계 2개 이상 포함
- 말미에 "지금 내 연봉이 평균보다 높은지 낮은지 확인해 보세요" 식의 CTA
[PERSONA_CTA]와 [RELATED_POSTS] 플레이스홀더를 반드시 포함하세요.
"""
    else:
        stats_block = f"\n[참고: 페르소나 통계]\n{stats_text}\n" if stats_text else ""
        return f"""
{stats_block}
서비스명: {service.get('title', '')}
카테고리: {category}
지원 대상: {service.get('target', '')}
지원 내용: {service.get('detail', '')}
신청 방법: {service.get('apply_method', '')}
persona_cta_url: {cta_url}

SYSTEM PROMPT의 글 구조를 정확히 따라 작성하세요.
[PERSONA_CTA]와 [RELATED_POSTS] 플레이스홀더를 반드시 포함하세요.
"""

PROOFREADER_PROMPT = """
다음 글을 교정하세요. 아래 규칙만 적용합니다.

수정 대상:
1. 맞춤법·문법 오류 (예: "성장하는을" → "성장을")
2. 조사 오류: 받침 있으면 이/은/이란, 없으면 가/는/란
   예: "투자자이라면" → "투자자라면", "청년이란" → 유지(받침 O)
3. 동일 단어/조사 연속 중복 (예: "보다보다" → "보다", "의의" → "의", "방문 방문" → "방문", "을을" → "을")
4. **반드시 수정해야 할 어색한 표현** — 아래 표현이 보이면 즉시 교체:
   "사비하다" → "직접 부담하다 / 개인이 부담하다"
   "비용하다" → "비용이 발생하다 / 비용을 부담하다"
   "수혜하다" → "혜택을 받다" (예: "수혜하려면" → "혜택을 받으려면")
   "지원하다"(목적어 없이 단독, 예: "지원합니다") → "지원을 받다 / 지원을 신청하다" (이유: "지원금을 지원합니다"는 중복, "지원합니다"는 주어 불명)
5. 어색한 반복 표현 (예: "기준 기준" → "기준")

수정 금지:
- 내용, 수치, 구조, 링크, 마크다운 포맷 변경 금지
- 문체 변경 금지 (구어체 유지)

출력: 교정된 전문을 그대로 출력. 변경 사항 설명 불필요.
"""

def _postprocess_proofread(text: str) -> str:
    """LLM 교정 후 regex 기반 추가 교정 (LLM이 놓친 패턴 안전망)"""
    # 1. 어색한 조어 교체
    REPLACE_MAP = {
        '사비할': '직접 부담할', '사비하다': '직접 부담하다',
        '사비하면': '직접 부담하면', '사비하고': '직접 부담하고',
        '사비하며': '직접 부담하며', '사비해': '직접 부담해',
        '사비하여': '직접 부담하여', '사비했': '직접 부담했',
        '수혜할': '혜택을 받을', '수혜하다': '혜택을 받다',
        '수혜하면': '혜택을 받으면', '수혜하려면': '혜택을 받으려면',
        '수혜하고': '혜택을 받고', '수혜하며': '혜택을 받으며',
        '수혜해': '혜택을 받아', '수혜하여': '혜택을 받아',
        '수혜했': '혜택을 받았',
    }
    for old, new in REPLACE_MAP.items():
        text = text.replace(old, new)

    # 2. 이탤릭·취소선 마크다운 제거 (ASTRO에서 미지원시 기호 노출 방지)
    for pat, repl in [
        (r'\*출처:([^*\n]+)\*', r'출처:\1'),
        (r'\*해설:([^*\n]+)\*', r'해설:\1'),
        (r'\*참고:([^*\n]+)\*', r'참고:\1'),
    ]:
        text = re.sub(pat, repl, text)
    # 인라인 *italic* → 일반 텍스트 (줄 첫머리 리스트, **bold** 보호)
    text = re.sub(r'(?<!\*)\*(?![\s*])([^*\n]+?)\*(?!\*)', r'\1', text)
    # ~~취소선~~ → 일반 텍스트
    text = re.sub(r'~~([^~\n]+)~~', r'\1', text)

    # 3. ⚠️ 외 이모지 제거 (LLM이 SYSTEM_PROMPT를 무시한 경우 안전망)
    # 유니코드 이모지 범위: 😀~ (U+1F300~), 📊 (U+1F4CA), ✅ (U+2705) 등
    text = re.sub('[\U0001F300-\U0001FAFF\u2700-\u27BF]', '', text)
    text = re.sub(r'  +', ' ', text)

    # 4. 동일 단어 연속 중복: 보다보다, 방문 방문, 기준 기준
    text = re.sub(r'([가-힣]{2,})\1', r'\1', text)
    text = re.sub(r'([가-힣]{2,}) +\1', r'\1', text)

    # 4. 조사 중복: 의의, 을을, 이이
    text = re.sub(r'(의|을|를|이|가|은|는|에|의)\1', r'\1', text)

    return text


def proofread(text: str, timeout: int = 90) -> str:
    """gemma-3n → deepseek-chat 폴백 체인으로 맞춤법·문법 교정 + regex 후처리"""
    for attempt in _proofread_chain(text, timeout):
        if attempt is not None:
            return attempt
    return text


def _proofread_chain(text: str, timeout: int = 90):
    """proofread 폴백 제너레이터 — 각 시도 결과를 yield"""
    # 1차: NVIDIA gemma-3n
    print("  [proofread] 시도 1/2 | google/gemma-3n-e4b-it")
    try:
        resp = client.chat.completions.create(
            model="google/gemma-3n-e4b-it",
            messages=[
                {"role": "system", "content": PROOFREADER_PROMPT},
                {"role": "user",   "content": text}
            ],
            temperature=0.0,
            max_tokens=len(text) + 500,
            timeout=timeout,
            stream=False,
        )
        corrected = resp.choices[0].message.content.strip()
        corrected = _postprocess_proofread(corrected)
        print(f"  [proofread] ✅ 교정 완료 ({len(text)}→{len(corrected)}자)")
        yield corrected
        return
    except Exception as e:
        print(f"  [proofread] ⚠️ gemma-3n 교정 실패: {e}")

    # 2차: DeepSeek 폴백
    if DEEPSEEK_API_KEY:
        print("  [proofread] 시도 2/2 | deepseek-chat")
        try:
            resp = deepseek_client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": PROOFREADER_PROMPT},
                    {"role": "user",   "content": text}
                ],
                temperature=0.0,
                max_tokens=len(text) + 500,
                timeout=timeout,
                stream=False,
            )
            corrected = resp.choices[0].message.content.strip()
            corrected = _postprocess_proofread(corrected)
            print(f"  [proofread] ✅ deepseek 교정 완료 ({len(text)}→{len(corrected)}자)")
            yield corrected
            return
        except Exception as e:
            print(f"  [proofread] ⚠️ deepseek 교정 실패: {e}")

    yield None


def _classify_error(e: Exception) -> str:
    """실패 원인 분류 — 재시도 정책 차등화 (스킬 failure policy 기준)
    - server(5xx) / network → 동일 티어 1회 재시도 허용
    - quota(429) → 티어 전용 5분 쿨다운, 즉시 다음 티어
    - auth(401/403) / notfound(404) → structural 쿨다운, 즉시 다음 티어
    - timeout / invalid_content(빈 응답·마커 누락) → 재시도 없이 다음 티어
    """
    if isinstance(e, APITimeoutError) or "timeout" in type(e).__name__.lower():
        return "timeout"
    status = getattr(getattr(e, "response", None), "status_code", None)
    if status == 429:
        return "quota"
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "notfound"
    if status and status >= 500:
        return "server"
    if isinstance(e, _ValidationError):
        return "invalid_content"
    return "network"


class _ValidationError(ValueError):
    """응답 검증 실패 (빈 응답, 마커 누락, 분량 미달) — invalid_content로 분류"""


# ── 폴백 상태 (스킬: persistent rotation contract) ────────────
FALLBACK_STATE_PATH = Path(__file__).resolve().parent / "db" / "fallback_state.json"
QUOTA_COOLDOWN_SEC = 300        # 429 → 5분, 해당 티어만
STRUCTURAL_COOLDOWN_SEC = 3600  # 401/403/404 → 1시간

def _tier_id(cfg: dict) -> str:
    return f"{cfg['provider']}/{cfg['model']}"

def _load_state() -> dict:
    """상태 로드 + 만료된 쿨다운 제거. 파일 없음/손상 = 빈 상태."""
    st = {}
    try:
        st = json.loads(FALLBACK_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    now = time.time()
    for k in ("quota_until", "structural_until"):
        st[k] = {t: v for t, v in (st.get(k) or {}).items() if v > now}
    st.setdefault("last_success_tier", None)
    return st

def _save_state(st: dict):
    """임시 파일 쓰기 후 원자적 교체."""
    FALLBACK_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = FALLBACK_STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, FALLBACK_STATE_PATH)

def _usable_tiers(st: dict) -> list:
    """쿨다운 중이 아닌 사용 가능 티어. last_success_tier 최우선 정렬."""
    now = time.time()
    usable = [c for c in FALLBACK_MODELS
              if _clients.get(c["provider"])
              and st["quota_until"].get(_tier_id(c), 0) <= now
              and st["structural_until"].get(_tier_id(c), 0) <= now]
    usable.sort(key=lambda c: 0 if _tier_id(c) == st["last_success_tier"] else 1)
    return usable


def generate_article(service: dict) -> dict | None:
    if not any(_clients.values()):
        print("  [writer] ❌ 사용 가능한 API 키 없음")
        return None

    st = _load_state()
    usable = _usable_tiers(st)
    if not usable:
        # 스킬: 전체 쿨다운 중이면 가장 먼저 만료되는 티어 1회만 시도
        now = time.time()
        cooled = [c for c in FALLBACK_MODELS
                  if _clients.get(c["provider"])
                  and (st["quota_until"].get(_tier_id(c), 0) > now
                       or st["structural_until"].get(_tier_id(c), 0) > now)]
        if not cooled:
            print("  [writer] ❌ 사용 가능한 API 키 없음")
            return None
        usable = [min(cooled, key=lambda c: min(
            st["quota_until"].get(_tier_id(c), 9e18),
            st["structural_until"].get(_tier_id(c), 9e18)))]
        print("  [writer] ⚠️  모든 티어 쿨다운 중 — 최조 만료 티어 1회만 시도")

    # 재시도 허용 클래스 (server/network만). timeout·quota·auth·invalid_content는 즉시 다음 티어.
    RETRYABLE = {"server", "network"}

    for ci, cfg in enumerate(usable):
        provider    = cfg["provider"]
        model       = cfg["model"]
        timeout     = cfg["timeout"]
        max_retries = cfg["max_retries"]
        note        = cfg["note"]
        tid         = _tier_id(cfg)
        selected_client = _clients[provider]
        next_tid = _tier_id(usable[ci + 1]) if ci + 1 < len(usable) else "-"

        for attempt in range(max_retries):
            t0 = time.time()
            try:
                print(f"  [writer] {note} | {model} (시도 {attempt+1}/{max_retries})")
                stream = selected_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": build_user_prompt(service)}
                    ],
                    temperature=0.6,
                    max_tokens=8192,
                    top_p=0.9,
                    frequency_penalty=0.3,
                    presence_penalty=0.3,
                    timeout=timeout,
                    stream=True,
                )

                chunks = []
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        print(delta.content, end='', flush=True)
                        chunks.append(delta.content)
                    if chunk.choices[0].finish_reason == 'length':
                        print("\n  ⚠️  [max_tokens 초과]")

                body = ''.join(chunks).strip()
                # 모든 모델에 thinking 태그 스트립 적용 (qwen/DeepSeek R1 계열 대비)
                body = _strip_thinking(body)
                print()

                # 검증 실패 = invalid_content → 동일 티어 재시도 없이 다음 티어
                if not body:
                    raise _ValidationError("빈 응답 (thinking 전용 모델?)")
                if "[PERSONA_CTA]" not in body:
                    raise _ValidationError("PERSONA_CTA 누락")
                if "[RELATED_POSTS]" not in body:
                    raise _ValidationError("RELATED_POSTS 누락")
                if len(body) < 800:
                    raise _ValidationError(f"본문 너무 짧음: {len(body)}자")

                # diffusiongemma 품질 경고
                if "diffusiongemma" in model:
                    print(f"  [writer] ⚠️  실험모델 사용됨 — 품질 검수 권장")

                # 성공: last_success_tier 갱신 + 해당 티어 쿨다운 해제
                st["last_success_tier"] = tid
                st["quota_until"].pop(tid, None)
                st["structural_until"].pop(tid, None)
                _save_state(st)

                print(f"  [writer] ✅ 성공: {model} ({len(body)}자)")
                print(f"  [trace] stage=draft tier={tid} duration_ms={int((time.time()-t0)*1000)} result=ok next=-")
                return {
                    "body":   body,
                    "tokens": 0,
                    "model":  model,
                }

            except Exception as e:
                kind = _classify_error(e)
                dur_ms = int((time.time() - t0) * 1000)
                will_retry = kind in RETRYABLE and attempt < max_retries - 1

                # 스킬 정책별 상태 갱신
                if kind == "quota":
                    st["quota_until"][tid] = time.time() + QUOTA_COOLDOWN_SEC
                    st.pop("last_success_tier", None)
                    st["last_success_tier"] = None if st.get("last_success_tier") == tid else st.get("last_success_tier")
                    _save_state(st)
                elif kind in ("auth", "notfound"):
                    st["structural_until"][tid] = time.time() + STRUCTURAL_COOLDOWN_SEC
                    if st.get("last_success_tier") == tid:
                        st["last_success_tier"] = None
                    _save_state(st)
                elif kind == "invalid_content":
                    # 마지막 성공 티어가 무효 콘텐츠 반환 → 우선순위 즉시 상실
                    if st.get("last_success_tier") == tid:
                        st["last_success_tier"] = None
                    _save_state(st)

                nxt = tid if will_retry else next_tid
                print(f"  [writer] ❌ 시도 {attempt+1} 실패 [{kind}]: {e}")
                print(f"  [trace] stage=draft tier={tid} duration_ms={dur_ms} result={kind} next={nxt}")

                if not will_retry:
                    break
                wait = 2 ** attempt
                print(f"  [writer] {wait}초 후 재시도...")
                time.sleep(wait)

        print(f"  [writer] ⚠️  {model} 종료 → 다음 모델 전환")

    print("  [trace] stage=draft tier=ALL duration_ms=- result=chain_exhausted next=-")
    print("  [writer] ❌ 모든 폴백 모델 실패")
    return None

# ── 단독 실행 테스트 ──────────────────────────────────────────
if __name__ == "__main__":
    test_service = {
        "service_id":   "TEST001",
        "title":        "청년 월세 지원금",
        "category":     "loan",
        "persona":      "youth",
        "persona_hint": '{"age_range": "19~34세", "income_limit": "5000만원 이하", "housing": "무주택자"}',
        "field":        "주거·자립",
        "summary":      "청년층의 주거비 부담을 완화하기 위한 월세 지원 서비스",
        "target":       "만 19세~34세 이하 청년 중 연소득 5,000만원 이하 무주택자",
        "detail":       "월 최대 20만원, 최대 12개월 지원",
        "apply_method": "복지로 온라인 신청 또는 주민센터 방문 신청",
        "contact":      "129",
        "org_name":     "국토교통부",
        "detail_url":   "https://www.bokjiro.go.kr",
    }

    print("=== LLM 폴백 체인 테스트 ===")
    print(f"등록 모델: {len(FALLBACK_MODELS)}개")
    for i, cfg in enumerate(FALLBACK_MODELS, 1):
        key_state = "✅" if _clients.get(cfg["provider"]) else "❌"
        print(f"  {i}. {key_state} [{cfg['provider']}] {cfg['model']} ({cfg['note']})")
    print(f"NVIDIA 키: {'설정됨' if NIM_API_KEY else '❌ 없음'}\n")

    result = generate_article(test_service)
    if result:
        print(f"\n=== 사용된 모델: {result['model']} ===")
        print("=== 생성된 글 (첫 500자) ===")
        print(result["body"][:500])
        print(f"\n... (전체 {len(result['body'])}자)")
    else:
        print("❌ 글 생성 실패")
