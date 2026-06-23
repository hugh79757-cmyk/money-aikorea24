import re, unicodedata

REQUIRED_HEADINGS = [
    "이란?",
    "조건",
    "방법",
    "자주 묻는 질문"
]

PERSONA_CTA_TEXTS = {
    "youth":     "내 또래 20대는 어떤 혜택을 받고 있을까?",
    "worker":    "같은 연봉 직장인들은 얼마나 환급받을까?",
    "newlywed":  "신혼부부 또래는 어떤 지원을 받고 있을까?",
    "unhoused":  "무주택 또래가 가장 많이 신청한 혜택은?",
    "lowincome": "내 소득 수준에서 받을 수 있는 혜택 확인",
    "midlife":   "50대 또래의 재무 현황이 궁금하다면?",
    "general":   "내 나이·지역 또래는 어떻게 살고 있을까?",
}

def make_persona_cta_block(cta_url: str, persona: str = "default") -> str:
    text = PERSONA_CTA_TEXTS.get(persona, "내 또래는 어떤 혜택을 받고 있을까?")
    return (
        f"\n\n> 💡 **{text}**\n"
        f"> 나이·성별·지역만 입력하면 주거·직업·소득 통계를 바로 확인할 수 있습니다.\n"
        f">\n"
        f"> **[👉 내 페르소나 분석하기 →]({cta_url})**\n"
    )

FAKE_LINK_PATTERNS = [
    r'\[.*?\]\(https?://example\.com[^\)]*\)',
    r'\[.*?\]\(https?://example\.org[^\)]*\)',
    r'\[.*?\]\(https?://www\.example[^\)]*\)',
    r'\[[^\[\]]*\]\(#\)',               # [text](#) - 단일 링크만 매치
    r'\[.*?\]\(javascript:[^\)]*\)',
]

def remove_fake_links(body: str) -> str:
    for pattern in FAKE_LINK_PATTERNS:
        body = re.sub(pattern, lambda m: re.search(r'\[([^\]]+)\]', m.group()).group(1), body)
    return body

def validate_and_fix(body: str, cta_url: str = None, cta_block: str = None) -> tuple[str, list]:
    issues = []

    # 0. 가짜 링크 제거
    body = remove_fake_links(body)

    # 1. CTA 블록 강제 삽입 (없으면 ## 마무리 직전에 삽입)
    default_block = cta_block or make_persona_cta_block(cta_url or "https://persona.aikorea24.kr/my-persona")
    if "내 또래" not in body and "[PERSONA_CTA]" not in body:
        if "## 마무리" in body:
            body = body.replace("## 마무리", default_block + "\n## 마무리")
        else:
            body += default_block
        issues.append("CTA_INSERTED")

    # [PERSONA_CTA] 플레이스홀더 실제 블록으로 교체
    if "[PERSONA_CTA]" in body:
        body = body.replace("[PERSONA_CTA]", default_block)

    # 2. 헤딩 구조 검증
    for heading in REQUIRED_HEADINGS:
        if heading not in body:
            issues.append(f"HEADING_MISSING:{heading}")

    # 3. 본문 길이 검증
    if len(body.strip()) < 800:
        issues.append("BODY_TOO_SHORT")

    return body, issues

def fill_related_posts(body: str, related: list) -> str:
    """[RELATED_POSTS] 플레이스홀더를 실제 내부 링크로 교체"""
    if not related:
        body = body.replace("[RELATED_POSTS]", "")
        return body

    block = "\n\n#### 비슷한 상황의 사람들이 함께 찾아본 글\n"
    for post in related:
        block += f"- [{post['title']}](/blog/{post['slug']}/)\n"

    body = body.replace("[RELATED_POSTS]", block)
    return body

def make_slug(title: str, service_id: str) -> str:
    slug = unicodedata.normalize("NFC", title)
    slug = re.sub(r"[^\w\s가-힣-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = slug[:60]
    return f"{slug}-{service_id[-6:]}"

def make_frontmatter(title, description, category,
                     hero_image, tags, slug,
                     needs_review=False) -> str:
    from datetime import datetime
    pub_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")
    tags_str  = str(tags).replace("'", '"')
    return f"""---
title: "{title}"
description: "{description}"
pubDate: {pub_date}
updatedDate: {pub_date}
heroImage: "{hero_image}"
category: "{category}"
tags: {tags_str}
draft: false
needs_review: {str(needs_review).lower()}
---\n\n"""
