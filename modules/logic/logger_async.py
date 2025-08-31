"""Asynchronous logger with rotating file handler and request correlation."""
from __future__ import annotations

import atexit
import logging
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Queue


class AsyncLogger:
    """Queue-based logger writing to rotating files."""

    def __init__(
        self,
        path: str = "user_logs/async_log.txt",
        *,
        max_bytes: int = 5 * 1024 * 1024,
        backup_count: int = 10,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.queue: Queue = Queue()
        handler = RotatingFileHandler(
            self.path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fmt = logging.Formatter("%(asctime)s [%(request_id)s] %(message)s")
        handler.setFormatter(fmt)

        self.logger = logging.getLogger("async_logger")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(QueueHandler(self.queue))

        self.listener = QueueListener(self.queue, handler)
        self.listener.start()
        atexit.register(self.close)

    def log(self, prompt: str, answer: str, request_id: str) -> None:
        entry = f"PROMPT:\n{prompt}\n\nANSWER:\n{answer}\n" + "-" * 40
        self.logger.info(entry, extra={"request_id": request_id})

    def close(self) -> None:
        self.listener.stop()


async_logger = AsyncLogger()
