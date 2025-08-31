"""Intent matching using sentence-transformer embeddings."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

try:  # pragma: no cover - dependency may fail without internet
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


class _DummyModel:
    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        dim = 384
        out = np.zeros((len(texts), dim), dtype="float32")
        for i, t in enumerate(texts):
            for tok in t.lower().split():
                out[i, hash(tok) % dim] += 1.0
            n = np.linalg.norm(out[i]) or 1.0
            out[i] /= n
        return out

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
QUESTIONS_FILE = DATA_DIR / "questions.txt"

if SentenceTransformer is not None:
    try:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:  # pragma: no cover - offline fallback
        _model = _DummyModel()
else:  # pragma: no cover - offline fallback
    _model = _DummyModel()

if QUESTIONS_FILE.exists():
    with QUESTIONS_FILE.open("r", encoding="utf-8") as f:
        _QUESTIONS: List[str] = [line.strip() for line in f if line.strip()]
    _EMB = _model.encode(_QUESTIONS, convert_to_numpy=True, show_progress_bar=False)
    _EMB = _EMB / np.linalg.norm(_EMB, axis=1, keepdims=True)
else:  # pragma: no cover - optional
    _QUESTIONS = []
    _EMB = np.zeros((0, 384), dtype="float32")


def parse_intent(question: str) -> Dict[str, float | str]:
    """Return closest catalog question and cosine similarity."""
    if not _QUESTIONS:
        return {"match": "", "confidence": 0.0}
    q_emb = _model.encode([question], convert_to_numpy=True, show_progress_bar=False)
    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)
    sims = (_EMB @ q_emb.T).squeeze(1)
    best_idx = int(np.argmax(sims))
    return {"match": _QUESTIONS[best_idx], "confidence": float(sims[best_idx])}
