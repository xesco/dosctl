"""Tests for discovery code encode/decode."""

import pytest
from dosctl.lib.network import DEFAULT_IPX_PORT
from dosctl.lib.discovery import (
    WORD_LIST,
    _WORD_TO_INDEX,
    _to_base36,
    _from_base36,
    encode_discovery_code,
    decode_discovery_code,
    resolve_host,
)


class TestWordList:
    """Test the word list integrity."""

    def test_word_list_has_256_entries(self):
        assert len(WORD_LIST) == 256

    def test_word_list_no_duplicates(self):
        assert len(set(WORD_LIST)) == 256

    def test_all_words_are_uppercase(self):
        for word in WORD_LIST:
            assert word == word.upper(), f"Word '{word}' is not uppercase"

    def test_reverse_lookup_matches(self):
        for i, word in enumerate(WORD_LIST):
            assert _WORD_TO_INDEX[word] == i


class TestBase36:
    """Test base36 encode/decode helpers."""

    def test_zero(self):
        assert _to_base36(0, 5) == "00000"

    def test_roundtrip(self):
        for n in [0, 1, 42, 255, 1000, 0xFFFFFF]:
            encoded = _to_base36(n, 5)
            assert _from_base36(encoded) == n

    def test_max_3_bytes(self):
        """3 bytes max value (16777215) should fit in 5 base36 digits."""
        encoded = _to_base36(0xFFFFFF, 5)
        assert _from_base36(encoded) == 0xFFFFFF

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            _to_base36(-1, 5)

    def test_overflow_raises(self):
        """Value too large for the given width should raise."""
        with pytest.raises(ValueError):
            _to_base36(36**5, 5)  # One more than max

    def test_invalid_char_raises(self):
        with pytest.raises(ValueError):
            _from_base36("!!!")


class TestEncodeDiscoveryCode:
    """Test encoding IP:port to discovery code."""

    def test_default_port_format(self):
        """Default port should produce WORD-NNNNN format (no port suffix)."""
        code = encode_discovery_code("10.0.0.1")
        parts = code.split("-")
        assert len(parts) == 2
        assert parts[0] in WORD_LIST
        assert len(parts[1]) == 5

    def test_custom_port_format(self):
        """Custom port should produce WORD-NNNNN-Pxxxx format."""
        code = encode_discovery_code("10.0.0.1", port=20000)
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[0] in WORD_LIST
        assert len(parts[1]) == 5
        assert parts[2].startswith("P")
        assert len(parts[2]) == 5  # "P" + 4 base36 digits

    def test_first_byte_maps_to_word(self):
        """First byte of IP should determine the word."""
        # 10.x.x.x -> byte 10 -> WORD_LIST[10] = "BUZZ"
        code = encode_discovery_code("10.0.0.1")
        assert code.startswith("BUZZ-") or code.split("-")[0] == WORD_LIST[10]

    def test_192_168_prefix(self):
        """192.168.x.x IPs should all start with the same word."""
        code1 = encode_discovery_code("192.168.1.1")
        code2 = encode_discovery_code("192.168.0.100")
        word1 = code1.split("-")[0]
        word2 = code2.split("-")[0]
        assert word1 == word2
        assert word1 == WORD_LIST[192]

    def test_different_ips_different_codes(self):
        code1 = encode_discovery_code("10.0.0.1")
        code2 = encode_discovery_code("10.0.0.2")
        assert code1 != code2

    def test_same_ip_different_ports_different_codes(self):
        code1 = encode_discovery_code("10.0.0.1", port=19900)
        code2 = encode_discovery_code("10.0.0.1", port=20000)
        assert code1 != code2


