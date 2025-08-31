"""Anonymised logging of user queries with basic performance metrics."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".llm_lg_ui" / "user_logs"
LOG_DIR = Path(os.getenv("LLM_LG_UI_LOG_DIR", DEFAULT_LOG_DIR))


def log_query(query: str) -> str:
    """Persist query with random UUID and timestamp.

    Returns generated ``request_id`` for correlation.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    request_id = str(uuid.uuid4())
    entry = {
        "uuid": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
    }
    path = LOG_DIR / f"{request_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    return request_id


def log_metrics(request_id: str, *, chunks_selected: int, citations_used: int) -> None:
    """Append latency and retrieval metrics for ``request_id`` entry."""
    path = LOG_DIR / f"{request_id}.json"
    if not path.exists():  # pragma: no cover - missing entry
        return
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    start = datetime.fromisoformat(data["timestamp"])
    latency = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    data.update(
        {
            "latency_ms": latency,
            "chunks_selected": chunks_selected,
            "citations_used": citations_used,
        }
    )
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
