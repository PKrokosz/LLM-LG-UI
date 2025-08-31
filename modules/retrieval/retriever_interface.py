"""Common interface for retrieval backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class Retriever(ABC):
    """Abstract retrieval backend."""

    @abstractmethod
    def search(self, query: str, k: int = 4) -> List[Dict]:
        """Return top-k documents for query."""
        raise NotImplementedError
