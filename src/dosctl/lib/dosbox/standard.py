"""Standard DOSBox launcher implementation."""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

from .base import DOSBoxLauncher
from ..platform.base import PlatformBase


class StandardDOSBoxLauncher(DOSBoxLauncher):
    """Standard DOSBox launcher implementation."""

    def is_available(self) -> bool:
        """Check if DOSBox is available on the system."""
        return self.platform.get_dosbox_executable() is not None

    def launch_game(self, game_path: Path, command: str, **options) -> None:
        """Launch a game with standard DOSBox."""
        executable = self.get_executable()

        # Build the DOSBox command
        mount_cmd = self.platform.format_dosbox_mount_command('C', game_path)

        cmd = [
            executable,
            '-c', mount_cmd,
        ]

        # Floppy mode: also mount as A: and start there
        if options.get('floppy', False):
            mount_a_cmd = self.platform.format_dosbox_mount_command('A', game_path)
            cmd.extend(['-c', mount_a_cmd, '-c', 'A:'])
        else:
            cmd.extend(['-c', 'C:'])

        cmd.extend(['-c', command])

        # Add platform-specific options
        if options.get('exit_on_completion', False):
            cmd.extend(['-c', 'exit'])

        if options.get('fullscreen', False):
            cmd.append('-fullscreen')

        # Add cycles if specified
        cycles = options.get('cycles')
        if cycles:
            cmd.extend(['-c', f'cycles {cycles}'])

        # Add machine type if specified
        machine = options.get('machine')
        if machine:
            cmd.extend(['-c', f'machine {machine}'])

        # Launch DOSBox
        popen_kwargs = {
            'stdout': subprocess.DEVNULL,
            'stderr': subprocess.DEVNULL
        }

        # Windows-specific options to prevent console window
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        subprocess.Popen(cmd, **popen_kwargs)
