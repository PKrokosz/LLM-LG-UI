import os
import re
import json
import math
import time
import html
import unicodedata
from typing import List, Dict, Tuple

import gradio as gr
import requests
from rank_bm25 import BM25Okapi
from unidecode import unidecode

# -----------------------------
# Config
# -----------------------------
LLAMA_BASE_URL = os.environ.get("LLAMA_BASE_URL", "http://127.0.0.1:8000")
LLAMA_MODEL = os.environ.get("LLAMA_MODEL", "local")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 384))
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.2))
STOP = ["<|end|>", "</s>", "<|endoftext|>"]

# -----------------------------
# Utils: text processing & chunking
# -----------------------------

def normalize(txt: str) -> str:
    """Lowercase + ASCII fold + basic whitespace squeeze."""
    txt = unicodedata.normalize("NFKC", txt)
    txt = unidecode(txt).lower()
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def md_to_pages(md_text: str, page_chars: int = 1400) -> List[Dict]:
    """Turn a Markdown doc into pseudo-pages (~page_chars each),
    carrying the last seen H1/H2/H3 as section label."""
    # Keep headings, flatten the rest
    sections = []
    last_h = {
        1: None,
        2: None,
        3: None,
    }
    pos = 0
    # Gather blocks with section context
    blocks: List[Tuple[str, str]] = []  # (section_str, block_text)

    for m in HEADING_RE.finditer(md_text):
        start, end = m.span()
        if start > pos:
            chunk = md_text[pos:start]
            if chunk.strip():
                section_str = " / ".join([h for h in [last_h[1], last_h[2], last_h[3]] if h])
                blocks.append((section_str, chunk.strip()))
        hashes, title = m.group(1), m.group(2).strip()
        level = len(hashes)
        if level <= 3:
            last_h[level] = title
            for lv in range(level + 1, 4):
                last_h[lv] = last_h.get(lv, None) and None
        pos = end
    # tail
    if pos < len(md_text):
        chunk = md_text[pos:]
        if chunk.strip():
            section_str = " / ".join([h for h in [last_h[1], last_h[2], last_h[3]] if h])
            blocks.append((section_str, chunk.strip()))

    # Merge blocks into ~page sized pages
    pages: List[Dict] = []
    buf = []
    buf_len = 0
    buf_sec = None
    page_no = 1

    def flush():
        nonlocal buf, buf_len, buf_sec, page_no
        if buf_len == 0:
            return
        text = "\n\n".join(buf).strip()
        pages.append({
            "page": page_no,
            "section": buf_sec or "",
            "text": text,
        })
        page_no += 1
        buf, buf_len, buf_sec = [], 0, None

    for sec, blk in blocks:
        if not buf_sec:
            buf_sec = sec
        if buf_len + len(blk) > page_chars and buf_len > 0:
            flush()
            buf_sec = sec
        buf.append(blk)
        buf_len += len(blk)
    flush()

    return pages


# -----------------------------
# BM25 index
# -----------------------------

def tokenize_for_bm25(text: str) -> List[str]:
    text = normalize(text)
    return re.findall(r"[a-z0-9_]+", text)


class BM25Index:
    def __init__(self, pages: List[Dict]):
        self.pages = pages
        tokenized = [tokenize_for_bm25(p["text"]) for p in pages]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, k: int = 4) -> List[Dict]:
        tq = tokenize_for_bm25(query)
        scores = self.bm25.get_scores(tq)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in order:
            p = dict(self.pages[i])
            p["score"] = float(scores[i])
            # short preview
            p["preview"] = (p["text"][:600] + ("…" if len(p["text"]) > 600 else "")).replace("\n", " ")
            results.append(p)
        return results


# -----------------------------
# LLM call
# -----------------------------

def call_llama(messages: List[Dict], seed: int = 42) -> str:
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


SYSTEM_PROMPT = (
    "Pisz po polsku. Bądź bardzo krótka, rzeczowa i bez dygresji. "
    "Odpowiadaj tylko na podstawie przekazanego kontekstu. "
    "Jeśli w kontekście nie ma odpowiedzi – napisz: 'Nie ma tego w podręczniku.'"
)

    "Pisz po polsku. Bądź krótka, konkretna, bez dygresji. "
    "ZAWSZE podaj źródło jako: [Strona X — Sekcja: Y]. "
    "Wpleć 1–2 krótkie cytaty (<= 20 słów) dokładnie z kontekstu."
)


