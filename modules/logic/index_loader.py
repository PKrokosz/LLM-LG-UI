"""Utilities for serializing, loading and caching BM25 and FAISS indexes."""
from __future__ import annotations

import hashlib
import json
import os
import pickle
from pathlib import Path
from typing import Any, Callable, Tuple

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


# ---------------------------------------------------------------------------

def _file_meta(path: str) -> dict:
    """Return sha256 hash and mtime for ``path``."""
    stat = os.stat(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return {"hash": h.hexdigest(), "mtime": stat.st_mtime}


def load_or_build(
    data_path: str,
    builder: Callable[[], Tuple[Any, faiss.Index]],
    *,
    cache_dir: str = "serialized_index",
    bm25_name: str = "bm25.pkl",
    faiss_name: str = "faiss.bin",
    meta_name: str = "meta.json",
) -> Tuple[Any, faiss.Index]:
    """Load indexes from disk if metadata matches ``data_path`` or rebuild.

    Parameters
    ----------
    data_path:
        Source file used to build indexes.
    builder:
        Callable returning ``(bm25_index, faiss_index)`` when rebuild is needed.
    cache_dir:
        Directory where serialized indexes and metadata live.
    """

    cdir = Path(cache_dir)
    bm25_path = cdir / bm25_name
    faiss_path = cdir / faiss_name
    meta_path = cdir / meta_name

    if bm25_path.exists() and faiss_path.exists() and meta_path.exists():
        try:
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            current = _file_meta(data_path)
            if meta == current:
                return load_bm25(str(bm25_path)), load_faiss(str(faiss_path))
        except Exception:  # pragma: no cover - corrupted cache
            pass

    cdir.mkdir(parents=True, exist_ok=True)
    bm25, vec = builder()
    save_bm25(bm25, str(bm25_path))
    save_faiss(vec, str(faiss_path))
    meta = _file_meta(data_path)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f)
    return bm25, vec


__all__ = [
    "save_bm25",
    "load_bm25",
    "save_faiss",
    "load_faiss",
    "load_or_build",
]
