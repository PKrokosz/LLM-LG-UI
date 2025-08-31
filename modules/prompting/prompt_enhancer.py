"""Prompt enhancer that injects intent metadata."""
from typing import Dict


def enhance_prompt(question: str, intent: Dict, context: str) -> str:
    """Return prompt with intent metadata and context."""
    intent_line = f"Dopasowane pytanie: {intent.get('match', '')} (pewność {intent.get('confidence', 0):.2f})"
    answer_format = (
        "Udziel odpowiedzi w 2–4 krótkich zdaniach, tylko na podstawie powyższych fragmentów. "
        "Wpleć 1–2 cytaty (≤ 20 słów) z najtrafniejszych części. "
        "Na końcu dodaj: Źródło: Strona X – Sekcja Y."
    )
    return (
        f"Pytanie użytkownika: {question}\n"
        f"{intent_line}\n\n"
        f"Najtrafniejsze fragmenty podręcznika (numerowane):\n{context}\n\n"
        f"{answer_format}\n\n"
        "Instrukcje: Odpowiadaj tylko na podstawie powyższych fragmentów. Jeśli brak odpowiedzi – napisz: 'Nie ma tego w podręczniku.'"
    )
