"""LLM client and question answering utilities."""

import time
from typing import Dict, List

import requests

from .config import LLAMA_BASE_URL, LLAMA_MODEL, MAX_TOKENS, STOP, TEMPERATURE
from .retrieval import BM25Index

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


def answer_question(state: Dict, question: str, top_k: int, seed: int):
    """Handle question answering using BM25 retrieval and LLM."""
    if not state or "index" not in state:
        return state, "Najpierw wczytaj podręcznik."

    q_clean = (question or "").strip()
    if len(q_clean) < 3:
        return state, "Doprecyzuj pytanie (np. 'Jak się walczy?')."

    idx: BM25Index = state["index"]
    hits = idx.search(q_clean, k=top_k)
    ctx = format_context(hits)

    answer_format = (
        "FORMAT ODPOWIEDZI (stosuj dokładnie):\n"
        "Odpowiedź: <2–4 krótkie zdania, tylko fakty z kontekstu; jeśli brak – 'Nie ma tego w podręczniku.'>\n"
        "Cytaty: \"<cytat1>\" ; \"<cytat2>\" (każdy ≤ 20 słów, dosłownie z kontekstu; jeśli masz tylko jeden – podaj jeden)\n"
        "Źródła: [Strona X — Sekcja: Y]; [Strona …]"
    )

    user_prompt = (
        f"Pytanie użytkownika: {q_clean}\n\n"
        f"Najtrafniejsze fragmenty podręcznika (numerowane):\n{ctx}\n\n"
        f"{answer_format}\n\n"
        "Instrukcje: Odpowiadaj tylko na podstawie powyższych fragmentów. "
        "Nie wymyślaj, nie dodawaj nic poza formatem."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        start = time.time()
        out = call_llama(messages, seed=seed)
        ms = int((time.time() - start) * 1000)
        debug = (
            "\n\n---\nKontekst użyty do odpowiedzi:\n" + ctx + f"\n\n(LLM {ms} ms)"
        )
        return state, out + (debug if state.get("show_ctx") else "")
    except Exception as e:
        return state, f"Błąd zapytania do LLM: {e}"
