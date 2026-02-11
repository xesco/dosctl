"""Discovery code encoding for sharing IP:port as human-friendly codes.

Encodes an IPv4 address + optional port into a short code like DOOM-3KF8A
that can be easily shared verbally or typed. Uses a 256-word list for the
first byte and base36 for the remaining 3 bytes of the IP address.

Default port (19900) is omitted; custom ports are appended as a suffix.

Format:
    Default port:  WORD-NNNNN        (e.g., DOOM-3KF8A)
    Custom port:   WORD-NNNNN-Pxxxx  (e.g., DOOM-3KF8A-P1E4)
"""

import socket
import struct
from pathlib import Path

from .network import DEFAULT_IPX_PORT


def _load_word_list():
    """Load the 256-word list from wordlist.txt.

    The file contains 8 words per line, space-separated.
    Words are loaded in order and mapped to byte values 0-255.
    """
    wordlist_path = Path(__file__).parent / "wordlist.txt"
    words = []
    with open(wordlist_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                words.extend(line.split())
    if len(words) != 256:
        raise RuntimeError(
            "wordlist.txt must contain exactly 256 words, got {}".format(len(words))
        )
    return words


# 256 short, memorable, DOS/gaming-themed words.
# Index maps directly to a byte value (0-255).
WORD_LIST = _load_word_list()

# Reverse lookup: word -> byte value
_WORD_TO_INDEX = {word: i for i, word in enumerate(WORD_LIST)}

# Base36 alphabet
_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _to_base36(n, width):
    """Encode non-negative integer n as a zero-padded base36 string."""
    if n < 0:
        raise ValueError("n must be non-negative")
    chars = []
    for _ in range(width):
        chars.append(_B36[n % 36])
        n //= 36
    if n > 0:
        raise ValueError("Value too large for given width")
    return "".join(reversed(chars))


def _from_base36(s):
    """Decode a base36 string to an integer."""
    n = 0
    for ch in s.upper():
        if ch not in _B36:
            raise ValueError(f"Invalid base36 character: '{ch}'")
        n = n * 36 + _B36.index(ch)
    return n


def encode_discovery_code(ip, port=DEFAULT_IPX_PORT):
    """Encode an IP address and port into a human-friendly discovery code.

    Args:
        ip: IPv4 address string (e.g., "203.0.113.5").
        port: Port number (default: 19900).

    Returns:
        Discovery code string (e.g., "NOVA-00ZH5").
    """
    # Parse IP into 4 bytes
    packed = socket.inet_aton(ip)
    a, b, c, d = struct.unpack("BBBB", packed)

    # First byte -> word, remaining 3 bytes -> base36 (5 digits)
    word = WORD_LIST[a]
    remainder = (b << 16) | (c << 8) | d
    digits = _to_base36(remainder, 5)

    code = "{}-{}".format(word, digits)

    # Append port suffix only if non-default
    if port != DEFAULT_IPX_PORT:
        port_b36 = _to_base36(port, 4)  # 36^4 = 1,679,616 > 65535
        code = "{}-P{}".format(code, port_b36)

    return code


def decode_discovery_code(code):
    """Decode a discovery code back to (ip, port).

    Args:
        code: Discovery code string (e.g., "NOVA-00ZH5" or "NOVA-00ZH5-P1E4").

    Returns:
        Tuple of (ip_string, port_int).

    Raises:
        ValueError: If the code is malformed or contains an unknown word.
    """
    code = code.upper().strip()
    parts = code.split("-")

    if len(parts) < 2 or len(parts) > 3:
        raise ValueError(
            "Invalid discovery code format: expected WORD-NNNNN "
            "or WORD-NNNNN-Pxxxx, got '{}'".format(code)
        )

    word, digits = parts[0], parts[1]

    # Decode word -> first byte
    if word not in _WORD_TO_INDEX:
        raise ValueError("Unknown word in discovery code: '{}'".format(word))
    a = _WORD_TO_INDEX[word]

    # Decode base36 digits -> remaining 3 bytes
    if len(digits) != 5:
        raise ValueError(
            "Invalid digit section: expected 5 characters, got {}".format(len(digits))
        )
    remainder = _from_base36(digits)
    if remainder > 0xFFFFFF:
        raise ValueError("Digit section out of range: {}".format(digits))
    b = (remainder >> 16) & 0xFF
    c = (remainder >> 8) & 0xFF
    d = remainder & 0xFF

    ip = socket.inet_ntoa(struct.pack("BBBB", a, b, c, d))

    # Decode port
    port = DEFAULT_IPX_PORT
    if len(parts) == 3:
        port_part = parts[2]
        if not port_part.startswith("P") or len(port_part) != 5:
            raise ValueError("Invalid port section: '{}'".format(port_part))
        port = _from_base36(port_part[1:])
        if port > 65535:
            raise ValueError("Port out of range: {}".format(port))

    return ip, port


def resolve_host(host_arg, default_port=DEFAULT_IPX_PORT):
    """Resolve a host argument that may be an IP address or a discovery code.

    Args:
        host_arg: Either an IPv4 address string or a discovery code.
        default_port: Port to use if host_arg is a raw IP (not a code).

    Returns:
        Tuple of (ip_string, port_int).

    Raises:
        ValueError: If the argument is neither a valid IP nor a valid code.
    """
    # If it contains a dot, treat as raw IP
    if "." in host_arg:
        # Validate it's a real IP
        try:
            socket.inet_aton(host_arg)
        except OSError:
            raise ValueError("Invalid IP address: '{}'".format(host_arg))
        return host_arg, default_port

    # Otherwise try to decode as discovery code
    return decode_discovery_code(host_arg)
