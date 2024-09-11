from abc import ABC, abstractmethod
from typing import List


# L - Liskov Substitution Principle: Derived classes should be replaceable by their base class (for rewards, searchers, etc.)
class Searcher(ABC):
    search_provider = "google"
    @abstractmethod
    def perform_search(self, query: str) -> List[str]:
        pass

    @abstractmethod
    def perform_batch_search(self, batch_queries: List[str]) -> List[str]:
        pass

