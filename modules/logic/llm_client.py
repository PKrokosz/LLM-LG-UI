"""LLM client and question answering utilities."""
from typing import Dict, List, Tuple

import requests
from modules.logic.trace import emit, save_artifact


def _trace_llm_request(cfg):
    emit(cfg.get("run_id"), "llm.request",
         model=cfg.get("MODEL"), temperature=cfg.get("TEMP"),
         max_tokens=cfg.get("MAX_NEW_TOKENS"), stop=cfg.get("STOP"))


def _trace_llm_response(run_id, text, finish_reason="stop", latency_ms=None):
    emit(run_id, "llm.response", finish_reason=finish_reason, latency_ms=latency_ms)
    save_artifact(run_id, "response.txt", text or "")


from .config import LLAMA_BASE_URL, LLAMA_MODEL, MAX_TOKENS, STOP, TEMPERATURE
from .intent_embedder import parse_intent
from modules.prompting.prompt_enhancer import enhance_prompt
from modules.prompting.response_formatter import weave_quotes
from modules.retrieval.retriever_interface import RetrieverInterface
from .metrics_logger import MetricsLogger
from .query_monitor import log_metrics, log_query
from .logger_async import async_logger
from .fallback_logic import neutral_fallback, needs_fallback
from .confidence_mode import is_confident

SYSTEM_PROMPT = (
    "Jesteś przyjaznym tutorem dla nowego gracza. Pisz po polsku, krótko i konkretnie. "
    "Odpowiadaj tylko na podstawie przekazanego kontekstu. "
    "Jeśli w kontekście nie ma odpowiedzi – napisz: 'Nie ma tego w podręczniku.'"
)


def _extract_quotes(hits: List[Dict], limit: int = 2) -> List[str]:
    """Return up to ``limit`` short quotes from retrieval hits."""
    quotes: List[str] = []
    for h in hits[:limit]:
        text = (h.get("preview") or "").strip()
        if not text:
            continue
        words = text.split()
        quotes.append(" ".join(words[:20]))
    return quotes


def _paraphrase_if_echo(answer: str, question: str, seed: int) -> str:
    """Paraphrase ``answer`` if it repeats ``question``."""
    if question and question.lower() in answer.lower():
        messages = [
            {"role": "system", "content": "Parafrazuj odpowiedź po polsku, bez powtarzania pytania."},
            {"role": "user", "content": answer},
        ]
        try:
            return call_llama(messages, seed=seed)
        except Exception:  # pragma: no cover - network failure
            return answer
    return answer


def call_llama(messages: List[Dict], seed: int = 42, run_id: str | None = None) -> str:
    """Send chat completion request to Llama server."""
    import time as _t
    url = f"{LLAMA_BASE_URL}/v1/chat/completions"
    payload = {
        "model": LLAMA_MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stop": STOP,
        "seed": seed,
    }
    _trace_llm_request({"run_id": run_id, "MODEL": LLAMA_MODEL, "TEMP": TEMPERATURE,
                        "MAX_NEW_TOKENS": MAX_TOKENS, "STOP": STOP})
    __t = _t.time()
    r = requests.post(url, json=payload, timeout=120)
    __lat = int((_t.time() - __t) * 1000)
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"].strip()
    try:
        finish_reason = data.get("choices", [{}])[0].get("finish_reason", "stop")
        _trace_llm_response(run_id, text, finish_reason, __lat)
    except Exception:
        _trace_llm_response(run_id, text, "stop", __lat)
    return text


def format_context(chunks: List[Dict]) -> str:
    """Return numbered preview of retrieved context chunks."""
    lines = []
    for i, c in enumerate(chunks, 1):
        sec = c.get("section") or "(brak)"
        lines.append(f"[{i}] Strona {c['page']} — Sekcja: {sec}\n{c['preview']}")
    return "\n\n".join(lines)



def answer_question(idx: RetrieverInterface, question: str, top_k: int = 3, seed: int = 42, run_id: str | None = None) -> Tuple[str, str, str]:
    """Handle question answering using retrieval and LLM."""
    logger = MetricsLogger()
    logger.start()
    request_id = log_query(question)

    q_clean = (question or "").strip()
    if len(q_clean) < 3:
        logger.end()
        return "", "Doprecyzuj pytanie (np. 'Jak się walczy?').", ""

    intent = parse_intent(q_clean)
    hits = idx.search(q_clean, k=top_k, run_id=run_id) if run_id else idx.search(q_clean, k=top_k)
    quotes = _extract_quotes(hits)
    if needs_fallback(hits):
        logger.end()
        return neutral_fallback(), "Brak dopasowań.", ""
    if intent["confidence"] >= 0.5:
        topic_hint = intent["match"].split()[0].lower()
        hits = sorted(
            hits,
            key=lambda h: topic_hint in h.get("section", "").lower(),
            reverse=True,
        )
    ctx = format_context(hits)
    if not is_confident(hits):
        logger.end()
        return "Nie jestem pewien. Oto znalezione cytaty:", "", ctx
    user_prompt = enhance_prompt(q_clean, intent, ctx)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        try:
            llm_out = call_llama(messages, seed=seed, run_id=run_id)
        except TypeError:
            llm_out = call_llama(messages, seed=seed)
        logger.first_response()
    except Exception as e:  # pragma: no cover - network failure
        llm_out = f"Błąd zapytania do LLM: {e}"

    if "nie ma tego w podręczniku" in llm_out.lower() and ctx.strip():
        final_ans = "[Popraw: cytat błędny – mimo obecności kontekstu]"
    else:
        llm_out = _paraphrase_if_echo(llm_out, q_clean, seed)
        final_ans = weave_quotes(llm_out, quotes)
        src = hits[0]
        sec = src.get("section") or "(brak)"
        final_ans = f"{final_ans} Źródło: Strona {src['page']} – Sekcja {sec}."

    async_logger.log(user_prompt, final_ans, request_id)
    logger.end()
    citations_ratio = int(len(quotes) / len(hits) * 100) if hits else 0
    log_metrics(request_id, chunks_selected=len(hits), citations_used=citations_ratio)
    parser_info = (
        f"Parser: dopasowano '{intent['match']}' (pewność: {intent['confidence']:.2f})"
    )
    used_sections = ", ".join([f"{h['page']}:{h['section']}" for h in hits])
    debug_bar = f"{parser_info} | Sekcje: {used_sections}"
    return final_ans, debug_bar, ctx
