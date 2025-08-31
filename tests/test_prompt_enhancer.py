import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from modules.prompting import enhance_prompt


def test_enhance_prompt_mentions_topic_relevance():
    prompt = enhance_prompt(
        "Jak się walczy?",
        {"match": "walka", "confidence": 0.7},
        "[1] Strona 1 — Sekcja: Walka\nPrzykładowy tekst"
    )
    assert "najtrafniejszych fragmentów powiązanych z tematem pytania" in prompt
    assert "Nie cytuj fragmentów niepowiązanych tematycznie" in prompt
