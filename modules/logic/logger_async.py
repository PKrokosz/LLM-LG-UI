"""Asynchronous logger using background thread."""
from __future__ import annotations

import atexit
import queue
import threading
from pathlib import Path
from typing import Tuple


class AsyncLogger:
    """Logger that writes prompt/answer pairs asynchronously."""

    def __init__(self, path: str | Path = "log.txt") -> None:
        self.path = Path(path)
        self._queue: queue.Queue[Tuple[str, str] | None] = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        atexit.register(self.close)

    def _worker(self) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            while True:
                item = self._queue.get()
                if item is None:
                    break
                prompt, answer = item
                f.write(
                    "PROMPT:\n" + prompt + "\n\nANSWER:\n" + answer + "\n" + "-" * 40 + "\n"
                )
                self._queue.task_done()

    def log(self, prompt: str, answer: str) -> None:
        self._queue.put((prompt, answer))

    def close(self) -> None:
        self._queue.put(None)
        self._thread.join()


_LOGGER: AsyncLogger | None = None


def get_logger() -> AsyncLogger:
    """Return module-level logger instance."""
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = AsyncLogger()
    return _LOGGER
