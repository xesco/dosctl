"""Utilities for handling DOS game executables."""

import click
from pathlib import Path
from typing import List, Optional

from .config_store import get_game_command
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
            f"**/*.{ext.lower()}",
            f"**/*.{ext.upper()}",
            f"**/*.{ext.capitalize()}",
        ]

        for pattern in patterns:
            executables.extend(
                [str(e.relative_to(game_path)) for e in game_path.glob(pattern)]
            )

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


def get_or_prompt_command(game_id, game_install_path, command_parts, configure):
    """Get the command to run, prompting if necessary.

    Resolves the executable to run for a game by checking (in order):
    1. --configure flag (forces re-selection)
    2. CLI-provided command parts
    3. Saved command from play_config.json
    4. Auto-detect and prompt user

    Shared by the play and net commands.
    """
    if configure:
        return prompt_for_executable(game_install_path, configure)

    # If user provides command on CLI, use it
    if command_parts:
        return " ".join(command_parts)

    # Check for saved command
    saved_command = get_game_command(game_id)
    if saved_command:
        return saved_command

    # First run - prompt for executable
    click.echo(f"No default executable set for game '{game_id}'. Searching...")
    return prompt_for_executable(game_install_path, configure)


def prompt_for_executable(game_install_path, force_menu=False) -> Optional[str]:
    """Prompt user to select an executable.

    If only one executable is found and force_menu is False, auto-selects it.
    Otherwise shows a numbered menu for the user to choose from.
    """
    executables = find_executables(game_install_path)

    if not executables:
        click.echo(
            "Error: No executables (.exe, .com, .bat) found in the archive.", err=True
        )
        return None

    # If there's only one option and we're not forcing the menu, choose it automatically
    if len(executables) == 1 and not force_menu:
        click.echo(
            f"Found a single executable: '{executables[0]}'. Setting as default."
        )
        return executables[0]

    # Show menu for user selection
    while True:
        menu_items = [
            f"  {i}: {exe_name.upper()}" for i, exe_name in enumerate(executables, 1)
        ]
        click.echo("Please choose one of the following to run:")
        click.echo("\n".join(menu_items))

        choice = click.prompt("Select a file to execute", type=int)
        if 1 <= choice <= len(executables):
            return executables[choice - 1]
        else:
            click.echo("Invalid choice. Please try again.", err=True)