def format_context(chunks: List[Dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        sec = c.get("section") or "(brak)"
        lines.append(f"[{i}] Strona {c['page']} — Sekcja: {sec}\n{c['preview']}")
    return "\n\n".join(lines)


def answer_question(state: Dict, question: str, top_k: int, seed: int):
    if not state or "index" not in state:
        return state, "Najpierw wczytaj podręcznik."

    q_clean = (question or "").strip()
    if len(q_clean) < 3:
        return state, "Doprecyzuj pytanie (np. 'Jak się walczy?')."

    idx: BM25Index = state["index"]
    hits = idx.search(q_clean, k=top_k)
    ctx = format_context(hits)

    FORMAT = (
        "FORMAT ODPOWIEDZI (stosuj dokładnie):
"
        "Odpowiedź: <2–4 krótkie zdania, tylko fakty z kontekstu; jeśli brak – 'Nie ma tego w podręczniku.'>
"
        "Cytaty: \"<cytat1>\" ; \"<cytat2>\" (każdy ≤ 20 słów, dosłownie z kontekstu; jeśli masz tylko jeden – podaj jeden)
"
        "Źródła: [Strona X — Sekcja: Y]; [Strona …]"
    )

    user_prompt = (
        "Pytanie użytkownika: " + q_clean + "

"
        "Najtrafniejsze fragmenty podręcznika (numerowane):
" + ctx + "

"
        + FORMAT + "

"
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
        debug = "

---
Kontekst użyty do odpowiedzi:
" + ctx + f"

(LLM {ms} ms)"
        return state, out + ("

" + debug if state.get("show_ctx") else "")
    except Exception as e:
        return state, f"Błąd zapytania do LLM: {e}"


# -----------------------------
# Gradio UI
# -----------------------------

def build_app():
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown("""
        # 📜 Gothic LARP – Podręcznik Q&A (RAG)
        1) Wgraj plik **Markdown** z podręcznikiem. 2) Zadaj pytanie. 3) Dostaniesz krótką odpowiedź z odnośnikiem do *strony* i *sekcji*.
        
        Serwer LLM: `{LLAMA_BASE_URL}` model: `{LLAMA_MODEL}`
        """)

        with gr.Row():
            md_file = gr.File(label="Podręcznik (Markdown)")
            top_k = gr.Slider(1, 6, value=3, step=1, label="Ile fragmentów (Top-K)")
            show_ctx = gr.Checkbox(value=True, label="Pokaż użyty kontekst")

        status = gr.Markdown(visible=False)
        state = gr.State({})

        with gr.Row():
            q = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jak się walczy?", lines=2)
        with gr.Row():
            seed = gr.Number(value=42, precision=0, label="Seed")
            ask = gr.Button("Zapytaj", variant="primary")
            reset = gr.Button("Reset")

        out = gr.Textbox(label="Odpowiedź", lines=10)

        def load_md(file_obj, k, show):
            try:
                if not file_obj:
                    return gr.update(visible=True, value="Wybierz plik .md"), gr.update(), {}
                content = file_obj.decode("utf-8") if isinstance(file_obj, bytes) else open(file_obj.name, "r", encoding="utf-8").read()
                pages = md_to_pages(content)
                idx = BM25Index(pages)
                new_state = {"index": idx, "show_ctx": bool(show), "pages": pages}
                msg = f"Wczytano: {len(pages)} stron (pseudo). Top-K={k}."
                return gr.update(visible=True, value=msg), gr.update(), new_state
            except Exception as e:
                return gr.update(visible=True, value=f"Błąd wczytywania: {e}"), gr.update(), {}

        md_file.change(load_md, inputs=[md_file, top_k, show_ctx], outputs=[status, out, state])

        ask.click(
            fn=answer_question,
            inputs=[state, q, top_k, seed],
            outputs=[state, out],
        )

        def do_reset():
            return {}, gr.update(value="")

        reset.click(do_reset, outputs=[state, out])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
