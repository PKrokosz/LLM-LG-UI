"""Hybrid retriever combining BM25 and vector similarity via reciprocal rank fusion."""
from __future__ import annotations

from typing import Dict, List

from .retrieval import BM25Index
from .retriever_vector import VectorIndex


class HybridRetriever:
    """Combine BM25 and vector search using Reciprocal Rank Fusion."""

    def __init__(self, bm25: BM25Index, vector: VectorIndex):
        self.bm25 = bm25
        self.vector = vector

    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Return fused results from BM25 and vector search."""
        b_res = self.bm25.search(query, k)
        v_res = self.vector.search(query, k)
        rrf_scores: Dict[int, float] = {}
        for rank, res in enumerate(b_res):
            rrf_scores[res["page"]] = rrf_scores.get(res["page"], 0.0) + 1.0 / (60 + rank + 1)
        for rank, res in enumerate(v_res):
            rrf_scores[res["page"]] = rrf_scores.get(res["page"], 0.0) + 1.0 / (60 + rank + 1)
        page_map = {p["page"]: p for p in self.bm25.pages}
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        results: List[Dict] = []
        for page, score in ranked:
            p = dict(page_map[page])
            p["score"] = float(score)
            p["preview"] = (p["text"][:600] + ("…" if len(p["text"]) > 600 else "")).replace("\n", " ")
            results.append(p)
        return results
