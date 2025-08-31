"""Fallback behaviours when no relevant citations are found."""
from __future__ import annotations

from typing import List, Dict


def neutral_fallback() -> str:
    """Return a neutral fallback answer."""
    return "Nie wiem."  # friendly yet neutral response


def needs_fallback(hits: List[Dict]) -> bool:
    """Return True if retrieval produced no hits."""
    return len(hits) == 0
