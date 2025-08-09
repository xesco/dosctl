"""Utilities for handling DOS game executables."""
from pathlib import Path
from typing import List
from .platform import get_platform

def find_executables(game_path: Path) -> List[str]:
    """Find all executable files in a game directory."""
    platform = get_platform()
    extensions = platform.get_executable_extensions()

    executables = []

    # Use platform-specific extensions
    for ext in extensions:
        # Create case-insensitive patterns for each extension
        patterns = [
            f'**/*.{ext.lower()}',
            f'**/*.{ext.upper()}',
            f'**/*.{ext.capitalize()}'
        ]

        for pattern in patterns:
            executables.extend([e.name for e in game_path.glob(pattern)])

    # Remove duplicates while preserving order
    seen = set()
    unique_executables = []
    for exe in executables:
        if exe.lower() not in seen:
            seen.add(exe.lower())
            unique_executables.append(exe)

    return sorted(unique_executables)

def executable_exists(game_path: Path, executable_name: str) -> bool:
    """Check if an executable exists in the game directory."""
    return (game_path / executable_name).exists()
