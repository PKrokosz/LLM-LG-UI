"""Markdown processing and BM25 retrieval utilities."""

import re
from typing import Dict, List, Tuple

try:
    from rank_bm25 import BM25Okapi
except ModuleNotFoundError:  # pragma: no cover - fallback for optional dependency
    BM25Okapi = None

from .utils import tokenize_for_bm25

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def md_to_pages(md_text: str, page_chars: int = 1400) -> List[Dict]:
    """Convert Markdown into pseudo-pages (~page_chars each)."""
    sections = []
    last_h = {1: None, 2: None, 3: None}
    pos = 0
    blocks: List[Tuple[str, str]] = []

    for m in HEADING_RE.finditer(md_text):
        start, end = m.span()
        if start > pos:
            chunk = md_text[pos:start]
            if chunk.strip():
                section_str = " / ".join(
                    [h for h in [last_h[1], last_h[2], last_h[3]] if h]
                )
                blocks.append((section_str, chunk.strip()))
        hashes, title = m.group(1), m.group(2).strip()
        level = len(hashes)
        if level <= 3:
            last_h[level] = title
            for lv in range(level + 1, 4):
                last_h[lv] = last_h.get(lv, None) and None
        pos = end
    if pos < len(md_text):
        chunk = md_text[pos:]
        if chunk.strip():
            section_str = " / ".join(
                [h for h in [last_h[1], last_h[2], last_h[3]] if h]
            )
            blocks.append((section_str, chunk.strip()))

    pages: List[Dict] = []
    buf = []
    buf_len = 0
    buf_sec = None
    page_no = 1

    def flush():
        nonlocal buf, buf_len, buf_sec, page_no
        if buf_len == 0:
            return
        text = "\n\n".join(buf).strip()
        pages.append({"page": page_no, "section": buf_sec or "", "text": text})
        page_no += 1
        buf, buf_len, buf_sec = [], 0, None

    for sec, blk in blocks:
        # If single block meets or exceeds page limit, split into chunks
        if len(blk) >= page_chars:
            for i in range(0, len(blk), page_chars):
                sub = blk[i : i + page_chars]
                if buf_len > 0:
                    flush()
                buf_sec = sec
                buf.append(sub)
                buf_len = len(sub)
                flush()
            continue
        if not buf_sec:
            buf_sec = sec
        if buf_len + len(blk) > page_chars and buf_len > 0:
            flush()
            buf_sec = sec
        buf.append(blk)
        buf_len += len(blk)
    flush()
    return pages


class BM25Index:
    """Simple BM25 index over pseudo-pages."""

    def __init__(self, pages: List[Dict]):
        if BM25Okapi is None:  # pragma: no cover - dependency guard
            raise ModuleNotFoundError(
                "rank_bm25 is required for BM25Index. Install 'rank_bm25' to use this feature."
            )
        self.pages = pages
        tokenized = [tokenize_for_bm25(p["text"]) for p in pages]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Return top-k matching pages for query."""
        tq = tokenize_for_bm25(query)
        scores = self.bm25.get_scores(tq)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in order:
            p = dict(self.pages[i])
            p["score"] = float(scores[i])
            p["preview"] = (
                p["text"][:600] + ("…" if len(p["text"]) > 600 else "")
            ).replace("\n", " ")
            results.append(p)
        return results
