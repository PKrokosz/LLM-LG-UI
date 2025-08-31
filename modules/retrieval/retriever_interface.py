"""Common interface for pluggable retrievers."""
from __future__ import annotations

from typing import Dict, List, Protocol


class RetrieverInterface(Protocol):
    """Minimal protocol required by the application retrievers."""

    def search(self, query: str, k: int = 4) -> List[Dict]:  # pragma: no cover - protocol
        """Return top-k results for ``query``."""
        ...


def create_retriever(kind: str, pages: List[Dict]) -> RetrieverInterface:
    """Factory returning retriever backend by name."""
    kind = kind.lower()
    if kind == "bm25":
        from .retrieval import BM25Index

        return BM25Index(pages)
    if kind == "faiss":
        from .retriever_vector import VectorIndex

        return VectorIndex(pages)
    if kind == "hybrid":
        from .retrieval import BM25Index
        from .retriever_vector import VectorIndex
        from .retriever_hybrid import HybridRetriever

        return HybridRetriever(BM25Index(pages), VectorIndex(pages))
    raise ValueError(f"Unknown retriever kind: {kind}")
