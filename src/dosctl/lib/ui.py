"""User experience and configuration enhancements."""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
import click

from ..config import get_dosctl_config_dir, get_dosctl_cache_dir


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
        default_config = {
            "display": {
                "show_year": True,
                "show_genre": True,
                "progress_bars": True,
                "name_column_width": 80,  # Configurable name column width
                "genre_column_width": 20,  # Configurable genre column width
            },
            "ui": {
                "confirm_deletion": True,
                "show_tips": True,
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)
                # Merge with defaults (preserve user settings, add new defaults)
                return self._merge_configs(default_config, user_config)
            except (json.JSONDecodeError, OSError):
                pass

        return default_config

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
        print("✅ Created configuration file at ~/.config/dosctl/config.json")
        print("💡 Tip: Use 'dosctl config show' to view settings or 'dosctl config set <key> <value>' to customize")

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

        default_config = {
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
        return _extract_paths(default_config)

    def set(self, path: str, value: Any):
        """Set configuration value by dot-separated path."""
        # Validate that the path is allowed
        valid_paths = self._get_valid_config_paths()
        if path not in valid_paths:
            # Create a more helpful error message with better formatting
            common_paths = [
                "display.show_year", "display.show_genre", "display.name_column_width",
                "dosbox.default_cycles", "dosbox.fullscreen",
                "ui.confirm_deletion"
            ]

            # Filter out root-level paths (those without dots) from valid_paths
            full_paths = [p for p in sorted(valid_paths) if '.' in p]

            # Format the error message with proper line breaks and indentation
            suggestion = "\n\nCommon settings:\n  " + "\n  ".join(common_paths)
            suggestion += "\n\nAll valid paths:\n  " + "\n  ".join(full_paths)
            raise ValueError(f"Invalid configuration path '{path}'.{suggestion}")

        keys = path.split(".")
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()


class UserInterface:
    """Enhanced user interface utilities."""

    def __init__(self, config: DOSCtlConfig):
        self.config = config


class UserInterface:
    """Enhanced user interface utilities."""

    def __init__(self, config: DOSCtlConfig):
        self.config = config

    def print_game_table(self, games: List[Dict], show_status: bool = False):
        """Print games in a formatted table."""
        if not games:
            click.echo("No games found.")
            return

        # Determine what columns to show
        show_year = self.config.get("display.show_year", True)
        show_genre = self.config.get("display.show_genre", True)

        # Calculate column widths
        configured_width = self.config.get("display.name_column_width", 80)
        genre_width = self.config.get("display.genre_column_width", 20)
        max_name = max(len(game.get("name", "")) for game in games)
        max_name = min(max_name, configured_width)  # Use configured width

        # Header
        header_parts = [f"{'ID':<8}", f"{'Name':<{max_name}}"]
        if show_year:
            header_parts.append(f"{'Year':<4}")
        if show_status:
            header_parts.append(f"{'Status':<12}")
        if show_genre:
            header_parts.append(f"{'Genre':<{genre_width}}")

        header = " | ".join(header_parts) + " |"  # Add closing pipe
        click.echo(header)
        click.echo("-" * len(header))

        # Games
        for game in games:
            game_id = game.get("id", "unknown")[:8]  # Shorter ID display
            name = game.get("name", "Unknown")[:max_name]
            row_parts = [f"{game_id:<8}", f"{name:<{max_name}}"]

            if show_year:
                year = game.get("year") or "----"  # Handle None gracefully
                row_parts.append(f"{year:<4}")

            if show_status:
                # This would require integration with installation manager
                status = "Unknown"  # Placeholder
                row_parts.append(f"{status:<12}")

            if show_genre:
                # Parse metadata to get genre
                from ..lib.metadata import parse_game_metadata

                metadata = parse_game_metadata(game.get("full_path", ""))
                genre = metadata.get("genre") or "Unknown"
                genre = genre[:genre_width]  # Use configurable width
                row_parts.append(f"{genre:<{genre_width}}")

            click.echo(" | ".join(row_parts) + " |")  # Add closing pipe

        # Add closing line of dashes
        click.echo("-" * len(header))

    def print_game_table_with_scores(self, scored_games: List[Tuple[Dict, float]]):
        """Print games in a formatted table with relevance scores."""
        if not scored_games:
            click.echo("No games found.")
            return

        games = [game for game, score in scored_games]

        # Determine what columns to show
        show_year = self.config.get("display.show_year", True)
        show_genre = self.config.get("display.show_genre", True)

        # Calculate column widths
        configured_width = self.config.get("display.name_column_width", 80)
        genre_width = self.config.get("display.genre_column_width", 20)
        max_name = max(len(game.get("name", "")) for game in games)
        max_name = min(max_name, configured_width)  # Use configured width

        # Header
        header_parts = [f"{'ID':<8}", f"{'Name':<{max_name}}"]
        if show_year:
            header_parts.append(f"{'Year':<4}")
        if show_genre:
            header_parts.append(f"{'Genre':<{genre_width}}")
        header_parts.append(f"{'Score':<5}")  # Add score column

        header = " | ".join(header_parts) + " |"  # Add closing pipe
        click.echo(header)
        click.echo("-" * len(header))

        # Games with scores
        for game, score in scored_games:
            game_id = game.get("id", "unknown")[:8]  # Shorter ID display
            name = game.get("name", "Unknown")[:max_name]
            row_parts = [f"{game_id:<8}", f"{name:<{max_name}}"]

            if show_year:
                year = game.get("year") or "----"  # Handle None gracefully
                row_parts.append(f"{year:<4}")

            if show_genre:
                # Parse metadata to get genre
                from ..lib.metadata import parse_game_metadata

                metadata = parse_game_metadata(game.get("full_path", ""))
                genre = metadata.get("genre") or "Unknown"
                genre = genre[:genre_width]  # Use configurable width
                row_parts.append(f"{genre:<{genre_width}}")

            # Add score
            row_parts.append(f"{score:<5.1f}")

            click.echo(" | ".join(row_parts) + " |")  # Add closing pipe

        # Add closing line of dashes
        click.echo("-" * len(header))

    def print_progress_bar(self, current: int, total: int, description: str = ""):
        """Print a progress bar."""
        if not self.config.get("display.progress_bars", True):
            return

        width = 40
        progress = current / total if total > 0 else 0
        filled = int(width * progress)
        bar = "█" * filled + "░" * (width - filled)
        percent = int(progress * 100)

        status = f"\r{description} [{bar}] {percent}% ({current}/{total})"
        click.echo(status, nl=False)

        if current >= total:
            click.echo()  # New line when complete

    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirm an action with the user."""
        if not self.config.get("ui.confirm_deletion", True):
            return True
        return click.confirm(message, default=default)

    def print_tip(self, tip: str):
        """Print a helpful tip."""
        if self.config.get("ui.show_tips", True):
            click.echo(f"\n💡 Tip: {tip}")


class CommandAliases:
    """Command aliases and shortcuts."""

    ALIASES = {
        "ls": "list",
        "find": "search",
        "play": "run",
        "start": "run",
        "launch": "run",
        "info": "inspect",
        "details": "inspect",
        "remove": "delete",
        "rm": "delete",
        "del": "delete",
        "update": "refresh",
        "sync": "refresh",
    }

    @classmethod
    def resolve_alias(cls, command: str) -> str:
        """Resolve command alias to actual command."""
        return cls.ALIASES.get(command, command)

    @classmethod
    def list_aliases(cls) -> List[Tuple[str, str]]:
        """List all available aliases."""
        return list(cls.ALIASES.items())


def setup_config_command():
    """Create a config command for managing settings."""

    @click.group()
    def config():
        """Manage dosctl configuration."""
        pass

    @config.command()
    @click.argument("key")
    @click.argument("value", required=False)
    def set(key, value):
        """Set a configuration value."""
        config_manager = DOSCtlConfig()

        if value is None:
            # Show current value
            current = config_manager.get(key)
            if current is not None:
                click.echo(f"{key} = {current}")
            else:
                click.echo(f"Configuration key '{key}' not found.")
        else:
            # Set new value (try to parse as JSON for complex types)
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                parsed_value = value

            try:
                config_manager.set(key, parsed_value)
                click.echo(f"Set {key} = {parsed_value}")
            except ValueError as e:
                click.echo(f"❌ Error: {e}", err=True)
                return

    @config.command()
    def show():
        """Show current configuration."""
        config_manager = DOSCtlConfig()
        click.echo(json.dumps(config_manager._config, indent=2))



    return config


def get_system_info() -> Dict:
    """Get system information for diagnostics."""
    info = {
        "os": os.name,
        "platform": os.uname() if hasattr(os, "uname") else "unknown",
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "dosctl_cache_dir": get_dosctl_cache_dir(),
        "dosctl_config_dir": get_dosctl_config_dir(),
    }

    # Check for DOSBox
    dosbox_path = shutil.which("dosbox")
    info["dosbox_available"] = dosbox_path is not None
    info["dosbox_path"] = dosbox_path

    # Check disk space
    try:
        cache_stat = shutil.disk_usage(get_dosctl_cache_dir())
        info["cache_disk_free_gb"] = round(cache_stat.free / (1024**3), 2)
    except OSError:
        info["cache_disk_free_gb"] = "unknown"

    return info
