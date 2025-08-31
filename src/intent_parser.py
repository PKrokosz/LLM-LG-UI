"""Simple fuzzy intent parser."""
from pathlib import Path
from typing import Dict, List
import unicodedata
import re

from rapidfuzz import process, fuzz
from unidecode import unidecode

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTIONS_FILE = DATA_DIR / "questions.txt"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = unidecode(text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


if QUESTIONS_FILE.exists():
    with QUESTIONS_FILE.open("r", encoding="utf-8") as f:
        _CATALOG: List[str] = [line.strip() for line in f if line.strip()]
else:  # pragma: no cover - file optional
    _CATALOG = []


def parse_intent(question: str) -> Dict[str, float | str]:
    """Return closest question match and confidence score.

    Parameters
    ----------
    question: str
        User provided question.

    Returns
    -------
    dict with keys ``match`` and ``confidence``.
    """
    if not _CATALOG:
        return {"match": "", "confidence": 0.0}
    match, score, _ = process.extractOne(
        question,
        _CATALOG,
        scorer=fuzz.ratio,
        processor=_normalize,
    )
    confidence = float(score) / 100.0
    return {"match": match, "confidence": confidence}
