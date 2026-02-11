"""Network configuration for DOSBox IPX multiplayer."""

import socket
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_IPX_PORT = 19900


@dataclass
class IPXServerConfig:
    """Configuration for hosting an IPX server.

    In Phase 2, the host command may resolve to an IPXClientConfig instead
    (connecting to a relay server), so the launcher should accept either type.
    """

    port: int = DEFAULT_IPX_PORT

    def to_dosbox_command(self) -> str:
        """Return the IPXNET command to run inside DOSBox."""
        return f"IPXNET STARTSERVER {self.port}"


@dataclass
class IPXClientConfig:
    """Configuration for joining an IPX server.

    In Phase 2, host/port may point to a relay server rather than a LAN peer.
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
