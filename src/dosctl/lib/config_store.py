import json
from pathlib import Path
from typing import Optional
from dosctl.config import CONFIG_DIR

CONFIG_FILE = CONFIG_DIR / "run_config.json"

def load_run_config() -> dict:
    """Loads the executable configuration file."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # If the file is corrupted or unreadable, treat it as empty
        return {}

def save_run_config(config: dict) -> None:
    """Saves the executable configuration file."""
    # Ensure the config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except OSError as e:
        # Handle write errors gracefully
        print(f"Warning: Could not save configuration: {e}")

def get_game_command(game_id: str) -> Optional[str]:
    """Gets the saved command for a specific game."""
    config = load_run_config()
    return config.get(game_id)

def set_game_command(game_id: str, command: Optional[str]) -> None:
    """Saves the chosen command for a specific game. If command is None, removes the entry."""
    config = load_run_config()

    if command is None:
        config.pop(game_id, None)  # Remove entry if exists
    else:
        config[game_id] = command

    save_run_config(config)
