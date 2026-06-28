import json
import os

CONFIG = os.path.join(os.path.dirname(__file__), "config", "category-keywords.json")
CATEGORIES = ["insurance", "invest", "loan", "tax"]

def load_config() -> dict:
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def classify(text: str) -> tuple[str, bool]:
    """
    반환: (category, needs_review)
    동점 or 모든 점수 0 → ("general", True)
    """
    config = load_config()
    scores = {}
    for cat in CATEGORIES:
        keywords = config[cat]["keywords"]
        scores[cat] = sum(1 for kw in keywords if kw in text)

    max_score = max(scores.values())

    if max_score == 0:
        return "general", True

    top_cats = [c for c, s in scores.items() if s == max_score]
    if len(top_cats) > 1:
        return "general", True

    return top_cats[0], False
