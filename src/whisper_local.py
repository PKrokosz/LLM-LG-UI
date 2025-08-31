"""Utilities for local speech-to-text transcription using Whisper."""
from __future__ import annotations

from typing import Any, Optional
import importlib

_MODEL: Optional[Any] = None


def _get_model(model_name: str) -> Any:
    """Load and cache a Whisper model.

    Parameters
    ----------
    model_name:
        Name of the Whisper model to load.

    Returns
    -------
    Any
        Loaded Whisper model instance.

    Raises
    ------
    RuntimeError
        If the `whisper` package is not installed.
    """
    global _MODEL
    if _MODEL is None:
        try:
            whisper = importlib.import_module("whisper")
        except ModuleNotFoundError as exc:  # pragma: no cover - defensive
            raise RuntimeError("whisper package is required for transcription") from exc
        _MODEL = whisper.load_model(model_name)
    return _MODEL


def transcribe(audio_path: str, model_name: str = "base") -> str:
    """Transcribe speech from an audio file path.

    Parameters
    ----------
    audio_path:
        Path to an audio file supported by Whisper.
    model_name:
        Name of the Whisper model to use. Defaults to ``"base"``.

    Returns
    -------
    str
        Transcribed text or empty string if transcription fails.
    """
    if not audio_path:
        return ""
    model = _get_model(model_name)
    result = model.transcribe(audio_path)
    return result.get("text", "").strip()
