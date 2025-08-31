import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.retrieval import BM25Index, md_to_pages
from src.retriever_vector import VectorIndex
from src.retriever_hybrid import HybridRetriever


@pytest.fixture(scope="session")
def pages():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    rules_path = os.path.join(base_dir, "data", "rules.md")
    with open(rules_path, "r", encoding="utf-8") as f:
        return md_to_pages(f.read())


@pytest.fixture(scope="session")
def vector_index(pages):
    return VectorIndex(pages)


@pytest.fixture(scope="session")
def bm25_index(pages):
    return BM25Index(pages)


def test_vector_search(vector_index):
    res = vector_index.search("Jak się walczy?")
    assert len(res) > 0


def test_hybrid_search(bm25_index, vector_index):
    hybrid = HybridRetriever(bm25_index, vector_index)
    res = hybrid.search("Jak się walczy?")
    assert len(res) > 0
