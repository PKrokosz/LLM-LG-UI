import os
import re
import time
import unicodedata
from typing import List, Dict, Tuple

try:
    import gradio as gr
except Exception:  # pragma: no cover - optional dependency
    gr = None
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None

try:
    from rank_bm25 import BM25Okapi
except Exception:  # pragma: no cover - optional dependency
    BM25Okapi = None
try:
    from unidecode import unidecode
except Exception:  # pragma: no cover - optional dependency
    def unidecode(txt: str) -> str:  # type: ignore
        if not isinstance(txt, str):
            return txt
        decomposed = unicodedata.normalize("NFKD", txt)
        return "".join(c for c in decomposed if not unicodedata.combining(c))
from difflib import SequenceMatcher

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
    txt = unicodedata.normalize("NFKC", txt)
    txt = unidecode(txt).lower()
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

def md_to_pages(md_text: str, page_chars: int = 1400) -> List[Dict]:
    last_h = {1: None, 2: None, 3: None}
    pos = 0
    blocks: List[Tuple[str, str]] = []

    for m in HEADING_RE.finditer(md_text):
        start, end = m.span()
        if start > pos:
            chunk = md_text[pos:start]
            if chunk.strip():
                sec = " / ".join([h for h in [last_h[1], last_h[2], last_h[3]] if h])
                blocks.append((sec, chunk.strip()))
        level = len(m.group(1))
        title = m.group(2).strip()
        if level <= 3:
            last_h[level] = title
            for lv in range(level + 1, 4):
                last_h[lv] = None
        pos = end

    if pos < len(md_text):
        chunk = md_text[pos:]
        if chunk.strip():
            sec = " / ".join([h for h in [last_h[1], last_h[2], last_h[3]] if h])
            blocks.append((sec, chunk.strip()))

    pages: List[Dict] = []
    buf: List[str] = []
    buf_len = 0
    buf_sec = None
    page_no = 1

    def flush():
        nonlocal buf, buf_len, buf_sec, page_no
        if buf_len == 0:
            return
        text = "\n\n".join(buf).strip()
        pages.append({"page": page_no, "section": buf_sec or "", "text": text})
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

def tokenize_for_bm25(text: str) -> List[str]:
    text = normalize(text)
    return re.findall(r"[a-z0-9_]+", text)

# -----------------------------
# BM25 index
# -----------------------------
class BM25Index:
    def __init__(self, pages: List[Dict]):
        self.pages = pages
        self.bm25 = BM25Okapi([tokenize_for_bm25(p["text"]) for p in pages])

    def search(self, query: str, k: int = 4) -> List[Dict]:
        tq = tokenize_for_bm25(query)
        scores = self.bm25.get_scores(tq)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in order:
            p = dict(self.pages[i])
            p["score"] = float(scores[i])
            p["preview"] = (p["text"][:700] + ("…" if len(p["text"]) > 700 else "")).replace("\n", " ")
            results.append(p)
        return results

# -----------------------------
# FAQ/Rules Parser (Intent Router)
# -----------------------------
Q_LINE = re.compile(r"^\s*(?:\d+[\).]|[-*])\s*(.+?)\s*$")

def extract_questions_from_md(md_text: str) -> List[str]:
    qs: List[str] = []
    for line in md_text.splitlines():
        m = Q_LINE.match(line)
        if m:
            q = m.group(1)
            if q.endswith("?") or len(q.split()) >= 4:
                qs.append(q.strip())
    # deduplicate
    seen = set(); out = []
    for q in qs:
        key = normalize(q)
        if key not in seen:
            seen.add(key); out.append(q)
    return out

def best_match(question: str, catalog: List[str]) -> Tuple[str, float]:
    qn = normalize(question)
    best_q, best_s = "", 0.0
    for cand in catalog:
        s = SequenceMatcher(None, qn, normalize(cand)).ratio()
        if s > best_s:
            best_q, best_s = cand, s
    return best_q, best_s

KEYWORD_MAP = {
    "walka": ["pojedynki", "punkty zdrowia", "pz", "trafienia", "koniec sceny"],
    "magia": ["mana", "czary", "zwoje", "runy", "rytualy"],
    "alchemia": ["mikstury", "trucizny", "esencje", "receptury"],
    "kradziez": ["krasc", "ukrasc", "przerwa fabularna", "oznakowanie przedmiotow", "fioletowa nalepka", "zielona nalepka"],
    "lowcy": ["karta lowcy", "patroszenie", "noz bezpieczny"],
}

