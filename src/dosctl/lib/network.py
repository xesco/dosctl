"""Network configuration for DOSBox IPX multiplayer."""

import socket
from dataclasses import dataclass
from typing import Optional

from urllib.request import urlopen, Request

DEFAULT_IPX_PORT = 19900


@dataclass
class IPXServerConfig:
    """Configuration for hosting an IPX server.

    Used by the DOSBox launcher to start an IPX server on the given port.
    For internet play, the net command handles UPnP and discovery codes
    separately — the launcher only sees this config.
    """

    port: int = DEFAULT_IPX_PORT

    def to_dosbox_command(self) -> str:
        """Return the IPXNET command to run inside DOSBox."""
        return f"IPXNET STARTSERVER {self.port}"


@dataclass
class IPXClientConfig:
    """Configuration for joining an IPX server.

    The host/port may be a LAN peer or an internet host (resolved from a
    discovery code by the net command before reaching the launcher).
    """

    host: str
    port: int = DEFAULT_IPX_PORT

    def to_dosbox_command(self) -> str:
        """Return the IPXNET command to run inside DOSBox."""
        return f"IPXNET CONNECT {self.host} {self.port}"


def get_local_ip() -> Optional[str]:
    """Best-effort detection of the machine's LAN IP address.

    Uses the UDP socket trick: connect to an external IP without sending data
    to determine which local interface would be used for outbound traffic.
    Returns None if detection fails.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Doesn't actually send anything; just triggers route lookup
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except (OSError, IndexError):
        return None


def get_public_ip(timeout=5):
    """Detect this machine's public IP address via an external service.

    Uses https://api.ipify.org which returns the public IP as plain text.
    Falls back to https://checkip.amazonaws.com if ipify is unreachable.

    Args:
        timeout: Maximum seconds to wait for a response.

    Returns:
        Public IP address string, or None if detection fails.
    """
    services = [
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
    ]

    for url in services:
        try:
            req = Request(url)
            req.add_header("User-Agent", "dosctl")
            response = urlopen(req, timeout=timeout)
            ip = response.read().decode("utf-8").strip()
            response.close()
            # Basic validation: should look like an IPv4 address
            socket.inet_aton(ip)
            return ip
        except Exception:
            continue

    return None
