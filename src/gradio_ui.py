"""Enhanced Gradio UI with voice input and quick question tiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import gradio as gr

from .llm_client import answer_question
from .retrieval import BM25Index, md_to_pages
from . import whisper_local

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FREQ_PATH = Path(__file__).resolve().parent.parent / "frequent_questions.json"


def _load_index() -> BM25Index:
    """Build BM25 index from Markdown files in :data:`DATA_DIR`."""
    pages: list[str] = []
    for md_path in DATA_DIR.glob("*.md"):
        pages.extend(md_to_pages(md_path.read_text(encoding="utf-8")))
    return BM25Index(pages)


INDEX = _load_index()


def handle_question(question: str) -> tuple[str, str, str]:
    """Retrieve answer, debug info and context for ``question``."""
    return answer_question(INDEX, question)


def load_frequent_questions() -> Iterable[str]:
    """Load predefined frequent questions from :data:`FREQ_PATH`."""
    if FREQ_PATH.exists():
        return json.loads(FREQ_PATH.read_text(encoding="utf-8"))
    return []


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio input into text using Whisper."""
    return whisper_local.transcribe(audio_path)


def fill_question(text: str) -> str:
    """Utility callback that simply returns provided text."""
    return text


def build_app() -> gr.Blocks:
    """Create Gradio Blocks application with voice and FAQ tiles."""
    with gr.Blocks(css=".gr-textbox textarea {font-size: 14px}") as demo:
        gr.Markdown(
            """
        # 📜 Gothic LARP – Podręcznik Q&A (RAG)
        Wpisz lub nagraj pytanie dotyczące zasad. Aplikacja automatycznie wczytuje pliki Markdown z katalogu `data`.
        """
        )

        q = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jak się walczy?", lines=2)

        with gr.Row():
            audio = gr.Audio(sources=["microphone"], type="filepath", label="🎤")
            transcribe_btn = gr.Button("Transkrybuj")

        with gr.Row():
            for question in load_frequent_questions():
                gr.Button(question).click(fn=lambda x=question: x, inputs=None, outputs=q)

        ask = gr.Button("Zapytaj", variant="primary")
        answer = gr.Markdown(label="Odpowiedź")
        debug_bar = gr.Markdown(label="Debug")
        context = gr.Markdown(label="Źródła i kontekst")

        transcribe_btn.click(transcribe_audio, inputs=audio, outputs=q)
        ask.click(fn=handle_question, inputs=q, outputs=[answer, debug_bar, context])

    return demo


if __name__ == "__main__":  # pragma: no cover - manual launch
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860, inbrowser=False)
