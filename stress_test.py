"""Concurrency stress test for log.txt writing."""

import threading
from pathlib import Path
from src.llm_client import _log

LOG_PATH = Path("log.txt")


def worker(i: int) -> None:
    for j in range(20):
        _log(f"prompt-{i}-{j}", f"answer-{i}-{j}")


def main() -> None:
    LOG_PATH.unlink(missing_ok=True)
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("stress test completed")


if __name__ == "__main__":
    main()
