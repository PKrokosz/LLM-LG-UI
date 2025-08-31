"""Prompt enhancer that injects intent metadata."""
from typing import Dict


def enhance_prompt(question: str, intent: Dict, context: str) -> str:
    """Return prompt with intent metadata and context."""
    intent_line = f"Dopasowane pytanie: {intent.get('match', '')} (pewność {intent.get('confidence', 0):.2f})"
    answer_format = (
        "FORMAT ODPOWIEDZI (stosuj dokładnie):\n"
        "Odpowiedź: <2–4 krótkie zdania, tylko fakty z najtrafniejszych fragmentów powiązanych z tematem pytania (np. 'walka', 'magia'). Jeśli brak – napisz: 'Nie ma tego w podręczniku.'>\n"
        "Nie cytuj fragmentów niepowiązanych tematycznie (np. alchemii dla pytania o walkę).\n"
        "Cytaty: \"<cytat1>\" ; \"<cytat2>\" (każdy ≤ 20 słów, dosłownie z kontekstu; jeśli masz tylko jeden – podaj jeden)\n"
        "Źródła: [Strona X — Sekcja: Y]; [Strona …]"
    )
    return (
        f"Pytanie użytkownika: {question}\n"
        f"{intent_line}\n\n"
        f"Najtrafniejsze fragmenty podręcznika (numerowane):\n{context}\n\n"
        f"{answer_format}\n\n"
        "Instrukcje: Odpowiadaj tylko na podstawie powyższych fragmentów. Nie wymyślaj, nie dodawaj nic poza formatem."
    )
