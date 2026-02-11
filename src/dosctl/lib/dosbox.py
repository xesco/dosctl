"""DOSBox launcher abstraction."""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from .network import IPXServerConfig, IPXClientConfig
from .platform import PlatformBase, get_platform


class DOSBoxLauncher(ABC):
    """Abstract base class for DOSBox launchers."""

    def __init__(self, platform: PlatformBase):
        self.platform = platform

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this DOSBox variant is available on the system."""
        pass

    @abstractmethod
    def launch_game(self, game_path: Path, command: str, **options) -> None:
        """Launch a game with DOSBox."""
        pass

    def get_executable(self) -> str:
        """Get the DOSBox executable path."""
        executable = self.platform.get_dosbox_executable()
        if not executable:
            raise RuntimeError("DOSBox executable not found")
        return executable


class StandardDOSBoxLauncher(DOSBoxLauncher):
    """Standard DOSBox launcher implementation."""

    def is_available(self) -> bool:
        """Check if DOSBox is available on the system."""
        return self.platform.get_dosbox_executable() is not None

    def launch_game(self, game_path: Path, command: str, **options) -> None:
        """Launch a game with standard DOSBox.

        Options:
            floppy (bool): Also mount game directory as A: drive.
            exit_on_completion (bool): Add 'exit' command after game.
            fullscreen (bool): Launch in fullscreen mode.
            cycles (str): DOSBox CPU cycles setting.
            machine (str): DOSBox machine type.
            ipx (IPXServerConfig | IPXClientConfig): IPX networking config.
                When set, enables IPX and injects the appropriate IPXNET
                command before the game executable.
        """
        executable = self.get_executable()
        ipx_config = options.get("ipx")

        # Build the DOSBox command
        cmd = [executable]

        # If IPX networking is requested, load the IPX config file
        if ipx_config is not None:
            ipx_conf_path = _ensure_ipx_conf()
            cmd.extend(["-conf", str(ipx_conf_path)])

        mount_cmd = self.platform.format_dosbox_mount_command("C", game_path)
        cmd.extend(["-c", mount_cmd])

        # Floppy mode: also mount as A: and start there
        if options.get("floppy", False):
            mount_a_cmd = self.platform.format_dosbox_mount_command("A", game_path)
            cmd.extend(["-c", mount_a_cmd, "-c", "A:"])
        else:
            cmd.extend(["-c", "C:"])

        # Inject the IPXNET command after mounting but before the game exe
        if ipx_config is not None:
            cmd.extend(["-c", ipx_config.to_dosbox_command()])

        # Convert forward slashes to backslashes for DOS path compatibility
        # (DOS uses / as the switch character, not a path separator)
        dos_command = command.replace("/", "\\")

        # If the command references a subdirectory, cd into it first
        # so the game can find its data files via relative paths
        if "\\" in dos_command.split()[0]:
            parts = dos_command.split()[0].rsplit("\\", 1)
            subdir = parts[0]
            exe_name = parts[1]
            # Rebuild command with just the executable name + any original arguments
            args = dos_command.split()[1:]
            dos_command = " ".join([exe_name] + args)
            cmd.extend(["-c", f"CD {subdir}"])

        cmd.extend(["-c", dos_command])

        # Add platform-specific options
        # Don't auto-exit during IPX sessions — players quit manually
        if options.get("exit_on_completion", False) and ipx_config is None:
            cmd.extend(["-c", "exit"])

        if options.get("fullscreen", False):
            cmd.append("-fullscreen")

        # Add cycles if specified
        cycles = options.get("cycles")
        if cycles:
            cmd.extend(["-c", f"cycles {cycles}"])

        # Add machine type if specified
        machine = options.get("machine")
        if machine:
            cmd.extend(["-c", f"machine {machine}"])

        # Launch DOSBox
        popen_kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}

        # Windows-specific options to prevent console window
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        subprocess.Popen(cmd, **popen_kwargs)


def _ensure_ipx_conf() -> Path:
    """Ensure the IPX config file exists and return its path.

    Creates a minimal DOSBox config file that enables IPX networking.
    This file is loaded via -conf and merged with DOSBox's default config.
    """
    from dosctl.config import IPX_CONF_PATH

    if not IPX_CONF_PATH.exists():
        IPX_CONF_PATH.parent.mkdir(parents=True, exist_ok=True)
        IPX_CONF_PATH.write_text("[ipx]\nipx=true\n")

    return IPX_CONF_PATH


def create_dosbox_launcher() -> Optional[DOSBoxLauncher]:
    """Create the best available DOSBox launcher for the current platform."""
    platform = get_platform()

    # For now, we only have the standard launcher
    # In the future, we can add DOSBox-Staging, DOSBox-X, etc.
    launcher = StandardDOSBoxLauncher(platform)

    if launcher.is_available():
        return launcher

    return None


# Singleton instance
_launcher_instance: Optional[DOSBoxLauncher] = None


def get_dosbox_launcher() -> DOSBoxLauncher:
    """Get the DOSBox launcher instance (singleton)."""
    global _launcher_instance
    if _launcher_instance is None:
        _launcher_instance = create_dosbox_launcher()
        if _launcher_instance is None:
            raise RuntimeError("No DOSBox installation found")
    return _launcher_instance


def is_dosbox_available() -> bool:
    """Check if DOSBox is available."""
    try:
        launcher = create_dosbox_launcher()
        return launcher is not None
    except Exception:
        return False


def is_dosbox_installed() -> bool:
    """Check if DOSBox is available on the system."""
    return is_dosbox_available()
