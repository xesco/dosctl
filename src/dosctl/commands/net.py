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
    get_public_ip,
    is_cgnat_address,
)
from dosctl.lib.discovery import encode_discovery_code, resolve_host
from dosctl.lib.upnp import UPnPPortMapper


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


def _setup_internet_hosting(port, game_id, public_ip=None, no_upnp=False):
    """Set up internet hosting: UPnP port mapping + public IP + discovery code.

    Args:
        port: UDP port for the IPX server.
        game_id: Game ID (used in the join hint message).
        public_ip: If provided, skip public IP detection and use this IP.
        no_upnp: If True, skip UPnP port mapping entirely.

    Returns:
        UPnPPortMapper instance (or None) for cleanup registration.
    """
    local_ip = get_local_ip()
    mapper = None

    # Step 1: Attempt UPnP port mapping (unless bypassed)
    if no_upnp:
        click.echo("Setting up internet play (UPnP skipped)...")
    else:
        click.echo("Setting up internet play...")
        try:
            mapper = UPnPPortMapper()
            if mapper.discover_gateway():
                if local_ip and mapper.add_port_mapping(port, local_ip):
                    mapper.register_cleanup()
                    if mapper.verify_port_mapping(port):
                        click.echo(
                            f"UPnP: Port mapping added and verified (UDP port {port})."
                        )
                    else:
                        click.echo(
                            f"UPnP: Port mapping added but could not verify "
                            f"(UDP port {port}). It may still work.",
                        )
                else:
                    # Probe for CGNAT: check the router's WAN IP
                    wan_ip = mapper.get_external_ip()
                    if not wan_ip or is_cgnat_address(wan_ip):
                        click.echo(
                            "UPnP: Port mapping failed. Your router appears "
                            "to be behind CGNAT (common with Starlink and "
                            "some ISPs), so port forwarding won't work.\n"
                            "The easiest option is to ask the other player to "
                            "host instead. Alternatively, get a public IP "
                            "add-on from your ISP or use a VPN like Tailscale.",
                            err=True,
                        )
                    else:
                        detail = ""
                        if mapper._last_error:
                            detail = " ({})".format(mapper._last_error)
                        click.echo(
                            f"UPnP: Could not open port{detail}. You may need "
                            f"to manually forward UDP port {port} to "
                            f"{local_ip or 'your machine'} on your router.",
                            err=True,
                        )
                    mapper = None
            else:
                click.echo(
                    f"UPnP: No gateway found. You may need to manually "
                    f"forward UDP port {port} to {local_ip or 'your machine'} "
                    f"on your router.",
                    err=True,
                )
                mapper = None
        except Exception:
            click.echo(
                f"UPnP: Could not automatically open port. You may need to manually "
                f"forward UDP port {port} to {local_ip or 'your machine'} "
                f"on your router.",
                err=True,
            )
            mapper = None

    # Step 2: Detect public IP (use provided IP, or try UPnP, then external service)
    if public_ip:
        click.echo(f"Using provided public IP: {public_ip}")
    else:
        if mapper:
            public_ip = mapper.get_external_ip()
        if not public_ip:
            click.echo("Detecting public IP address...")
            public_ip = get_public_ip()

    # Step 3: Generate and display discovery code
    if public_ip:
        code = encode_discovery_code(public_ip, port)
        click.echo(f"\nHosting IPX server on port {port}.")
        click.echo(f"Your discovery code: {code}")
        click.echo(
            f"\nShare this code with other players. They can join with:"
            f"\n  dosctl net join {game_id} {code}"
        )
    else:
        click.echo(
            "\nCould not detect your public IP address.",
            err=True,
        )
        click.echo(f"Hosting IPX server on port {port}.")
        if local_ip:
            click.echo(f"Your local IP appears to be: {local_ip}")
        click.echo(
            "Share your public IP address with the other player so they can join.",
        )

    click.echo()
    return mapper


@click.group(invoke_without_command=True)
@click.pass_context
def net(ctx):
    """Multiplayer networking commands (IPX over LAN or internet)."""
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
@click.option(
    "-i",
    "--internet",
    is_flag=True,
    default=False,
    help="Enable internet play (UPnP port mapping + discovery code).",
)
@click.option(
    "-I",
    "--public-ip",
    default=None,
    type=str,
    help="Specify your public IP address (skips automatic detection).",
)
@click.option(
    "-U",
    "--no-upnp",
    is_flag=True,
    default=False,
    help="Skip UPnP port mapping (use if port is already forwarded).",
)
@ensure_cache
def host(
    collection, game_id, command_parts, port, configure, internet, public_ip, no_upnp
):
    """Host a multiplayer game as an IPX server.

    Starts DOSBox with an IPX server so other players can connect.

    For LAN play, share your IP address with them:

      dosctl net join GAME_ID YOUR_IP

    For internet play, use the --internet flag to get a discovery code:

      dosctl net host GAME_ID --internet

    If you have already configured port forwarding on your router, you can
    skip UPnP and/or specify your public IP directly:

      dosctl net host GAME_ID --internet --no-upnp --public-ip 203.0.113.5
    """
    if not _check_dosbox():
        return

    # --public-ip and --no-upnp require --internet
    if (public_ip or no_upnp) and not internet:
        click.echo(
            "Error: --public-ip and --no-upnp require the --internet flag.",
            err=True,
        )
        return

    try:
        game_install_path, chosen_command_str = _prepare_game(
            collection, game_id, command_parts, configure
        )
        if not game_install_path:
            return

        if internet:
            _setup_internet_hosting(port, game_id, public_ip=public_ip, no_upnp=no_upnp)
        else:
            # LAN mode: show local IP and join instructions
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

    Connects to a DOSBox IPX server hosted by another player. You can use
    either an IP address or a discovery code:

      dosctl net join GAME_ID 192.168.1.42        # LAN (raw IP)

      dosctl net join GAME_ID DOOM-3KF8A          # Internet (discovery code)
    """
    if not _check_dosbox():
        return

    try:
        # Resolve host_ip: could be a raw IP or a discovery code
        try:
            resolved_ip, resolved_port = resolve_host(host_ip, default_port=port)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            return

        # If the user provided a discovery code, the port embedded in the code
        # takes precedence. If they provided a raw IP, use the --port flag.
        # However, if the user explicitly passed --port with a code, that's
        # ambiguous; we prefer the code's port (unless it's the default).
        if "." not in host_ip and resolved_port != DEFAULT_IPX_PORT:
            # Code had a custom port embedded
            actual_port = resolved_port
        else:
            actual_port = port

        game_install_path, chosen_command_str = _prepare_game(
            collection, game_id, command_parts, configure
        )
        if not game_install_path:
            return

        # Show what we resolved
        if "." not in host_ip:
            click.echo(f"\nResolved discovery code: {resolved_ip}:{actual_port}")

        click.echo(f"Connecting to IPX server at {resolved_ip}:{actual_port}...")
        click.echo()

        ipx_config = IPXClientConfig(host=resolved_ip, port=actual_port)
        _launch_net_game(game_install_path, chosen_command_str, ipx_config)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
