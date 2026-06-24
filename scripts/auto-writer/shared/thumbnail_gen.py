import os, random, textwrap, boto3
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from dotenv import load_dotenv

load_dotenv("/Users/twinssn/Projects/money-aikorea24/.env")
load_dotenv(os.path.expanduser("~/.env.common"))

BG_DIR   = os.getenv("BG_IMG_DIR",
           "/Users/twinssn/Projects/money-aikorea24/public/bg_img")
FONT_PATH = os.getenv("THUMB_FONT",
           "/System/Library/Fonts/Supplemental/AppleGothic.ttf")
R2_BUCKET   = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS   = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET   = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BASE_URL = "https://pub-2f5c7af1c303419a933069212bc25874.r2.dev/blog-thumbnails"

SIZE = 800

CATEGORY_BG_POOL = {
    "insurance": ["bg_seoul_30.jpeg", "bg_single_50.jpeg"],
    "invest":    ["bg_gyeonggi_40.jpeg", "bg_general_01.jpeg", "bg_general_02.jpeg"],
    "loan":      ["bg_seoul_20.jpeg", "bg_busan_all.jpeg", "bg_rural_50.jpeg"],
    "tax":       ["bg_seoul_60.jpeg", "bg_single_20.jpeg", "bg_general_03.jpeg"],
    "general":   ["bg_gangwon_all.jpeg", "bg_jeju_all.jpeg", "bg_general_04.jpeg", "bg_general_05.jpeg"],
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

def get_font(size: int):
    candidates = [
        FONT_PATH,
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def generate(slug: str, title: str, category: str) -> str | None:
    try:
        pool = CATEGORY_BG_POOL.get(category, ["bg_gangwon_all.jpeg"])
        bg_file = random.choice(pool)
        bg_path = os.path.join(BG_DIR, bg_file)
        if os.path.exists(bg_path):
            img = Image.open(bg_path).convert("RGB").resize((SIZE, SIZE))
        else:
            accent = CATEGORY_ACCENT.get(category, (31, 41, 55))
            img = Image.new("RGB", (SIZE, SIZE), accent)

        # 어둡게 (텍스트 가독성)
        img = ImageEnhance.Brightness(img).enhance(0.45)

        draw = ImageDraw.Draw(img)

        # 하단 그라디언트 — 반투명 검정 띠
        overlay = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
        mask = Image.new("L", (SIZE, SIZE), 0)
        mask_draw = ImageDraw.Draw(mask)
        for y in range(SIZE // 2, SIZE):
            alpha = int(180 * (y - SIZE // 2) / (SIZE // 2))
            mask_draw.line([(0, y), (SIZE, y)], fill=alpha)
        img = Image.composite(overlay, img, mask)
        draw = ImageDraw.Draw(img)

        # 카테고리 뱃지 (상단 좌측)
        badge_font = get_font(28)
        badge_text = CATEGORY_LABELS.get(category, category)
        accent = CATEGORY_ACCENT.get(category, (31, 41, 55))
        bx, by = 50, 50
        bbox = draw.textbbox((bx, by), badge_text, font=badge_font)
        pad = 12
        draw.rounded_rectangle(
            [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
            radius=20,
            fill=(*accent, 220),
        )
        draw.text((bx, by), badge_text, font=badge_font, fill=(255, 255, 255))

        # 제목 (중앙 하단 영역)
        title_font = get_font(52)
        wrapped = textwrap.wrap(title, width=14)[:3]
        line_gap = 68
        total_h = len(wrapped) * line_gap
        start_y = SIZE - total_h - 100

        for i, line in enumerate(wrapped):
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_w = bbox[2] - bbox[0]
            x = (SIZE - text_w) // 2
            y = start_y + i * line_gap
            draw.text((x + 2, y + 2), line, font=title_font, fill=(0, 0, 0, 160))
            draw.text((x, y), line, font=title_font, fill=(255, 255, 255))

        # 도메인 (하단 중앙)
        domain_font = get_font(24)
        domain = "persona.aikorea24.kr"
        bbox = draw.textbbox((0, 0), domain, font=domain_font)
        domain_w = bbox[2] - bbox[0]
        draw.text(
            ((SIZE - domain_w) // 2, SIZE - 44),
            domain,
            font=domain_font,
            fill=(200, 200, 200),
        )

        # 임시 저장 후 R2 업로드
        tmp_path = f"/tmp/{slug}.jpg"
        img.save(tmp_path, "JPEG", quality=90)

        s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS,
            aws_secret_access_key=R2_SECRET,
        )
        s3.upload_file(tmp_path, R2_BUCKET,
                       f"blog-thumbnails/{slug}.jpg",
                       ExtraArgs={"ContentType": "image/jpeg"})
        os.remove(tmp_path)

        url = f"{R2_BASE_URL}/{slug}.jpg"
        print(f"  [thumbnail] 업로드 완료: {url}")
        return url

    except Exception as e:
        print(f"  [thumbnail] 실패: {e}")
        return None
