import json
import os

CONFIG = os.path.join(os.path.dirname(__file__), "config", "finance-keywords.json")
THRESHOLD = 2

def load_keywords() -> list:
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)["keywords"]

def is_finance(text: str) -> tuple[bool, int]:
    keywords = load_keywords()
    count = sum(1 for kw in keywords if kw in text)
    return count >= THRESHOLD, count
