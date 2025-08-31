"""Tests for the ``whisper_local`` transcription helper."""
from __future__ import annotations

import types
from unittest.mock import MagicMock

from src import whisper_local


def test_transcribe_uses_whisper(monkeypatch, tmp_path):
    """``transcribe`` delegates to the underlying Whisper model."""
    fake_model = MagicMock()
    fake_model.transcribe.return_value = {"text": "hello"}
    fake_whisper = types.SimpleNamespace(load_model=MagicMock(return_value=fake_model))
    monkeypatch.setattr(whisper_local.importlib, "import_module", lambda _: fake_whisper)

    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"data")

    text = whisper_local.transcribe(str(audio))

    assert text == "hello"
    fake_whisper.load_model.assert_called_once_with("base")
    fake_model.transcribe.assert_called_once_with(str(audio))
