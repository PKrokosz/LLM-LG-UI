from __future__ import annotations

"""Gradio UI with optional debug mode showing full logs."""

from pathlib import Path
import json

import gradio as gr

from modules.logic import debug_mode
from modules.logic.llm_client import answer_question
from modules.retrieval.retrieval import BM25Index, md_to_pages

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


_INDEX: BM25Index | None = None


def _load_index() -> BM25Index:
    pages = []
    for md_path in DATA_DIR.glob("*.md"):
        pages.extend(md_to_pages(md_path.read_text(encoding="utf-8")))
    return BM25Index(pages)


def _get_index() -> BM25Index:
    global _INDEX
    if _INDEX is None:
        _INDEX = _load_index()
    return _INDEX


def handle_question(question: str) -> tuple[str, str, str, str]:
    out, debug_bar, ctx = answer_question(_get_index(), question)
    logs = ""
    if debug_mode.is_debug():
        logs = f"PROMPT:\n{question}\n\nRETRIEVAL:\n{ctx}\n\nODPOWIEDŹ:\n{out}"
    return out, debug_bar, ctx, logs


def toggle_debug(enabled: bool) -> gr.components.Textbox:
    debug_mode.set_debug(enabled)
    return gr.Textbox.update(visible=enabled)


def load_frequent_questions() -> list[str]:
    """Load predefined frequent questions from JSON file."""
    fq_path = Path(__file__).resolve().parents[2] / "frequent_questions.json"
    try:
        data = json.loads(fq_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    return data.get("questions", [])


def ask_frequent(question: str) -> tuple[gr.Update, str, str, str, str]:
    """Handle button click for a predefined question."""
    out, debug_bar, ctx, logs = handle_question(question)
    return gr.Textbox.update(value=question), out, debug_bar, ctx, logs


def build_app():
    """Create Gradio Blocks application with debug toggle."""
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown(
            """
        # 📜 Gothic LARP – Podręcznik Q&A (RAG)
        Wpisz pytanie dotyczące zasad. Aplikacja automatycznie wczytuje pliki Markdown z katalogu `data`.
        """
        )

        q = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jak się walczy?", lines=2)
        answer = gr.Markdown(label="Odpowiedź")
        debug_bar = gr.Markdown(label="Debug")
        context = gr.Markdown(label="Źródła i kontekst")
        logs = gr.Textbox(label="Pełne logi", lines=10, visible=False)

        with gr.Row():
            for q_text in load_frequent_questions():
                gr.Button(q_text).click(
                    lambda qt=q_text: ask_frequent(qt),
                    outputs=[q, answer, debug_bar, context, logs],
                )

        debug_toggle = gr.Checkbox(label="Tryb debug", value=False)
        ask = gr.Button("Zapytaj", variant="primary")

        debug_toggle.change(fn=toggle_debug, inputs=debug_toggle, outputs=logs)
        ask.click(fn=handle_question, inputs=q, outputs=[answer, debug_bar, context, logs])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
