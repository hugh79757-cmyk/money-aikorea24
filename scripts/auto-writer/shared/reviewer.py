import os, re, json, requests
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import paths

load_dotenv(paths.DOTENV_PATH)
load_dotenv(paths.COMMON_ENV_PATH)

MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_URL = "https://api.mimo.kr/v2_5/complete"

MARKER_PLACEHOLDER_PREFIX = "__MARKER_"
MARKER_PLACEHOLDER_SUFFIX = "__"

PERSONA_CTA_MARKER = "[PERSONA_CTA]"
RELATED_POSTS_MARKER = "[RELATED_POSTS]"

def _extract_and_protect(body):
    """마커를 추출해 Placeholder로 대체, 원본 매핑 반환"""
    mapping = {}
    modified = body

    for marker in [PERSONA_CTA_MARKER, RELATED_POSTS_MARKER]:
        count = 0
        while marker in modified:
            placeholder = f"{MARKER_PLACEHOLDER_PREFIX}{marker[1:-1]}_{count}{MARKER_PLACEHOLDER_SUFFIX}"
            modified = modified.replace(marker, placeholder, 1)
            mapping[placeholder] = marker
            count += 1

    return modified, mapping

def _restore_markers(body, mapping):
    """Placeholder를 원본 마커로 복원"""
    result = body
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result, set(mapping.keys()) - set(re.findall(rf"{MARKER_PLACEHOLDER_PREFIX}[^_]+_\d+{MARKER_PLACEHOLDER_SUFFIX}", result))

def _ensure_markers(body):
    """CTA 마커가 없으면 fallback 위치에 삽입"""
    has_cta = PERSONA_CTA_MARKER in body
    has_related = RELATED_POSTS_MARKER in body
    needs_cta_insert = not has_cta
    needs_related_insert = not has_related

    if needs_cta_insert:
        idx = body.find("\n## 신청 방법")
        if idx == -1:
            idx = body.find("## 신청")
        if idx == -1:
            idx = body.find("\n## ")
        if idx != -1:
            next_section = body.find("\n## ", idx + 3)
            insert_pos = next_section if next_section != -1 else len(body)
            body = body[:insert_pos] + f"\n\n{PERSONA_CTA_MARKER}\n" + body[insert_pos:]
        else:
            body += f"\n\n{PERSONA_CTA_MARKER}\n"

    if needs_related_insert:
        idx = body.find("## 마무리")
        if idx == -1:
            idx = body.find("\n## ")
            if idx != -1:
                insert_pos = body.rfind("\n## ")
                body = body[:insert_pos] + f"\n{RELATED_POSTS_MARKER}\n" + body[insert_pos:]
            else:
                body += f"\n{RELATED_POSTS_MARKER}\n"
        else:
            after_summary = body.find("\n", idx)
            if after_summary != -1:
                next_section_end = body.find("\n## ", after_summary + 1)
                insert_pos = next_section_end if next_section_end != -1 else len(body)
                body = body[:insert_pos] + f"\n\n{RELATED_POSTS_MARKER}\n" + body[insert_pos:]
            else:
                body += f"\n\n{RELATED_POSTS_MARKER}\n"

    return body, needs_cta_insert or needs_related_insert

def review_article(body, model_used="unknown"):
    """Mimo v2.5 검수 + 마커 보호/복원"""
    protected_body, marker_map = _extract_and_protect(body)
    issues = []
    needs_review = False

    if not MIMO_API_KEY:
        issues.append("MIMO_API_KEY 없음, 검수 스킵")
        restored_body, lost = _restore_markers(protected_body, marker_map)
        restored_body, fixed = _ensure_markers(restored_body)
        if fixed:
            issues.append("마커 fallback 삽입")
        return restored_body, issues, True

    system_prompt = (
        "당신은 한국어 블로그 글 교정 전문가입니다. "
        "아래 기준으로 검수하고 수정이 필요한 부분만 수정해서 전체 글을 출력하세요.\n\n"
        "1. CTA(클릭 유도 문구)가 자연스럽게 배치되었는가?\n"
        "2. 헤딩 계층이 올바른가? (h1 없음, h2 > h3 순서)\n"
        "3. FOMO 훅이 도입부에 있는가?\n"
        "4. 전체 분량이 1,800~2,800자인가?\n"
        "5. 외부 링크는 신청방법 섹션에만 있는가?\n"
        "6. 정보가 정확하고 구체적인가? (숫자, 금액, 기한 등)\n"
        "7. <think> 태그가 있으면 제거했는가?\n"
        "8. 마크다운 문법이 올바른가?"
    )

    user_prompt = f"검수할 블로그 글:\n\n{protected_body}"

    try:
        resp = requests.post(
            MIMO_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": MIMO_API_KEY,
            },
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 8196,
                "temperature": 0.1,
                "top_p": 0.2,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        reviewed = data["choices"][0]["message"]["content"]
    except Exception as e:
        issues.append(f"Mimo 검수 실패: {e}")
        needs_review = True
        restored_body, lost = _restore_markers(protected_body, marker_map)
        restored_body, fixed = _ensure_markers(restored_body)
        if fixed:
            issues.append("마커 fallback 삽입")
        return restored_body, issues, True

    restored_body, lost_placeholders = _restore_markers(reviewed, marker_map)
    if lost_placeholders:
        issues.append(f"마커 복원 실패: {lost_placeholders}")
        needs_review = True
    restored_body, fixed = _ensure_markers(restored_body)
    if fixed:
        issues.append("마커 fallback 삽입")
    if model_used and "diffusiongemma" in model_used.lower():
        needs_review = True
        issues.append("diffusiongemma 모델 → 검수 필요")

    return restored_body, issues, needs_review
