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
from modules.prompting.prompt_templates import SYSTEM_PROMPT_PL
from modules.logic.trace import emit, save_artifact, prompt_hash
import json

def build_pl_prompt(question: str, contexts, run_id=None):
    joined = "\n\n".join(f"[Cytat #{i+1}]\n{c}" for i, c in enumerate(contexts))
    prompt = f"""{SYSTEM_PROMPT_PL}

[Pytanie]
{question}

[Kontekst]
{joined}

[Instrukcja]
Odpowiedz po polsku, krótko i precyzyjnie. Użyj tylko informacji z [Kontekst].
"""
    if run_id:
        save_artifact(run_id, "prompt.txt", prompt)
        save_artifact(run_id, "context.json", json.dumps(contexts, ensure_ascii=False, indent=2))
        emit(run_id, "prompt.build", template_id="pl_only_from_context",
             prompt_hash=prompt_hash(prompt), tokens_est=len(prompt.split()), context_ids=list(range(1, len(contexts)+1)))
    return prompt


def polish_rewrite(q: str):
  return q.strip()
