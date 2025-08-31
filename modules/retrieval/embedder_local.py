from __future__ import annotations

"""Simple offline-safe text embedder using a bag-of-words representation."""

from collections import Counter
from typing import Iterable, List


class LocalEmbedder:
    """Create vector representations without external dependencies."""

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}

    # ------------------------------------------------------------------
    def fit(self, corpus: Iterable[str]) -> None:
        words = set()
        for doc in corpus:
            words.update(doc.lower().split())
        self.vocab = {w: i for i, w in enumerate(sorted(words))}

    # ------------------------------------------------------------------
    def encode(self, texts: Iterable[str]) -> List[List[int]]:
        vectors: List[List[int]] = []
        for text in texts:
            counts = Counter(text.lower().split())
            vec = [counts.get(w, 0) for w in self.vocab]
            vectors.append(vec)
        return vectors
