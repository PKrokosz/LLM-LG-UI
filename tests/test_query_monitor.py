import json
from importlib import reload

import modules.logic.query_monitor as qm


def test_query_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_LG_UI_LOG_DIR", str(tmp_path))
    reload(qm)
    req_id = qm.log_query("co to jest?")
    qm.log_metrics(req_id, chunks_selected=3, citations_used=50)
    path = tmp_path / f"{req_id}.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["query"] == "co to jest?"
    assert data["chunks_selected"] == 3
    assert data["citations_used"] == 50
    assert "latency_ms" in data
