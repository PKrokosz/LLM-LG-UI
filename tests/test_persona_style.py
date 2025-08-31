import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src import persona_selector, style_prompting


def test_select_persona_defaults_to_gracz():
    assert "krótko" in persona_selector.select_persona("unknown")


def test_apply_style_for_mg():
    base = "Pytanie"
    out = style_prompting.apply_style(base, "MG")
    assert base in out
    assert "analitycznie" in out
