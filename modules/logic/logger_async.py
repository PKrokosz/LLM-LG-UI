"""Asynchronous prompt/answer logging using a background thread."""
from __future__ import annotations

import atexit
import queue
import threading
from pathlib import Path


class AsyncLogger:
    """Logger writing entries to disk without blocking the main thread."""

    def __init__(self, path: str = "user_logs/async_log.txt"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.queue: "queue.Queue[str | None]" = queue.Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        atexit.register(self.close)

    def _worker(self) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            while True:
                msg = self.queue.get()
                if msg is None:
                    break
                f.write(msg)
                f.flush()

    def log(self, prompt: str, answer: str) -> None:
        entry = f"PROMPT:\n{prompt}\n\nANSWER:\n{answer}\n" + "-" * 40 + "\n"
        self.queue.put(entry)

    def close(self) -> None:
        self.queue.put(None)
        self.thread.join(timeout=1)


async_logger = AsyncLogger()
