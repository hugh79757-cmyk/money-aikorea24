# scripts/auto-writer/writer.py
import os, json, re, time, yaml
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

# ── NVIDIA NIM 폴백 체인 ─────────────────────────────────────
NIM_API_KEY  = os.getenv("NVIDIA_API_KEY")
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# diffusiongemma 메인, gemma-4-31b-it 폴백
FALLBACK_MODELS = [
    {
        "model":       "google/diffusiongemma-26b-a4b-it",
        "timeout":     120,
        "max_retries": 2,
        "note":        "메인 (실험모델)"
    },
    {
        "model":       "google/gemma-4-31b-it",
        "timeout":     120,
        "max_retries": 1,
        "note":        "gemma-4 폴백"
    },
    {
        "model":       "google/gemma-3n-e4b-it",
        "timeout":     90,
        "max_retries": 1,
        "note":        "gemma-3n 최후 폴백"
    },
]

client = OpenAI(
    api_key=NIM_API_KEY,
    base_url=NIM_BASE_URL,
    # blogsmith: max_retries 미설정 → SDK 기본(2)
)

# ── 페르소나 통계 로더 ─────────────────────────────────────
from shared.persona_stats import resolve_keys as _resolve_stat_keys, get_stats as _get_stats, format_for_prompt as _fmt_stats, make_fomo_hook as _make_hook

