"""
연도 검증 + 치환 모듈 — 본문/제목에서 과거 연도 감지 후 현재 연도로 변경
"""
import re
from datetime import datetime


def get_current_year() -> int:
    return datetime.now().year


def extract_years(text: str) -> set[int]:
    """텍스트에서 모든 연도(20xx) 추출"""
    return {int(m) for m in re.findall(r'(20\d{2})년', text)}


def check_year_freshness(
    pub_date: str, body: str, title: str = ""
) -> tuple[bool, list[int]]:
    """
    pubDate 연도 vs 본문/제목 연도 비교 (±1년 허용).
    Returns: (is_fresh, stale_years)
    """
    pub_year = int(pub_date[:4])
    all_years = extract_years(body) | extract_years(title)
    stale = sorted(y for y in all_years if abs(y - pub_year) > 1)
    return len(stale) == 0, stale


def replace_stale_years(text: str, current_year: int = None) -> tuple[str, list[int]]:
    """
    본문에서 과거 연도를 현재 연도로 치환.
    '2024년' → '2026년', '2024년 5월' → '2026년 5월'
    Returns: (수정된 텍스트, 치환된 연도 목록)
    """
    if current_year is None:
        current_year = get_current_year()

    replaced = []
    years_in_text = extract_years(text)

    for year in sorted(years_in_text):
        if abs(year - current_year) > 1:
            text = text.replace(f"{year}년", f"{current_year}년")
            replaced.append(year)

    return text, replaced
