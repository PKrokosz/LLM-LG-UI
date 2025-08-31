"""Confidence-based answer gating."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml

SETTINGS_PATH = Path(__file__).resolve().parents[2] / "settings.yaml"
with SETTINGS_PATH.open("r", encoding="utf-8") as f:
    _cfg = yaml.safe_load(f) or {}

THRESHOLD: float = float(_cfg.get("confidence_threshold", 0.0))


def is_confident(hits: List[Dict]) -> bool:
    """Return True if top hit score meets confidence threshold."""
    if not hits:
        return False
    return float(hits[0].get("score", 1.0)) >= THRESHOLD
