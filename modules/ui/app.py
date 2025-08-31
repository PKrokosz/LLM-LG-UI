"""Gradio application for Markdown-based Q&A."""
from pathlib import Path

import gradio as gr

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


def handle_question(question: str) -> tuple[str, str, str]:
    return answer_question(_get_index(), question)


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

        answer = gr.Markdown(label="Odpowiedź")
        debug_bar = gr.Markdown(label="Debug")
        context = gr.Markdown(label="Źródła i kontekst")

        ask.click(fn=handle_question, inputs=q, outputs=[answer, debug_bar, context])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