class TestDecodeDiscoveryCode:
    """Test decoding discovery code back to IP:port."""

    def test_default_port(self):
        ip, port = decode_discovery_code("BUZZ-00001")
        assert port == DEFAULT_IPX_PORT

    def test_case_insensitive(self):
        """Codes should be case-insensitive."""
        code = encode_discovery_code("10.0.0.1")
        ip1, port1 = decode_discovery_code(code.upper())
        ip2, port2 = decode_discovery_code(code.lower())
        assert ip1 == ip2
        assert port1 == port2

    def test_strips_whitespace(self):
        code = encode_discovery_code("10.0.0.1")
        ip, port = decode_discovery_code("  " + code + "  ")
        assert ip == "10.0.0.1"

    def test_unknown_word_raises(self):
        with pytest.raises(ValueError, match="Unknown word"):
            decode_discovery_code("ZZZZZ-00001")

    def test_wrong_digit_length_raises(self):
        with pytest.raises(ValueError, match="5 characters"):
            decode_discovery_code("BUZZ-001")

    def test_too_many_parts_raises(self):
        with pytest.raises(ValueError, match="Invalid discovery code"):
            decode_discovery_code("BUZZ-00001-P1234-EXTRA")

    def test_too_few_parts_raises(self):
        with pytest.raises(ValueError, match="Invalid discovery code"):
            decode_discovery_code("BUZZ")

    def test_invalid_port_section_raises(self):
        with pytest.raises(ValueError, match="Invalid port section"):
            decode_discovery_code("BUZZ-00001-X1234")

    def test_invalid_port_length_raises(self):
        with pytest.raises(ValueError, match="Invalid port section"):
            decode_discovery_code("BUZZ-00001-P12")


class TestRoundTrip:
    """Test encode -> decode round-trips."""

    def test_basic_roundtrip(self):
        ip, port = "203.0.113.5", DEFAULT_IPX_PORT
        code = encode_discovery_code(ip, port)
        decoded_ip, decoded_port = decode_discovery_code(code)
        assert decoded_ip == ip
        assert decoded_port == port

    def test_roundtrip_custom_port(self):
        ip, port = "10.0.0.1", 20000
        code = encode_discovery_code(ip, port)
        decoded_ip, decoded_port = decode_discovery_code(code)
        assert decoded_ip == ip
        assert decoded_port == port

    def test_roundtrip_edge_ips(self):
        """Test edge-case IP addresses."""
        edge_ips = [
            "0.0.0.0",
            "255.255.255.255",
            "1.1.1.1",
            "192.168.0.1",
            "172.16.0.1",
            "10.255.255.255",
        ]
        for ip in edge_ips:
            code = encode_discovery_code(ip)
            decoded_ip, decoded_port = decode_discovery_code(code)
            assert decoded_ip == ip, f"Round-trip failed for {ip}"
            assert decoded_port == DEFAULT_IPX_PORT

    def test_roundtrip_edge_ports(self):
        """Test edge-case port numbers."""
        ip = "10.0.0.1"
        edge_ports = [1, 80, 443, 8080, 19900, 65535]
        for port in edge_ports:
            code = encode_discovery_code(ip, port)
            decoded_ip, decoded_port = decode_discovery_code(code)
            assert decoded_ip == ip
            assert decoded_port == port, f"Round-trip failed for port {port}"

    def test_roundtrip_all_first_bytes(self):
        """Every possible first byte (0-255) should round-trip."""
        for first_byte in range(256):
            ip = f"{first_byte}.0.0.1"
            code = encode_discovery_code(ip)
            decoded_ip, _ = decode_discovery_code(code)
            assert decoded_ip == ip, f"Round-trip failed for {ip}"


class TestResolveHost:
    """Test the resolve_host helper."""

    def test_raw_ip_passthrough(self):
        ip, port = resolve_host("192.168.1.42")
        assert ip == "192.168.1.42"
        assert port == DEFAULT_IPX_PORT

    def test_raw_ip_with_custom_default_port(self):
        ip, port = resolve_host("192.168.1.42", default_port=9999)
        assert ip == "192.168.1.42"
        assert port == 9999

    def test_discovery_code(self):
        # Encode a known IP, then resolve it
        code = encode_discovery_code("203.0.113.5")
        ip, port = resolve_host(code)
        assert ip == "203.0.113.5"
        assert port == DEFAULT_IPX_PORT

    def test_discovery_code_with_port(self):
        code = encode_discovery_code("203.0.113.5", port=20000)
        ip, port = resolve_host(code)
        assert ip == "203.0.113.5"
        assert port == 20000

    def test_invalid_ip_raises(self):
        with pytest.raises(ValueError, match="Invalid IP"):
            resolve_host("999.999.999.999")

    def test_invalid_code_raises(self):
        with pytest.raises(ValueError):
            resolve_host("NOTAWORD-12345")
