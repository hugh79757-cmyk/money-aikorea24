import re
import os
from datetime import date


def extract_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return parse_yaml_simple(parts[1]), parts[2]


def parse_yaml_simple(fm_raw: str) -> dict:
    result = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("["):
            result[key] = re.findall(r'["\']([^"\']*)["\']', val)
            continue
        if val.lower() == "true":
            result[key] = True
            continue
        if val.lower() == "false":
            result[key] = False
            continue
        if len(val) >= 2 and val[0] in ('"', "'") and val[0] == val[-1]:
            val = val[1:-1]
        result[key] = val
    return result


def build_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            items = ", ".join(f'"{x}"' for x in v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            sv = str(v)
            if any(c in sv for c in ':#[]{}|>&*!,?'):
                sv = sv.replace('"', '\\"')
                lines.append(f'{k}: "{sv}"')
            else:
                lines.append(f"{k}: {sv}")
    lines.append("---")
    return "\n".join(lines)


def date_from_filename(fname: str) -> str:
    basename = os.path.basename(fname)
    m = re.match(r'(\d{4})(\d{2})(\d{2})', basename)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return str(date.today())


def slug_from_filename(fname: str) -> str:
    basename = os.path.basename(fname).replace(".md", "")
    cleaned = re.sub(r'^\d{8}-\d{6}-', "", basename)
    cleaned = re.sub(r'^\d{8}-', "", cleaned)
    return cleaned


def transform(filepath: str, category: str, needs_review: bool) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    fm, body = extract_frontmatter(raw)
    slug = slug_from_filename(filepath)

    if "date" in fm:
        fm["pubDate"] = fm.pop("date")
    elif "pubDate" not in fm:
        fm["pubDate"] = date_from_filename(filepath)

    fm["draft"] = False
    fm.pop("source_file", None)
    fm.pop("categories", None)
    fm["category"] = category
    if needs_review:
        fm["needs_review"] = True
    fm["updatedDate"] = str(date.today())
    fm["heroImage"] = f"/blog-thumbnails/{slug}.jpg"
    if "tags" not in fm:
        fm["tags"] = []

    ordered = {}
    for k in ["title", "description", "pubDate", "updatedDate", "draft",
              "category", "tags", "heroImage", "needs_review"]:
        if k in fm:
            ordered[k] = fm[k]
    for k, v in fm.items():
        if k not in ordered:
            ordered[k] = v

    return build_frontmatter(ordered) + "\n" + body
