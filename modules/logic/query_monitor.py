from __future__ import annotations

"""Anonymised logging of user queries."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".llm_lg_ui" / "user_logs"
LOG_DIR = Path(os.getenv("LLM_LG_UI_LOG_DIR", DEFAULT_LOG_DIR))


def log_query(query: str) -> Path:
    """Persist query with random UUID and timestamp.

    Parameters
    ----------
    query: str
        Raw user question to store.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "uuid": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
    }
    path = LOG_DIR / f"{entry['uuid']}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    return path
