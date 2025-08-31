"""Gradio application for Markdown-based Q&A."""

from typing import Dict

import gradio as gr

from .config import LLAMA_BASE_URL, LLAMA_MODEL
from .llm_client import answer_question
from .retrieval import BM25Index, md_to_pages


def load_md(file_obj, k, show):
    """Load Markdown file and build BM25 index."""
    try:
        if not file_obj:
            return gr.update(visible=True, value="Wybierz plik .md"), gr.update(), {}
        content = (
            file_obj.decode("utf-8")
            if isinstance(file_obj, bytes)
            else open(file_obj.name, "r", encoding="utf-8").read()
        )
        pages = md_to_pages(content)
        idx = BM25Index(pages)
        new_state = {"index": idx, "show_ctx": bool(show), "pages": pages}
        msg = f"Wczytano: {len(pages)} stron (pseudo). Top-K={k}."
        return gr.update(visible=True, value=msg), gr.update(), new_state
    except Exception as e:
        return gr.update(visible=True, value=f"Błąd wczytywania: {e}"), gr.update(), {}


def do_reset():
    """Reset application state."""
    return {}, gr.update(value="")


def build_app():
    """Create Gradio Blocks application."""
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown(
            f"""
        # 📜 Gothic LARP – Podręcznik Q&A (RAG)
        1) Wgraj plik **Markdown** z podręcznikiem. 2) Zadaj pytanie. 3) Dostaniesz krótką odpowiedź z odnośnikiem do *strony* i *sekcji*.

        Serwer LLM: `{LLAMA_BASE_URL}` model: `{LLAMA_MODEL}`
        """
        )

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

        md_file.change(load_md, inputs=[md_file, top_k, show_ctx], outputs=[status, out, state])
        ask.click(fn=answer_question, inputs=[state, q, top_k, seed], outputs=[state, out])
        reset.click(do_reset, outputs=[state, out])

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
