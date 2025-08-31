"""Minimal FAISS stub for testing without external dependency."""
from __future__ import annotations

import numpy as np


class _BaseIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.vecs: np.ndarray | None = None

    def add(self, vecs: np.ndarray) -> None:
        self.vecs = vecs.astype("float32")

    def _search(self, q: np.ndarray, k: int, metric) -> tuple[np.ndarray, np.ndarray]:
        if self.vecs is None:
            return np.zeros((q.shape[0], k)), -np.ones((q.shape[0], k), dtype=int)
        sims = metric(self.vecs, q.T)
        idxs = np.argsort(-sims, axis=0)[:k].T
        scores = np.take_along_axis(sims.T, idxs, axis=1)
        return scores.astype("float32"), idxs.astype("int64")


class IndexFlatL2(_BaseIndex):
    def search(self, q: np.ndarray, k: int):
        metric = lambda a, b: -((a**2).sum(1, keepdims=True) + (b**2).sum(0) - 2 * a @ b)
        return self._search(q, k, metric)


class IndexFlatIP(_BaseIndex):
    def search(self, q: np.ndarray, k: int):
        metric = lambda a, b: a @ b
        return self._search(q, k, metric)


def normalize_L2(x: np.ndarray) -> None:
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    x /= n


def write_index(index: IndexFlatL2, path: str) -> None:
    with open(path, "wb") as f:
        np.save(f, index.vecs)


def read_index(path: str) -> IndexFlatL2:
    with open(path, "rb") as f:
        data = np.load(f)
    idx = IndexFlatL2(data.shape[1])
    idx.add(data)
    return idx
