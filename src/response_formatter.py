"""Utilities for formatting model responses."""
from typing import List

# H1.3: weave quotes naturally into the answer narrative

def weave_quotes(answer: str, quotes: List[str]) -> str:
    """Return answer with quotes embedded in a natural tone."""
    if quotes:
        quote_text = " ".join(f"„{q}”" for q in quotes)
        return f"{answer} Na kartach podręcznika czytamy: {quote_text}."
    return answer
