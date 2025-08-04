from abc import ABC, abstractmethod
from typing import List, Dict

class BaseCollection(ABC):
    """
    Abstract base class for a game collection.
    """
    def __init__(self, source: str):
        self.source = source

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def get_games(self) -> List[Dict]:
        pass

    @abstractmethod
    def download_game(self, game_name: str, destination: str) -> None:
        pass
