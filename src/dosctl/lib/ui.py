"""User experience and configuration enhancements."""

import json
from pathlib import Path
from typing import Dict, Any

from ..config import get_dosctl_config_dir

DEFAULT_CONFIG = {
    "display": {
        "show_year": True,
        "show_genre": True,
        "progress_bars": True,
        "name_column_width": 80,
        "genre_column_width": 20,
    },
    "ui": {
        "confirm_deletion": True,
        "show_tips": True,
    },
}


class DOSCtlConfig:
    """Enhanced configuration management with user preferences."""

    def __init__(self):
        self.config_dir = Path(get_dosctl_config_dir())
        self.config_file = self.config_dir / "config.json"

        # Check if this is the first run (before loading config)
        self._is_first_run = not self.config_file.exists()
        self._config = self._load_config()

        # Create config file on first run
        if self._is_first_run:
            self._create_initial_config()

    def _load_config(self) -> Dict:
        """Load main configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                # Merge with defaults (preserve user settings, add new defaults)
                return self._merge_configs(DEFAULT_CONFIG, user_config)
            except (json.JSONDecodeError, OSError):
                pass

        return DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _create_initial_config(self):
        """Create initial config file and notify user."""
        self.save_config()
        print("Created configuration file at ~/.config/dosctl/config.json")
        print("Tip: Use 'dosctl config show' to view settings or 'dosctl config set <key> <value>' to customize")

    def save_config(self):
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self._config, f, indent=2)

    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path."""
        keys = path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def _get_valid_config_paths(self) -> set:
        """Get all valid configuration paths from the default config structure."""
        def _extract_paths(config_dict, prefix=""):
            paths = set()
            for key, value in config_dict.items():
                current_path = f"{prefix}.{key}" if prefix else key
                paths.add(current_path)
                if isinstance(value, dict):
                    paths.update(_extract_paths(value, current_path))
            return paths

        return _extract_paths(DEFAULT_CONFIG)

    def set(self, path: str, value: Any):
        """Set configuration value by dot-separated path."""
        # Validate that the path is allowed
        valid_paths = self._get_valid_config_paths()
        if path not in valid_paths:
            # Filter out root-level paths (those without dots) from valid_paths
            full_paths = [p for p in sorted(valid_paths) if '.' in p]

            # Format the error message with proper line breaks and indentation
            suggestion = "\n\nValid paths:\n  " + "\n  ".join(full_paths)
            raise ValueError(f"Invalid configuration path '{path}'.{suggestion}")

        keys = path.split(".")
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()
