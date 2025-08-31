"""Vector-based semantic retriever using SentenceTransformers and FAISS."""
from __future__ import annotations

from typing import Dict, List
from .retriever_interface import RetrieverInterface

import faiss
import numpy as np

try:  # pragma: no cover - dependency may fail without internet
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


class _DummyModel:
    """Fallback embedding model based on hashing tokens."""

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        dim = 384
        out = np.zeros((len(texts), dim), dtype="float32")
        for i, t in enumerate(texts):
            for tok in t.lower().split():
                out[i, hash(tok) % dim] += 1.0
            n = np.linalg.norm(out[i]) or 1.0
            out[i] /= n
        return out


class VectorIndex(RetrieverInterface):
    """FAISS index over sentence-transformer embeddings."""

    def __init__(self, pages: List[Dict], model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.pages = pages
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:  # pragma: no cover - offline fallback
                self.model = _DummyModel()
        else:  # pragma: no cover - offline fallback
            self.model = _DummyModel()
        texts = [p["text"] for p in pages]
        embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        faiss.normalize_L2(embs)
        self.dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embs)

    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Return top-k pages most similar to query."""
        q_emb = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
        faiss.normalize_L2(q_emb)
        k = min(k, len(self.pages))
        if k == 0:
            return []
        scores, idx = self.index.search(q_emb, k)
        results: List[Dict] = []
        for rank, i in enumerate(idx[0]):
            p = dict(self.pages[i])
            p["score"] = float(scores[0][rank])
            p["preview"] = (p["text"][:600] + ("…" if len(p["text"]) > 600 else "")).replace("\n", " ")
            results.append(p)
        return results
