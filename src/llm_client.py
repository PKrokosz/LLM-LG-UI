"""Wrapper exposing logic.llm_client with patchable hooks for tests."""

from modules.logic import llm_client as _impl
from modules.logic.llm_client import *  # noqa: F401,F403

_log = _impl._log


def answer_question(*args, **kwargs):
    """Proxy to logic.answer_question while respecting local monkeypatches."""
    _impl.call_llama = globals().get("call_llama", _impl.call_llama)
    _impl.parse_intent = globals().get("parse_intent", _impl.parse_intent)
    return _impl.answer_question(*args, **kwargs)

