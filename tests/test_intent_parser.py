import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gothic_rag_ui_parser import parse_intent, normalize


def test_parse_intent_walka():
    res = parse_intent("Jak wygląda walka?")
    assert res["intent"] == "walka"
    assert 0.0 <= res["confidence"] <= 1.0
    assert "walk" in res["match"].lower()


def test_parse_intent_kradziez():
    res = parse_intent("Co mogę ukraść na larpie?")
    assert res["intent"] == "kradziez"
    match_norm = normalize(res["match"])
    assert any(sub in match_norm for sub in ("krad", "ukra", "krasc"))
