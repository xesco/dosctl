"""Multiplayer networking commands for DOS games via IPX."""

import click
import textwrap
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.game import install_game
from dosctl.lib.config_store import set_game_command
from dosctl.lib.executables import executable_exists, get_or_prompt_command
from dosctl.lib.dosbox import is_dosbox_installed, get_dosbox_launcher
from dosctl.lib.network import (
    DEFAULT_IPX_PORT,
    IPXServerConfig,
    IPXClientConfig,
    get_local_ip,
)


def _check_dosbox():
    """Check that DOSBox is installed, print help if not. Returns True if OK."""
    if is_dosbox_installed():
        return True

    help_text = textwrap.dedent("""
        Error: 'dosbox' command not found in your PATH.

        Please install DOSBox. We recommend DOSBox Staging for the best experience.

        To install with Homebrew on macOS:
          brew install dosbox           # For standard DOSBox
          brew install dosbox-staging # For DOSBox Staging (recommended)

        If you install DOSBox Staging, you may need to create a symlink so `dosctl` can find it:
          ln -s "$(brew --prefix dosbox-staging)/bin/dosbox-staging" ~/.local/bin/dosbox
    """)
    click.echo(help_text, err=True)
    return False


def _prepare_game(collection, game_id, command_parts, configure):
    """Install game and resolve executable. Returns (install_path, command) or (None, None)."""
    _, game_install_path = install_game(collection, game_id)
    if not game_install_path:
        return None, None

    chosen_command_str = get_or_prompt_command(
        game_id, game_install_path, command_parts, configure
    )
    if not chosen_command_str:
        return None, None

    # Save the chosen command for future runs
    set_game_command(game_id, chosen_command_str)

    # Validate that the chosen executable exists
    executable_name = chosen_command_str.split()[0]
    if not executable_exists(game_install_path, executable_name):
        click.echo(f"Error: Executable '{executable_name}' not found.", err=True)
        set_game_command(game_id, None)
        return None, None

    return game_install_path, chosen_command_str


def _launch_net_game(game_install_path, chosen_command_str, ipx_config):
    """Launch a game with DOSBox and IPX networking enabled."""
    click.echo(
        f"Starting '{chosen_command_str.upper()}' with DOSBox (IPX networking)..."
    )

    try:
        launcher = get_dosbox_launcher()
        launcher.launch_game(
            game_path=game_install_path,
            command=chosen_command_str,
            ipx=ipx_config,
        )
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "Please ensure DOSBox is installed and available in your system PATH.",
            err=True,
        )
    except Exception as e:
        click.echo(f"Error launching game: {e}", err=True)


@click.group(invoke_without_command=True)
@click.pass_context
def net(ctx):
    """Multiplayer networking commands (IPX over LAN)."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@net.command()
@click.argument("game_id")
@click.argument("command_parts", nargs=-1)
@click.option(
    "-p",
    "--port",
    default=DEFAULT_IPX_PORT,
    type=int,
    show_default=True,
    help="UDP port for the IPX server.",
)
@click.option(
    "-c",
    "--configure",
    is_flag=True,
    default=False,
    help="Force re-selection of the default executable.",
)
@ensure_cache
def host(collection, game_id, command_parts, port, configure):
    """Host a multiplayer game as an IPX server.

    Starts DOSBox with an IPX server so other players on your local network
    can connect. Share your IP address with them so they can join using:

      dosctl net join GAME_ID YOUR_IP
    """
    if not _check_dosbox():
        return

    try:
        game_install_path, chosen_command_str = _prepare_game(
            collection, game_id, command_parts, configure
        )
        if not game_install_path:
            return

        # Show hosting info
        local_ip = get_local_ip()
        click.echo(f"\nHosting IPX server on port {port}.")
        if local_ip:
            click.echo(f"Your local IP appears to be: {local_ip}")
            click.echo(
                f"\nOther players on your network can join with:"
                f"\n  dosctl net join {game_id} {local_ip}"
            )
            if port != DEFAULT_IPX_PORT:
                click.echo(f"  dosctl net join {game_id} {local_ip} --port {port}")
        else:
            click.echo(
                "Could not detect your local IP. "
                "Share your IP address with the other player."
            )
        click.echo()

        ipx_config = IPXServerConfig(port=port)
        _launch_net_game(game_install_path, chosen_command_str, ipx_config)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)


@net.command()
@click.argument("game_id")
@click.argument("host_ip")
@click.argument("command_parts", nargs=-1)
@click.option(
    "-p",
    "--port",
    default=DEFAULT_IPX_PORT,
    type=int,
    show_default=True,
    help="UDP port of the IPX server.",
)
@click.option(
    "-c",
    "--configure",
    is_flag=True,
    default=False,
    help="Force re-selection of the default executable.",
)
@ensure_cache
def join(collection, game_id, host_ip, command_parts, port, configure):
    """Join a multiplayer game as an IPX client.

    Connects to a DOSBox IPX server hosted by another player on your local
    network. You need the host's IP address (shown when they run 'dosctl net host').
    """
    if not _check_dosbox():
        return

    try:
        game_install_path, chosen_command_str = _prepare_game(
            collection, game_id, command_parts, configure
        )
        if not game_install_path:
            return

        click.echo(f"\nConnecting to IPX server at {host_ip}:{port}...")
        click.echo()

        ipx_config = IPXClientConfig(host=host_ip, port=port)
        _launch_net_game(game_install_path, chosen_command_str, ipx_config)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
