import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

THUMBNAIL_DIR = "/Users/twinssn/projects/money-aikorea24/public/blog-thumbnails"
BG_DIR = "/Users/twinssn/Projects/money-aikorea24/public/bg_img"

CATEGORY_BG = {
    "insurance": "bg_seoul_30.jpeg",
    "invest":    "bg_gyeonggi_40.jpeg",
    "loan":      "bg_seoul_20.jpeg",
    "tax":       "bg_seoul_60.jpeg",
    "general":   "bg_gangwon_all.jpeg",
}

CATEGORY_LABELS = {
    "insurance": "보험",
    "invest":    "투자·절세",
    "loan":      "대출·부동산",
    "tax":       "세금·절약",
    "general":   "금융 가이드",
}

CATEGORY_ACCENT = {
    "insurance": (30,  58,  95),
    "invest":    (6,   95,  70),
    "loan":      (146, 64,  14),
    "tax":       (76,  29,  149),
    "general":   (31,  41,  55),
}

SIZE = 1024


def get_font(size: int):
    candidates = [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate(slug: str, title: str, category: str) -> str:
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    out_path = os.path.join(THUMBNAIL_DIR, f"{slug}.jpg")

    if os.path.exists(out_path):
        return out_path

    # 배경 이미지 로드
    bg_file = CATEGORY_BG.get(category, "bg_gangwon_all.jpeg")
    bg_path = os.path.join(BG_DIR, bg_file)
    if os.path.exists(bg_path):
        img = Image.open(bg_path).convert("RGB").resize((SIZE, SIZE))
    else:
        accent = CATEGORY_ACCENT.get(category, (31, 41, 55))
        img = Image.new("RGB", (SIZE, SIZE), accent)

    # 어둡게 (텍스트 가독성)
    img = ImageEnhance.Brightness(img).enhance(0.45)

    draw = ImageDraw.Draw(img)

    # 하단 그라디언트 느낌 — 반투명 검정 띠
    overlay = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    mask = Image.new("L", (SIZE, SIZE), 0)
    mask_draw = ImageDraw.Draw(mask)
    for y in range(SIZE // 2, SIZE):
        alpha = int(180 * (y - SIZE // 2) / (SIZE // 2))
        mask_draw.line([(0, y), (SIZE, y)], fill=alpha)
    img = Image.composite(overlay, img, mask)
    draw = ImageDraw.Draw(img)

    # 카테고리 뱃지 (상단 좌측)
    badge_font = get_font(32)
    badge_text = CATEGORY_LABELS.get(category, category)
    accent = CATEGORY_ACCENT.get(category, (31, 41, 55))
    bx, by = 60, 60
    bbox = draw.textbbox((bx, by), badge_text, font=badge_font)
    pad = 14
    draw.rounded_rectangle(
        [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
        radius=24,
        fill=(*accent, 220),
    )
    draw.text((bx, by), badge_text, font=badge_font, fill=(255, 255, 255))

    # 제목 (중앙 하단 영역)
    title_font = get_font(64)
    wrapped = textwrap.wrap(title, width=16)[:3]
    line_gap = 80
    total_h = len(wrapped) * line_gap
    start_y = SIZE - total_h - 120

    for i, line in enumerate(wrapped):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_w = bbox[2] - bbox[0]
        x = (SIZE - text_w) // 2
        y = start_y + i * line_gap
        draw.text((x + 2, y + 2), line, font=title_font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255))

    # 도메인 (하단 중앙)
    domain_font = get_font(28)
    domain = "persona.aikorea24.kr"
    bbox = draw.textbbox((0, 0), domain, font=domain_font)
    domain_w = bbox[2] - bbox[0]
    draw.text(
        ((SIZE - domain_w) // 2, SIZE - 54),
        domain,
        font=domain_font,
        fill=(200, 200, 200),
    )

    img.save(out_path, "JPEG", quality=90)
    return out_path
