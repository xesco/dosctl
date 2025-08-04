import json
from pathlib import Path
from dosctl.config import CONFIG_DIR

CONFIG_FILE = CONFIG_DIR / "run_config.json"

def load_run_config() -> dict:
    """Loads the executable configuration file."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted, treat it as empty.
        return {}

def save_run_config(config: dict) -> None:
    """Saves the executable configuration file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_game_command(game_id: str) -> str | None:
    """Gets the saved command for a specific game."""
    config = load_run_config()
    return config.get(game_id)

def set_game_command(game_id: str, command: str) -> None:
    """Saves the chosen command for a specific game."""
    config = load_run_config()
    config[game_id] = command
    save_run_config(config)
