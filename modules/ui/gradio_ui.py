from __future__ import annotations

"""Gradio UI with optional debug mode showing full logs."""

from pathlib import Path
import json

import gradio as gr
from modules.logic.trace import trace_run, emit

from modules.logic import debug_mode
from modules.logic.llm_client import answer_question
from modules.retrieval import create_retriever, md_to_pages
from modules.retrieval.retriever_interface import RetrieverInterface

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


_INDEX: RetrieverInterface | None = None


def _load_index() -> RetrieverInterface:
    pages = []
    for md_path in DATA_DIR.glob("*.md"):
        pages.extend(md_to_pages(md_path.read_text(encoding="utf-8")))
    return create_retriever("hybrid", pages)


def _get_index() -> RetrieverInterface:
    global _INDEX
    if _INDEX is None:
        _INDEX = _load_index()
    return _INDEX


def _handle_question_impl(question: str, run_id: str | None = None) -> tuple[str, str, str, str]:
    out, debug_bar, ctx = answer_question(_get_index(), question, run_id=run_id)
    chunks = ctx.split("\n\n") if ctx else []
    quality = "⚑" if len(chunks) <= 1 else "✓"
    tldr = f"{quality} {out}"
    logs = ""
    if debug_mode.is_debug():
        logs = f"PROMPT:\n{question}\n\nRETRIEVAL:\n{ctx}\n\nODPOWIEDŹ:\n{out}"
    return tldr, debug_bar, ctx, logs



def handle_question(question: str, *args, **kw):
    meta = {"app_version": "0.1.0", "model": getattr(kw, "model", None), "settings_hash": "auto", "debug": True}
    with trace_run(meta) as run_id:
        emit(run_id, "ui.input", question_raw=question, user_lang="pl")
        result = _handle_question_impl(question, run_id=run_id, *args, **kw)
        if isinstance(result, tuple) and len(result) >= 1:
            answer = result[0]
        else:
            answer = result
        emit(run_id, "ui.output", answer_len=len(answer or ""))
        return result


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
        answer = gr.Markdown(label="TL;DR")
        with gr.Accordion("Z czego to wzięto", open=False):
            context = gr.Markdown(label="Źródła i kontekst")
            debug_bar = gr.Markdown(label="Debug")
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
