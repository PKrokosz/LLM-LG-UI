import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.retrieval import BM25Index, md_to_pages


def test_md_to_pages_splits_file():
    md_text = "# T\n\n" + "Lorem ipsum " * 100
    pages = md_to_pages(md_text, page_chars=100)
    assert len(pages) > 1
    assert pages[0]["page"] == 1 and pages[1]["page"] == 2


def test_bm25_index_search_returns_results():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    rules_path = os.path.join(base_dir, "data", "rules.md")
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_text = f.read()
    pages = md_to_pages(rules_text)
    index = BM25Index(pages)
    results = index.search("Jak się walczy?")
    assert len(results) > 0
