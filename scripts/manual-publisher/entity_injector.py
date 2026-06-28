import os
import re

BLOG_DIR = "/Users/twinssn/projects/money-aikorea24/src/content/blog"


def get_posts_by_category() -> dict:
    """
    blog/ 전체 스캔 → 카테고리별 {slug, title} 목록 반환
    """
    result = {}
    for fname in os.listdir(BLOG_DIR):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(BLOG_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        cat_m = re.search(r"category:\s*[\"']?(\w+)", content)
        title_m = re.search(r"title:\s*[\"']?(.+)", content)
        date_m = re.search(r"pubDate:\s*(\S+)", content)

        if not cat_m or not title_m:
            continue

        cat = cat_m.group(1).strip()
        title = title_m.group(1).strip().strip('"\'')
        slug = fname.replace(".md", "")
        pub_date = date_m.group(1).strip() if date_m else "0"

        if cat not in result:
            result[cat] = []
        result[cat].append({"slug": slug, "title": title, "pubDate": pub_date})

    # 각 카테고리별 최신순 정렬
    for cat in result:
        result[cat].sort(key=lambda x: x["pubDate"], reverse=True)

    return result


def inject(content: str, category: str, current_slug: str = "") -> str:
    """
    1. 본문 중간에 관련 글 콜아웃 삽입 (동적 — blog/ 스캔)
    2. 글 맨 끝에 persona-entity 주석 삽입
    """
    # persona-entity 주석
    marker = f"<!-- persona-entity: {category} -->"
    if marker not in content:
        content = content.rstrip() + f"\n\n{marker}\n"

    # 이미 내부링크 콜아웃 있으면 제거 후 재삽입 (최신화)
    content = re.sub(r"\n*<!-- related-link -->.*?(?=\n\n|\Z)", "", content, flags=re.DOTALL)

    # frontmatter 분리
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = "---" + parts[1] + "---"
            body = parts[2]
        else:
            return content
    else:
        fm = ""
        body = content

    # 동적으로 같은 카테고리 글 스캔
    posts_by_cat = get_posts_by_category()
    related = [
        p for p in posts_by_cat.get(category, [])
        if p["slug"] != current_slug
    ][:1]

    # general이고 없으면 tax에서 가져오기
    if not related:
        related = [
            p for p in posts_by_cat.get("tax", [])
            if p["slug"] != current_slug
        ][:1]

    if not related:
        return fm + body

    # 본문 단락 분리 후 중간에 삽입
    paragraphs = body.split("\n\n")
    if len(paragraphs) < 4:
        return fm + body

    mid = len(paragraphs) // 2
    r = related[0]
    callout = f"<!-- related-link -->\n> 📌 **함께 읽으면 좋은 글**\n> [{r['title']}](/blog/{r['slug']}/)"

    paragraphs.insert(mid, callout)
    new_body = "\n\n".join(paragraphs)
    return fm + new_body
