"""Gradio application for Markdown-based Q&A."""
from pathlib import Path

import gradio as gr

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


def handle_question(question: str) -> tuple[str, str, str]:
    out, debug_bar, ctx = answer_question(_get_index(), question)
    chunks = ctx.split("\n\n") if ctx else []
    quality = "⚑" if len(chunks) <= 1 else "✓"
    return f"{quality} {out}", debug_bar, ctx


def build_app():
    """Create Gradio Blocks application."""
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown(
            """
        # 📜 Gothic LARP – Podręcznik Q&A (RAG)
        Wpisz pytanie dotyczące zasad. Aplikacja automatycznie wczytuje pliki Markdown z katalogu `data`.
        """
        )

        q = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jak się walczy?", lines=2)
        ask = gr.Button("Zapytaj", variant="primary")

        answer = gr.Markdown(label="TL;DR")
        with gr.Accordion("Z czego to wzięto", open=False):
            context = gr.Markdown(label="Źródła i kontekst")
            debug_bar = gr.Markdown(label="Debug")

        ask.click(fn=handle_question, inputs=q, outputs=[answer, debug_bar, context])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
