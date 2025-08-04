from abc import ABC, abstractmethod
from typing import List, Dict

class BaseCollection(ABC):
    """
    Abstract base class for a game collection.

    This class defines the interface that all collection backends must implement.
    """

    def __init__(self, source: str):
        """
        Initializes the collection with its source.

        Args:
            source: The location of the collection (e.g., a URL or local path).
        """
        self.source = source

    @abstractmethod
    def load(self) -> None:
        """
        Loads the game data from the source.

        This method is responsible for fetching the raw data and preparing it
        for parsing.
        """
        pass

    @abstractmethod
    def get_games(self) -> List[Dict]:
        """
        Returns a list of all available games.

        Returns:
            A list of dictionaries, where each dictionary represents a game
            and must contain at least an 'id' and 'name'.
        """
        pass

    @abstractmethod
    def get_game_details(self, game_id: str) -> Dict:
        """
        Retrieves detailed information for a single game.

        Args:
            game_id: The unique ID of the game.

        Returns:
            A dictionary containing comprehensive details about the game.
        """
        pass

    @abstractmethod
    def download_game(self, game_id: str, destination: str) -> None:
        """
        Downloads the files for a specific game to a local directory.

        Args:
            game_id: The unique ID of the game to download.
            destination: The local path where the game files should be saved.
        """
        pass
