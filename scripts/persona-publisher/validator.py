"""
Persona Publisher — Validator
Frontmatter 타입 검증 + auto-fix + NFD 파일명 정규화

publisher.py에서 transform() 후, blog/에 쓰기 전에 호출한다.
"""
import os
import re
import unicodedata
from datetime import date

# Astro content.config.ts 스키마와 일치하는 enum
VALID_CATEGORIES = {"insurance", "invest", "loan", "tax", "general"}

# 배열이어야 하는 frontmatter 필드
ARRAY_FIELDS = {"tags"}

# boolean이어야 하는 frontmatter 필드
BOOLEAN_FIELDS = {"draft", "needs_review"}


def validate_frontmatter(fm: dict) -> tuple[dict, list[str]]:
    """
    frontmatter 딕셔너리를 받아서 타입 오류를 자동 수정.
    반환: (수정된 fm, 적용된 fix 설명 목록)
    """
    fixes: list[str] = []

    for key in ARRAY_FIELDS:
        if key not in fm:
            continue
        val = fm[key]
        if isinstance(val, list):
            continue  # 이미 배열 — OK
        if isinstance(val, str):
            # "a, b, c" 또는 "a,b,c" → ["a", "b", "c"]
            raw = val.strip().strip('"').strip("'")
            items = [x.strip() for x in re.split(r'[,\s]+', raw) if x.strip()]
            if not items:
                # 빈 문자열 → 빈 배열
                fm[key] = []
            else:
                fm[key] = items
            fixes.append(f"{key}: 문자열 → 배열 ({len(items)}개 항목)")
        else:
            # 알 수 없는 타입 → 빈 배열 fallback
            fm[key] = []
            fixes.append(f"{key}: {type(val).__name__} → 빈 배열 (fallback)")

    for key in BOOLEAN_FIELDS:
        if key not in fm:
            continue
        val = fm[key]
        if isinstance(val, bool):
            continue
        if isinstance(val, str):
            lower = val.strip().lower()
            if lower in ("true", "yes", "1"):
                fm[key] = True
                fixes.append(f"{key}: '{val}' → true")
            elif lower in ("false", "no", "0", ""):
                fm[key] = False
                fixes.append(f"{key}: '{val}' → false")
            else:
                # 기본값
                fm[key] = False
                fixes.append(f"{key}: '{val}' → false (기본값)")

    # category 검증
    if "category" in fm:
        cat = fm["category"]
        if isinstance(cat, str) and cat not in VALID_CATEGORIES:
            old_cat = cat
            fm["category"] = "general"
            fixes.append(f"category: '{old_cat}' → 'general' (유효하지 않은 카테고리)")

    return fm, fixes


def validate_and_fix_content(content: str) -> tuple[str, list[str]]:
    """
    전체 파일 내용(---frontmatter--- + body)을 받아서
    frontmatter만 파싱 → 검증 → 재조립.
    반환: (수정된 content, fix 목록)
    """
    from transformer import extract_frontmatter, build_frontmatter

    fm, body = extract_frontmatter(content)
    if not fm:
        # frontmatter가 없으면 건드리지 않음
        return content, []

    fm, fixes = validate_frontmatter(fm)

    # updatedDate 갱신 (수정이 있었으므로)
    if fixes:
        fm["updatedDate"] = str(date.today())

    corrected = build_frontmatter(fm) + "\n" + body
    return corrected, fixes


def normalize_slug(slug: str) -> str:
    """
    NFD(Normalization Form D)로 저장된 slug를 NFC로 변환하고,
    공백을 하이픈으로 치환, 연속 하이픈 → 단일 하이픈.
    """
    # NFC 정규화 (자모 결합)
    normalized = unicodedata.normalize("NFC", slug)
    # 공백 → 하이픈
    normalized = re.sub(r"\s+", "-", normalized)
    # 연속 하이픈 → 단일 하이픈
    normalized = re.sub(r"-{2,}", "-", normalized)
    # 앞뒤 하이픈 제거
    normalized = normalized.strip("-")
    return normalized


def normalize_file_content(filename: str, content: str) -> tuple[str, str, list[str]]:
    """
    파일명과 내용을 함께 정규화.
    반환: (정규화된 파일명, 수정된 content, fix 목록)
    """
    from transformer import extract_frontmatter, build_frontmatter

    fixes: list[str] = []

    # 1. 파일명 정규화
    new_name = normalize_slug(filename)
    if new_name != filename:
        fixes.append(f"파일명 정규화: '{filename}' → '{new_name}'")

    # 2. content 내부의 heroImage 경로도 정규화
    fm, body = extract_frontmatter(content)
    if fm:
        hero = fm.get("heroImage", "")
        if hero:
            normalized_hero = normalize_slug(hero)
            if normalized_hero != hero:
                fm["heroImage"] = normalized_hero
                fixes.append(f"heroImage 정규화: '{hero}' → '{normalized_hero}'")
                content = build_frontmatter(fm) + "\n" + body

    return new_name, content, fixes
