import os
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src import llm_client


class DummyIndex:
    def search(self, query: str, k: int):
        return [
            {"page": 1, "section": "Alchemia", "preview": "a"},
            {"page": 2, "section": "Walka", "preview": "b"},
            {"page": 3, "section": "Smierc", "preview": "c"},
        ]


def test_answer_question_reorders_by_intent(monkeypatch):
    def fake_parse_intent(q):
        return {"match": "walka zasady", "confidence": 0.6}

    monkeypatch.setattr(llm_client, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(llm_client, "call_llama", lambda messages, seed: "Nie ma tego w podręczniku")

    ans, debug, ctx = llm_client.answer_question(DummyIndex(), "Jak się walczy?")
    assert ans == "[Popraw: cytat błędny – mimo obecności kontekstu]"
    assert "Sekcje: 2:Walka, 1:Alchemia, 3:Smierc" in debug
    assert ctx.splitlines()[0].startswith("[1] Strona 2")


def test_answer_question_preserves_order_on_low_conf(monkeypatch):
    def fake_parse_intent(q):
        return {"match": "walka zasady", "confidence": 0.4}

    monkeypatch.setattr(llm_client, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(llm_client, "call_llama", lambda messages, seed: "odp")

    ans, debug, ctx = llm_client.answer_question(DummyIndex(), "Jak się walczy?")
    assert ans.startswith("odp")
    assert ans.endswith("Sekcja Alchemia.")
    assert "Sekcje: 1:Alchemia, 2:Walka, 3:Smierc" in debug
    assert ctx.splitlines()[0].startswith("[1] Strona 1")