# ── 시스템 프롬프트 (뱅크샐러드 스타일) ──────────────────────
SYSTEM_PROMPT = """
당신은 대한민국 No.1 금융 정보 플랫폼 수준의 콘텐츠를 생성하는 전문 금융 에디터입니다.
독자는 20~40대 대한민국 직장인/청년이며, 복잡한 금융 정보를 쉽고 빠르게 이해하길 원합니다.

## 글쓰기 철학
- "나만 모르는 것 같아서 불안한" 독자의 FOMO 심리를 해소해 주는 글
- 관료적·상품 소개서 어투 금지. 친한 선배가 알려주는 대화체 사용
- 모든 정보는 "나에게 해당되는지"를 독자가 스스로 판단할 수 있도록 조건을 명확히 제시

## 페르소나 통계 활용 (필수)
- [참고: 페르소나 통계] 섹션의 실제 통계 데이터를 반드시 활용
- 도입부 FOMO 훅에 "서울 35세 남성의 평균 월 소득은 404만원입니다" 같은 구체적 수치 삽입
- "표본 X명 통계청 2024" 출처 표기로 신뢰도 확보
- 독자의 호기심을 자극하는 비교형 서술: "당신의 소득은 평균보다 높나요?"

## 제목 규칙 (필수)
- 첫 줄은 반드시 `# {제목}` 형식으로 출력 (h1 마크다운)
- 구체적 숫자 포함: 금액(만원), 금리(%), 기간(년/개월), 나이 중 최소 1개
- 독자 페르소나 명시: 청년 / 무주택자 / 직장인 / 신혼부부 / 소상공인 / 저신용자 중 택1
- 마무리 키워드: "총정리" / "완벽정리" / "한눈에" / "필독" 중 택1
- 제도·금리 변동 주제는 [2026] 연도 접두어 사용

## 본문 구조 (반드시 이 순서 준수, H2 단위)
1. H2: {제도/상품명}이란? – 1~2문단, 핵심 혜택 수치 포함
2. H2: 신청/가입 조건 – 표(Table) 필수. 조건 불충족 케이스도 명시
3. H2: {금리/지급액/한도} 얼마나 받을 수 있나? – 가구/소득 유형별 계산 포함
4. H2: 신청 방법 – 온라인/오프라인 채널별 단계 안내
5. H2: 자주 묻는 질문 (Q&A 3개 이상)
6. [RELATED_POSTS] – 연관 아티클 링크 3개 (앵커 텍스트 포함)
7. [PERSONA_CTA] – 독자 행동 유도

## 어투 규칙
- 경어체 통일: "~해요", "~이에요", "~할 수 있어요"
- 문장 최대 2줄, 이후 줄바꿈
- 강조는 **볼드** 우선, 이탤릭 금지
- 숫자: 한글 혼용 금지. "165만원" (O), "165만 원" (O), "일백육십오만원" (X)
- 이모지: 섹션 제목 앞 1개, 본문 내 강조 포인트 1~2개 이내

## 표(Table) 사용 기준
- 3개 이상 비교 항목이 있으면 반드시 표로 정리
- 표 아래에는 반드시 출처 각주 추가: * {기관명} {날짜} 기준
- 표 직전에 1~2문장 설명 텍스트 필수 (표만 단독 배치 금지)

## 금지 사항
- 상품코드, 서비스 ID, API 응답 원문 필드명 노출 금지
- "본 상품은~", "당사에서는~" 같은 공급자 어투 금지
- 근거 없는 수익률 예측 및 투자 권유 금지
- 최신 정보 불확실 시 "정확한 내용은 {기관} 공식 홈페이지에서 확인해 주세요" 문구 삽입
- [RELATED_POSTS]와 [PERSONA_CTA]를 ## 헤딩 안에 포함하지 말 것
  잘못된 예: "## [RELATED_POSTS] 관련 아티클"
  올바른 예: "## 관련 아티클" + 별도 줄에 "[RELATED_POSTS]"
- [RELATED_POSTS]와 [PERSONA_CTA]는 반드시 단독 줄에 위치할 것
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

def generate_article(service: dict) -> dict | None:
    if not NIM_API_KEY:
        print("  [writer] ❌ NVIDIA_API_KEY 없음")
        return None

    for cfg in FALLBACK_MODELS:
        model      = cfg["model"]
        timeout    = cfg["timeout"]
        max_retries = cfg["max_retries"]
        note       = cfg["note"]

        for attempt in range(max_retries):
            try:
                print(f"  [writer] {note} | {model} (시도 {attempt+1}/{max_retries})")
                stream = client.chat.completions.create(
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
                body = _strip_thinking(body)
                print()

                # 필수 요소 검증
                if "[PERSONA_CTA]" not in body:
                    raise ValueError("PERSONA_CTA 누락")
                if "[RELATED_POSTS]" not in body:
                    raise ValueError("RELATED_POSTS 누락")
                if len(body) < 800:
                    raise ValueError(f"본문 너무 짧음: {len(body)}자")

                # diffusiongemma 품질 경고
                if "diffusiongemma" in model:
                    print(f"  [writer] ⚠️  실험모델 사용됨 — 품질 검수 권장")

                print(f"  [writer] ✅ 성공: {model} ({len(body)}자)")
                return {
                    "body":   body,
                    "tokens": 0,
                    "model":  model,
                }

            except Exception as e:
                wait = 2 ** attempt
                print(f"  [writer] ❌ 시도 {attempt+1} 실패: {e}")
                if attempt < max_retries - 1:
                    print(f"  [writer] {wait}초 후 재시도...")
                    time.sleep(wait)

        print(f"  [writer] ⚠️  {model} 모두 실패 → 다음 모델 전환")

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

    print("=== NVIDIA NIM 폴백 체인 테스트 ===")
    print(f"사용 가능한 모델: {len(FALLBACK_MODELS)}개")
    for i, cfg in enumerate(FALLBACK_MODELS, 1):
        print(f"  {i}. {cfg['model']} ({cfg['note']})")
    print(f"API 키: {'설정됨' if NIM_API_KEY else '❌ 없음'}\n")

    result = generate_article(test_service)
    if result:
        print(f"\n=== 사용된 모델: {result['model']} ===")
        print("=== 생성된 글 (첫 500자) ===")
        print(result["body"][:500])
        print(f"\n... (전체 {len(result['body'])}자)")
    else:
        print("❌ 글 생성 실패")
