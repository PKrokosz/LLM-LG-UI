"""Fallback handling for unanswered queries."""
from typing import Dict, List

FALLBACK_MESSAGE = "Nie wiem."


def should_fallback(hits: List[Dict], min_score: float = 0.1) -> bool:
    """Return True if retrieval hits are insufficient."""
    if not hits:
        return True
    score = hits[0].get("score")
    if score is None:
        return False
    return float(score) < min_score
