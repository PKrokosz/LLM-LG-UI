"""Utilities for serializing and loading BM25 and FAISS indexes."""
from __future__ import annotations

import pickle
from typing import Any

import faiss


def save_bm25(index: Any, path: str) -> None:
    """Persist BM25 index to ``path`` using pickle."""
    with open(path, "wb") as f:
        pickle.dump(index, f)


def load_bm25(path: str) -> Any:
    """Load BM25 index from ``path``."""
    with open(path, "rb") as f:
        return pickle.load(f)


def save_faiss(index: faiss.Index, path: str) -> None:
    """Save FAISS index to ``path``."""
    faiss.write_index(index, path)


def load_faiss(path: str) -> faiss.Index:
    """Load FAISS index from ``path``."""
    return faiss.read_index(path)
