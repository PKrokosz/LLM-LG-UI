import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src import meta_response


def test_with_introduction_adds_prefix():
    message = "Odpowiedź"
    out = meta_response.with_introduction(message)
    assert out.startswith("Cześć! Jestem Pomocnik Gothic LARP.")
    assert message in out
