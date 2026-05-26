#!/usr/bin/env python3
"""36개 누락 blog-thumbnails 플레이스홀더 생성 스크립트"""
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BLOG_DIR    = Path(__file__).parent.parent / "src/content/blog"
THUMB_DIR   = Path(__file__).parent.parent / "public/blog-thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

# 카테고리별 그라디언트 색상 (시작/끝)
CATEGORY_COLORS = {
    "tax":       ((30,  90, 160), (10,  50, 110)),   # 파랑
    "invest":    ((20, 140,  80), ( 5,  90,  50)),   # 초록
    "loan":      ((200, 110,  20), (140,  70,  10)),  # 주황
    "insurance": ((120,  40, 160), ( 70,  20, 110)),  # 보라
    "general":   ((70,  70,  90), (40,  40,  60)),   # 회색
}

# 한국어 지원 폰트 (AppleSDGothicNeo 우선)
FONT_PATHS = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NanumGothic.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
]

def get_font(size):
    for fp in FONT_PATHS:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_gradient(draw, w, h, c1, c2):
    """수직 그라디언트 배경"""
    for y in range(h):
        t = y / h
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def wrap_text(text, font, max_width, draw):
    """텍스트 줄바꿈"""
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def make_thumbnail(slug, title, category):
    W, H = 1200, 630
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    c1, c2 = CATEGORY_COLORS.get(category, CATEGORY_COLORS["general"])
    draw_gradient(draw, W, H, c1, c2)

    # 반투명 오버레이 (하단)
    overlay = Image.new("RGBA", (W, H // 2), (0, 0, 0, 80))
    img.paste(overlay, (0, H // 2), overlay)

    # 카테고리 레이블
    cat_font  = get_font(32)
    cat_label = category.upper()
    draw.text((60, 60), cat_label, font=cat_font, fill=(255, 255, 255, 200))

    # 제목 텍스트
    title_font = get_font(58)
    lines      = wrap_text(title, title_font, W - 120, draw)
    # 최대 3줄
    lines = lines[:3]
    total_h = len(lines) * 72
    y_start = (H - total_h) // 2 + 40

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tw   = bbox[2] - bbox[0]
        x    = (W - tw) // 2
        y    = y_start + i * 72
        # 그림자
        draw.text((x + 3, y + 3), line, font=title_font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255))

    # 하단 도메인
    small_font = get_font(28)
    draw.text((60, H - 60), "money-aikorea24.pages.dev", font=small_font,
              fill=(255, 255, 255, 160))

    out = THUMB_DIR / f"{slug}.jpg"
    img.save(out, "JPEG", quality=88)
    return out


def parse_fm(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    import yaml
    try:
        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def main():
    generated = 0
    for md_path in sorted(BLOG_DIR.glob("*.md")):
        slug = md_path.stem
        dest = THUMB_DIR / f"{slug}.jpg"
        if dest.exists():
            continue  # 이미 있으면 스킵

        fm    = parse_fm(md_path.read_text(encoding="utf-8"))
        title = fm.get("title", slug)
        cat   = str(fm.get("category", "general")).strip('"')
        if cat not in CATEGORY_COLORS:
            cat = "general"

        out = make_thumbnail(slug, title, cat)
        print(f"  ✅ {slug}.jpg ({cat})")
        generated += 1

    print(f"\n총 {generated}개 생성 완료 → {THUMB_DIR}")


if __name__ == "__main__":
    main()
