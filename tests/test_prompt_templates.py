import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src import prompt_templates


def test_system_prompt_mentions_helper():
    assert "przyjaznym tutorem" in prompt_templates.SYSTEM_PROMPT


def test_fewshot_nonempty():
    assert len(prompt_templates.FEWSHOT_QA) >= 2
