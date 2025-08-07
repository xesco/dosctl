"""Utilities for handling DOS game executables."""
from pathlib import Path
from typing import List

def find_executables(game_path: Path) -> List[str]:
    """Find all executable files in a game directory."""
    executables = []

    # Find .exe files
    executables.extend([e.name for e in game_path.glob('**/*.[eE][xX][eE]')])
    # Find .com files  
    executables.extend([e.name for e in game_path.glob('**/*.[cC][oO][mM]')])
    # Find .bat files
    executables.extend([e.name for e in game_path.glob('**/*.[bB][aA][tT]')])

    return sorted(executables)

def executable_exists(game_path: Path, executable_name: str) -> bool:
    """Check if an executable exists in the game directory."""
    return (game_path / executable_name).exists()
