def inject(content: str, category: str) -> str:
    """
    글 본문 맨 끝에 persona-entity 주석 삽입
    이미 주석이 있으면 스킵
    """
    marker = f"<!-- persona-entity: {category} -->"
    if marker in content:
        return content
    return content.rstrip() + f"\n\n{marker}\n"
