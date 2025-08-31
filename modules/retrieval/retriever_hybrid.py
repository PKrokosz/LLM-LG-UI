"""Hybrid retriever combining BM25 and vector similarity with reranking."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import hashlib
import logging

import faiss
import numpy as np
import yaml

from .retriever_interface import RetrieverInterface
from .retrieval import BM25Index
from .retriever_vector import VectorIndex


log = logging.getLogger(__name__)


def _load_cfg() -> Dict:
    """Load retrieval configuration from ``settings.yaml`` if present."""
    cfg_path = Path(__file__).resolve().parents[2] / "settings.yaml"
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("retrieval", {})
    except Exception:  # pragma: no cover - missing config
        return {}


CFG = _load_cfg()


class HybridRetriever(RetrieverInterface):
    """Combine BM25 and vector search using Reciprocal Rank Fusion + rerank."""

    def __init__(
        self,
        bm25: BM25Index,
        vector: VectorIndex,
        *,
        top_k_bm25: int | None = None,
        top_k_vec: int | None = None,
        k_final: int | None = None,
        max_chunks: int | None = None,
        min_similarity: float | None = None,
    ) -> None:
        self.bm25 = bm25
        self.vector = vector
        self.top_k_bm25 = top_k_bm25 or int(CFG.get("top_k_bm25", 8))
        self.top_k_vec = top_k_vec or int(CFG.get("top_k_vec", 8))
        self.k_final = k_final or int(CFG.get("k_final", 5))
        self.max_chunks = max_chunks or int(CFG.get("max_chunks", 2))
        self.min_similarity = min_similarity if min_similarity is not None else float(
            CFG.get("min_similarity", 0.2)
        )

    def _vector_search(self, q_emb: np.ndarray) -> List[Dict]:
        """Search FAISS index with precomputed query embedding."""
        k = min(self.top_k_vec, len(self.vector.pages))
        if k == 0:
            return []
        scores, idx = self.vector.index.search(q_emb, k)
        results: List[Dict] = []
        for rank, i in enumerate(idx[0]):
            p = dict(self.vector.pages[i])
            p["score"] = float(scores[0][rank])
            results.append(p)
        return results

    def search(self, query: str, k: int | None = None) -> List[Dict]:
        """Return up to ``max_chunks`` reranked results for ``query``."""
        q_emb = self.vector.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        faiss.normalize_L2(q_emb)

        b_res = self.bm25.search(query, self.top_k_bm25)
        v_res = self._vector_search(q_emb)

        rrf_scores: Dict[int, float] = {}
        for rank, res in enumerate(b_res):
            rrf_scores[res["page"]] = rrf_scores.get(res["page"], 0.0) + 1.0 / (60 + rank + 1)
        for rank, res in enumerate(v_res):
            rrf_scores[res["page"]] = rrf_scores.get(res["page"], 0.0) + 1.0 / (60 + rank + 1)

        page_map = {p["page"]: p for p in self.bm25.pages}
        k_final = k or self.k_final
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k_final]

        # Rerank by cosine similarity and remove duplicates/low scores
        scored: List[tuple[float, Dict]] = []
        for page, _ in ranked:
            p = dict(page_map[page])
            emb = self.vector.model.encode([p["text"]], convert_to_numpy=True, show_progress_bar=False)
            faiss.normalize_L2(emb)
            sim = float(np.dot(q_emb[0], emb[0]))
            if sim < self.min_similarity:
                continue
            p["score"] = sim
            p["preview"] = (p["text"][:600] + ("…" if len(p["text"]) > 600 else "")).replace("\n", " ")
            scored.append((sim, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        seen: set[str] = set()
        results: List[Dict] = []
        for sim, p in scored:
            h = hashlib.sha1(p["text"].strip().lower().encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            results.append(p)
            if len(results) >= self.max_chunks:
                break

        log.info("chunks_selected=%d", len(results))
        return results
