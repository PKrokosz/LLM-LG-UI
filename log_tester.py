"""Verify integrity of log.txt entries after stress testing."""

import re
from pathlib import Path

LOG_PATH = Path("log.txt")


def check() -> None:
    text = LOG_PATH.read_text(encoding="utf-8")
    prompts = len(re.findall(r"^PROMPT:", text, flags=re.MULTILINE))
    answers = len(re.findall(r"^ANSWER:", text, flags=re.MULTILINE))
    if prompts != answers:
        raise AssertionError(f"Mismatch: {prompts} prompts vs {answers} answers")
    print(f"log entries: {prompts}")


if __name__ == "__main__":
    check()
