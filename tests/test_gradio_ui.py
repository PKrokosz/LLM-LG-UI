"""Smoke tests for Gradio UI helpers."""
from __future__ import annotations

import gradio as gr

from src import gradio_ui


def test_build_app_returns_blocks() -> None:
    """UI builder should return a :class:`gradio.Blocks` instance."""
    app = gradio_ui.build_app()
    assert isinstance(app, gr.Blocks)