def expand_keywords(q: str) -> str:
    qn = normalize(q)
    extra: List[str] = []
    for key, vals in KEYWORD_MAP.items():
        if key in qn:
            extra += vals
    return q if not extra else f"{q}, " + ", ".join(extra)

# -----------------------------
# Intent parsing
# -----------------------------
INTENT_KEYWORDS = {k: [k] + v for k, v in KEYWORD_MAP.items()}
INTENT_FILES = ["FAQ LARP GOTHIC.md", "rules.md"]


def _detect_intent(text: str) -> str:
    qn = normalize(text)
    for intent, words in INTENT_KEYWORDS.items():
        for w in words:
            if w in qn:
                return intent
    return "inne"


def _build_question_catalog(paths: List[str]) -> Tuple[List[str], Dict[str, str]]:
    catalog: List[str] = []
    intents: Dict[str, str] = {}
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                qs = extract_questions_from_md(f.read())
                for q in qs:
                    catalog.append(q)
                    intents[q] = _detect_intent(q)
    return catalog, intents


QUESTION_CATALOG, QUESTION_INTENTS = _build_question_catalog(INTENT_FILES)


def parse_intent(question: str) -> Dict:
    """Return best matched question and intent for a user query.

    Args:
        question: User provided question.

    Returns:
        Dict with keys: intent (str), match (str), confidence (float 0-1).
    """

    q_expanded = expand_keywords(question)
    intent = _detect_intent(question)
    catalog = (
        [q for q in QUESTION_CATALOG if QUESTION_INTENTS.get(q) == intent]
        if intent != "inne"
        else QUESTION_CATALOG
    )
    match, score = best_match(q_expanded, catalog)
    if intent == "inne" and match:
        intent = QUESTION_INTENTS.get(match, "inne")
    return {
        "intent": intent,
        "match": match,
        "confidence": round(score, 2),
    }

