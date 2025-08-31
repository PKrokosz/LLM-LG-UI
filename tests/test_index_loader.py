import os
import sys

import faiss

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.index_loader import load_bm25, load_faiss, save_bm25, save_faiss
from src.retrieval import BM25Index, md_to_pages
from src.retriever_vector import VectorIndex


def test_index_serialization(tmp_path):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    rules_path = os.path.join(base_dir, "data", "rules.md")
    with open(rules_path, "r", encoding="utf-8") as f:
        pages = md_to_pages(f.read())
    bm25 = BM25Index(pages)
    vector = VectorIndex(pages)

    bm25_path = tmp_path / "bm25.pkl"
    save_bm25(bm25, bm25_path)
    bm25_loaded = load_bm25(bm25_path)
    assert bm25_loaded.search("Jak się walczy?")

    faiss_path = tmp_path / "vec.bin"
    save_faiss(vector.index, str(faiss_path))
    vec_loaded = load_faiss(str(faiss_path))
    q = vector.model.encode(["Jak się walczy?"], convert_to_numpy=True, show_progress_bar=False)
    faiss.normalize_L2(q)
    scores, idxs = vec_loaded.search(q, 1)
    assert idxs.shape[1] == 1
