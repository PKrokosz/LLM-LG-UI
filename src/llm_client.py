"""LLM client and question answering utilities."""
from typing import Dict, List, Tuple

import requests

from .config import LLAMA_BASE_URL, LLAMA_MODEL, MAX_TOKENS, STOP, TEMPERATURE
from .intent_parser import parse_intent
from .prompt_enhancer import enhance_prompt
from .retrieval import BM25Index
from .metrics_logger import MetricsLogger
from .query_monitor import log_query

SYSTEM_PROMPT = (
    "Pisz po polsku. Bądź krótka, konkretna, bez dygresji. "
    "Odpowiadaj tylko na podstawie przekazanego kontekstu. "
    "Jeśli w kontekście nie ma odpowiedzi – napisz: 'Nie ma tego w podręczniku.' "
    "ZAWSZE podaj źródło jako: [Strona X — Sekcja: Y]. "
    "Wpleć 1–2 krótkie cytaty (<= 20 słów) dokładnie z kontekstu."
)


def call_llama(messages: List[Dict], seed: int = 42) -> str:
    """Send chat completion request to Llama server."""
    url = f"{LLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": LLAMA_MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stop": STOP,
        "seed": seed,
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


def format_context(chunks: List[Dict]) -> str:
    """Return numbered preview of retrieved context chunks."""
    lines = []
    for i, c in enumerate(chunks, 1):
        sec = c.get("section") or "(brak)"
        lines.append(f"[{i}] Strona {c['page']} — Sekcja: {sec}\n{c['preview']}")
    return "\n\n".join(lines)


def _log(prompt: str, answer: str) -> None:
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write("PROMPT:\n" + prompt + "\n\nANSWER:\n" + answer + "\n" + "-" * 40 + "\n")


def answer_question(idx: BM25Index, question: str, top_k: int = 3, seed: int = 42) -> Tuple[str, str, str]:
    """Handle question answering using BM25 retrieval and LLM."""
    logger = MetricsLogger()
    logger.start()
    log_query(question)

    q_clean = (question or "").strip()
    if len(q_clean) < 3:
        logger.end()
        return "", "Doprecyzuj pytanie (np. 'Jak się walczy?').", ""

    intent = parse_intent(q_clean)
    hits = idx.search(q_clean, k=top_k)
    if intent["confidence"] > 0.5:
        topic_hint = intent["match"].split()[0].lower()
        hits = sorted(
            hits,
            key=lambda h: topic_hint in h.get("section", "").lower(),
            reverse=True,
        )
    ctx = format_context(hits)
    user_prompt = enhance_prompt(q_clean, intent, ctx)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        out = call_llama(messages, seed=seed)
        logger.first_response()
    except Exception as e:  # pragma: no cover - network failure
        out = f"Błąd zapytania do LLM: {e}"
    if "Nie ma tego w podręczniku" in out and "Strona" in ctx:
        out = out.replace(
            "Nie ma tego w podręczniku",
            "[Popraw: cytat błędny – mimo obecności kontekstu]",
        )
    _log(user_prompt, out)
    logger.end()
    parser_info = (
        f"Parser: dopasowano '{intent['match']}' (pewność: {intent['confidence']:.2f})"
    )
    used_sections = ", ".join([f"{h['page']}:{h['section']}" for h in hits])
    debug_bar = f"{parser_info} | Sekcje: {used_sections}"
    return out, debug_bar, ctx
