from __future__ import annotations

"""Utility for logging basic performance metrics."""

import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MetricsRecord:
    """Container for timing information."""

    start_time: float
    first_response_time: float | None = None
    end_time: float | None = None

    @property
    def total_duration(self) -> float | None:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def time_to_first_response(self) -> float | None:
        if self.first_response_time is None:
            return None
        return self.first_response_time - self.start_time


class MetricsLogger:
    """Log start, first response and total duration to a JSONL file."""

    def __init__(self, log_file: str | Path = "metrics.log") -> None:
        self.log_file = Path(log_file)
        self.record: MetricsRecord | None = None

    def start(self) -> None:
        """Mark start time."""
        self.record = MetricsRecord(start_time=time.time())

    def first_response(self) -> None:
        """Mark time of first response if not already set."""
        if self.record and self.record.first_response_time is None:
            self.record.first_response_time = time.time()

    def end(self) -> None:
        """Mark end time and persist record."""
        if not self.record:
            return
        self.record.end_time = time.time()
        self._write_record()

    # ------------------------------------------------------------------
    def _write_record(self) -> None:
        if not self.record:
            return
        data = {
            "start_time": self.record.start_time,
            "first_response_time": self.record.first_response_time,
            "total_duration": self.record.total_duration,
        }
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
