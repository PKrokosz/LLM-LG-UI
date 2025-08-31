import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.intent_embedder import parse_intent


def test_parse_intent_walka():
    res = parse_intent("Jak wygląda walka?")
    assert res["confidence"] > 0.5
    assert "walka" in res["match"].lower()


def test_parse_intent_kradziez():
    res = parse_intent("Co mogę ukraść na larpie?")
    assert res["confidence"] > 0.5
    assert any(sub in res["match"].lower() for sub in ("ukra", "krad"))