# -----------------------------
# LLM call
# -----------------------------
def call_llama(messages: List[Dict], seed: int = 42) -> str:
    r = requests.post(
        f"{LLAMA_BASE_URL}/v1/chat/completions",
        json={
            "model": LLAMA_MODEL,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "stop": STOP,
            "seed": seed,
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

SYSTEM_PROMPT = (
    "Pisz po polsku. Bądź krótka, konkretna, bez dygresji. "
    "Odpowiadaj TYLKO na podstawie przekazanego kontekstu. "
    "Jeśli w kontekście nie ma odpowiedzi – napisz: 'Nie ma tego w podręczniku.' "
    "Na końcu podaj źródła w formacie: [Strona X — Sekcja: Y]. "
    "Możesz dodać 1 krótki cytat (≤ 12 słów) dokładnie z kontekstu."
)

def format_context(chunks: List[Dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        sec = c.get("section") or "(brak)"
        lines.append(f"[{i}] Strona {c['page']} — Sekcja: {sec}\n{c['preview']}")
    return "\n\n".join(lines)

def build_messages(user_question: str, chunks: List[Dict]) -> List[Dict]:
    ctx = format_context(chunks)
    format_block = (
        "FORMAT ODPOWIEDZI (stosuj dokładnie):\n"
        "Odpowiedź: <2–4 krótkie zdania, tylko fakty z kontekstu; jeśli brak – 'Nie ma tego w podręczniku.'>\n"
        "Cytat: \"<cytat>\" (≤ 12 słów, dosłownie z kontekstu; jeśli brak – pomiń)\n"
        "Źródła: [Strona X — Sekcja: Y]; [Strona …]"
    )
    user = (
        f"Pytanie użytkownika: {user_question}\n\n"
        f"Najtrafniejsze fragmenty podręcznika (numerowane):\n{ctx}\n\n"
        f"{format_block}\n\n"
        "Instrukcje: Odpowiadaj tylko na podstawie powyższych fragmentów. "
        "Nie wymyślaj, nie dodawaj nic poza formatem."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]

# -----------------------------
# QA flow (parser + retrieval + answer)
# -----------------------------
def answer_question(state: Dict, question: str, top_k: int, seed: int,
                    parser_on: bool, parser_thr: float):
    if not state or "index" not in state:
        return state, "Najpierw wczytaj podręcznik.", ""

    q_raw = (question or "").strip()
    if len(q_raw) < 3:
        return state, "Doprecyzuj pytanie (np. 'Jak się walczy?').", ""

    chosen = ""
    score = 0.0
    used_parser = False
    if parser_on and state.get("qbank"):
        chosen, score = best_match(q_raw, state["qbank"])
        used_parser = score >= parser_thr

    base_query = chosen if used_parser else q_raw
    q_enh = expand_keywords(base_query)

    idx: BM25Index = state["index"]
    hits = idx.search(q_enh, k=int(top_k)) or idx.search(q_raw, k=int(top_k))

    try:
        t0 = time.time()
        out_text = call_llama(build_messages(q_raw, hits), seed=int(seed) if seed not in (None, "") else 42)
        ms = int((time.time() - t0) * 1000)
        footer = ""
        if state.get("show_ctx"):
            ctx = format_context(hits)
            router = f"\nRouter: {'HIT' if used_parser else 'MISS'} (score={score:.2f}; canonical='{chosen}')\nZapytanie po rozszerzeniu: {q_enh}"
            footer = f"\n\n---\nKontekst:\n{ctx}{router}\n\n(LLM {ms} ms)"
        return state, out_text + footer, (chosen if used_parser else "")
    except Exception as e:
        return state, f"Błąd zapytania do LLM: {e}", (chosen if used_parser else "")

# -----------------------------
# UI
# -----------------------------
def build_app():
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown(f"""
        # 📜 Gothic LARP – Q&A (RAG++)
        1) Wgraj główny **Markdown** (podręcznik). 2) (Opcjonalnie) wgraj **FAQ/Rules** do parsera.
        3) Zadaj pytanie – dostaniesz krótką odpowiedź z cytatem i źródłami.

        Serwer LLM: `{LLAMA_BASE_URL}`  model: `{LLAMA_MODEL}`
        """)

        with gr.Row():
            md_file = gr.File(label="Podręcznik (Markdown)")
            faq_files = gr.Files(label="FAQ / Rules (opcjonalnie, .md)")

        with gr.Row():
            top_k = gr.Slider(1, 8, value=4, step=1, label="Top-K fragmentów")
            show_ctx = gr.Checkbox(value=True, label="Pokaż użyty kontekst i debug")

        with gr.Row():
            parser_on = gr.Checkbox(value=True, label="Użyj parsera (baza pytań)")
            parser_thr = gr.Slider(0.0, 1.0, value=0.62, step=0.01, label="Próg dopasowania (0–1)")

        status = gr.Markdown(visible=False)
        state = gr.State({})

        q = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jak się walczy?", lines=2)
        with gr.Row():
            seed = gr.Number(value=42, precision=0, label="Seed")
            ask = gr.Button("Zapytaj", variant="primary")
            reset = gr.Button("Reset")

        out = gr.Textbox(label="Odpowiedź", lines=12)
        chosen_intent = gr.Textbox(label="Parser: dopasowane pytanie (kanoniczne)", lines=2)

        def load_md(file_obj, show):
            try:
                if not file_obj:
                    return gr.update(visible=True, value="Wybierz plik .md"), {}
                content = file_obj.decode("utf-8") if isinstance(file_obj, bytes) else open(file_obj.name, "r", encoding="utf-8").read()
                pages = md_to_pages(content)
                idx = BM25Index(pages)
                st = {"index": idx, "pages": pages, "show_ctx": bool(show)}
                return gr.update(visible=True, value=f"Wczytano: {len(pages)} stron (pseudo)."), st
            except Exception as e:
                return gr.update(visible=True, value=f"Błąd wczytywania: {e}"), {}

        def load_faq(files, state):
            try:
                if not files:
                    state.pop("qbank", None)
                    return state, "(Brak bazy pytań)"
                all_qs: List[str] = []
                for f in files:
                    text = f.read().decode("utf-8") if hasattr(f, "read") else open(f.name, "r", encoding="utf-8").read()
                    all_qs += extract_questions_from_md(text)
                # dedup
                seen = set(); uniq = []
                for qq in all_qs:
                    key = normalize(qq)
                    if key not in seen:
                        seen.add(key); uniq.append(qq)
                state["qbank"] = uniq
                return state, f"Baza pytań: {len(uniq)} pozycji"
            except Exception as e:
                state.pop("qbank", None)
                return state, f"Błąd parsowania FAQ/Rules: {e}"

        md_file.change(load_md, inputs=[md_file, show_ctx], outputs=[status, state])
        faq_files.change(load_faq, inputs=[faq_files, state], outputs=[state, status])

        ask.click(
            fn=answer_question,
            inputs=[state, q, top_k, seed, parser_on, parser_thr],
            outputs=[state, out, chosen_intent],
        )

        def do_reset():
            return {}, gr.update(value=""), gr.update(value="")
        reset.click(do_reset, outputs=[state, out, chosen_intent])

    return demo

if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
