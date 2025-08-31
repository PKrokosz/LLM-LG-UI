import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src import response_formatter


def test_weave_quotes_inserts_inline():
    answer = "Walka jest wymagająca."
    quotes = ["W mroku każdy cios jest ryzykiem."]
    out = response_formatter.weave_quotes(answer, quotes)
    assert out.startswith(answer)
    assert "„W mroku każdy cios jest ryzykiem.”" in out
