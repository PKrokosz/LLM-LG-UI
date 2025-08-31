"""Utility functions for text normalization and tokenization."""

import re
import unicodedata
from typing import List

try:
    from unidecode import unidecode
except ModuleNotFoundError:  # pragma: no cover - fallback when dependency missing
    def unidecode(text: str) -> str:  # type: ignore[return-type]
        return text


def normalize(txt: str) -> str:
    """Lowercase, ASCII-fold and normalize whitespace."""
    txt = unicodedata.normalize("NFKC", txt)
    txt = unidecode(txt).lower()
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize text for BM25 retrieval."""
    text = normalize(text)
    return re.findall(r"[a-z0-9_]+", text)
