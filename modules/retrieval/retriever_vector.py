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

# --- PL: switch to multilingual E5 embeddings + normalized outputs ---
MODEL_NAME = "intfloat/multilingual-e5-base"
if SentenceTransformer is not None:
    try:
        _emb = SentenceTransformer(MODEL_NAME)
    except Exception:  # pragma: no cover - offline fallback
        _emb = _DummyModel()
else:  # pragma: no cover - offline fallback
    _emb = _DummyModel()

import numpy as _np

def _norm(x):
    return x / (_np.linalg.norm(x, axis=-1, keepdims=True) + 1e-12)

def embed_passages(texts):
    if isinstance(_emb, _DummyModel):
        embs = _emb.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    else:
        embs = _emb.encode([f"passage: {t}" for t in texts], normalize_embeddings=True)
    return _norm(embs)

def embed_query(q):
    if isinstance(_emb, _DummyModel):
        embs = _emb.encode([q], convert_to_numpy=True, show_progress_bar=False)
    else:
        embs = _emb.encode([f"query: {q}"], normalize_embeddings=True)
    return _norm(embs)


class VectorIndex(RetrieverInterface):
    """FAISS index over sentence-transformer embeddings."""

    def __init__(self, pages: List[Dict]):
        self.pages = pages
        texts = [p["text"] for p in pages]
        embs = embed_passages(texts)
        self.dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embs)

    @property
    def model(self):  # pragma: no cover - simple accessor
        return _emb

    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Return top-k pages most similar to query."""
        q_emb = embed_query(query)
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
