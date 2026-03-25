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
    def test_word_list_integrity(self):
        assert len(WORD_LIST) == 256
        assert len(set(WORD_LIST)) == 256
        assert all(w == w.upper() for w in WORD_LIST)

    def test_reverse_lookup_matches(self):
        for i, word in enumerate(WORD_LIST):
            assert _WORD_TO_INDEX[word] == i


class TestBase36:
    def test_roundtrip(self):
        for n in [0, 1, 42, 255, 1000, 0xFFFFFF]:
            assert _from_base36(_to_base36(n, 5)) == n

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            _to_base36(-1, 5)

    def test_overflow_raises(self):
        with pytest.raises(ValueError):
            _to_base36(36**5, 5)

    def test_invalid_char_raises(self):
        with pytest.raises(ValueError):
            _from_base36("!!!")


class TestEncodeDiscoveryCode:
    def test_default_port_format(self):
        code = encode_discovery_code("10.0.0.1")
        parts = code.split("-")
        assert len(parts) == 2
        assert parts[0] in WORD_LIST
        assert len(parts[1]) == 5

    def test_custom_port_format(self):
        code = encode_discovery_code("10.0.0.1", port=20000)
        parts = code.split("-")
        assert len(parts) == 3
        assert parts[2].startswith("P")
        assert len(parts[2]) == 5

    def test_first_byte_maps_to_word(self):
        assert encode_discovery_code("10.0.0.1").split("-")[0] == WORD_LIST[10]
        assert encode_discovery_code("192.168.1.1").split("-")[0] == WORD_LIST[192]


class TestDecodeDiscoveryCode:
    def test_default_port(self):
        _, port = decode_discovery_code("BUZZ-00001")
        assert port == DEFAULT_IPX_PORT

    def test_case_insensitive(self):
        code = encode_discovery_code("10.0.0.1")
        assert decode_discovery_code(code.upper()) == decode_discovery_code(code.lower())

    def test_strips_whitespace(self):
        code = encode_discovery_code("10.0.0.1")
        ip, _ = decode_discovery_code("  " + code + "  ")
        assert ip == "10.0.0.1"

    def test_unknown_word_raises(self):
        with pytest.raises(ValueError, match="Unknown word"):
            decode_discovery_code("ZZZZZ-00001")

    def test_wrong_digit_length_raises(self):
        with pytest.raises(ValueError, match="5 characters"):
            decode_discovery_code("BUZZ-001")

    @pytest.mark.parametrize("code", ["BUZZ-00001-P1234-EXTRA", "BUZZ"])
    def test_wrong_part_count_raises(self, code):
        with pytest.raises(ValueError, match="Invalid discovery code"):
            decode_discovery_code(code)

    @pytest.mark.parametrize("code", ["BUZZ-00001-X1234", "BUZZ-00001-P12"])
    def test_invalid_port_section_raises(self, code):
        with pytest.raises(ValueError, match="Invalid port section"):
            decode_discovery_code(code)


class TestRoundTrip:
    def test_roundtrip_edge_ports(self):
        ip = "10.0.0.1"
        for port in [1, 80, 443, 8080, 19900, 65535]:
            code = encode_discovery_code(ip, port)
            assert decode_discovery_code(code) == (ip, port)

    def test_roundtrip_all_first_bytes(self):
        for first_byte in range(256):
            ip = f"{first_byte}.0.0.1"
            decoded_ip, _ = decode_discovery_code(encode_discovery_code(ip))
            assert decoded_ip == ip


class TestResolveHost:
    def test_raw_ip_passthrough(self):
        assert resolve_host("192.168.1.42") == ("192.168.1.42", DEFAULT_IPX_PORT)

    def test_raw_ip_with_custom_default_port(self):
        assert resolve_host("192.168.1.42", default_port=9999) == ("192.168.1.42", 9999)

    def test_discovery_code(self):
        for port in [DEFAULT_IPX_PORT, 20000]:
            code = encode_discovery_code("203.0.113.5", port)
            assert resolve_host(code) == ("203.0.113.5", port)

    def test_invalid_ip_raises(self):
        with pytest.raises(ValueError, match="Invalid IP"):
            resolve_host("999.999.999.999")

    def test_invalid_code_raises(self):
        with pytest.raises(ValueError):
            resolve_host("NOTAWORD-12345")
