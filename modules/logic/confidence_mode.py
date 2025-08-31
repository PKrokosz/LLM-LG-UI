"""Decide response mode based on retrieval confidence."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.yaml"
CONFIDENCE_THRESHOLD: float = 0.5
if _SETTINGS_PATH.exists():
    with _SETTINGS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        CONFIDENCE_THRESHOLD = float(data.get("confidence_threshold", CONFIDENCE_THRESHOLD))


def should_cite_only(hits: List[Dict], threshold: float = CONFIDENCE_THRESHOLD) -> bool:
    """Return True when only citation should be shown."""
    if not hits:
        return False
    score = hits[0].get("score")
    if score is None:
        return False
    return float(score) < threshold
