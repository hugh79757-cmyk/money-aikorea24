"""
Project Paths — all paths derived from PROJECT_ROOT.
Usage:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from paths import PROJECT_ROOT, BLOG_DIR, DOTENV_PATH, ...
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

PROJECT_ROOT    = str(_ROOT)
BLOG_DIR        = str(_ROOT / "src" / "content" / "blog")
INBOX_DIR       = str(_ROOT / "inbox")
BG_IMG_DIR      = str(_ROOT / "public" / "bg_img")
THUMBNAIL_DIR   = str(_ROOT / "public" / "blog-thumbnails")
DOTENV_PATH     = str(_ROOT / ".env")
COMMON_ENV_PATH = str(Path.home() / ".env.common")
SCRIPTS_DIR     = str(_ROOT / "scripts")
