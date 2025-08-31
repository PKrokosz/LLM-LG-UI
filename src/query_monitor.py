from __future__ import annotations

"""Anonymised logging of user queries."""

import json
import uuid
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "user_logs"


def log_query(query: str) -> Path:
    """Persist query with random UUID and timestamp.

    Parameters
    ----------
    query: str
        Raw user question to store.
    """
    LOG_DIR.mkdir(exist_ok=True)
    entry = {
        "uuid": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "query": query,
    }
    path = LOG_DIR / f"{entry['uuid']}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    return path
