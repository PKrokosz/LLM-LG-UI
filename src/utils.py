"""Utility functions for text normalization and tokenization."""

import re
import unicodedata
from typing import List

from unidecode import unidecode


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
