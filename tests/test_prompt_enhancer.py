import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.prompt_enhancer import enhance_prompt


def test_enhance_prompt_mentions_topic_relevance():
    prompt = enhance_prompt(
        "Jak się walczy?",
        {"match": "walka", "confidence": 0.7},
        "[1] Strona 1 — Sekcja: Walka\nPrzykładowy tekst"
    )
    assert "Wpleć 1–2 cytaty" in prompt
    assert "Źródło: Strona X – Sekcja Y" in prompt
