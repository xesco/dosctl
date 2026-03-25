"""Tests for network utilities."""

from dosctl.lib.network import is_cgnat_address


class TestIsCgnatAddress:
    def test_cgnat_range(self):
        assert is_cgnat_address("100.64.0.0") is True
        assert is_cgnat_address("100.78.42.1") is True
        assert is_cgnat_address("100.127.255.255") is True

    def test_cgnat_range_boundaries(self):
        assert is_cgnat_address("100.63.255.255") is False
        assert is_cgnat_address("100.128.0.0") is False

    def test_private_ranges(self):
        assert is_cgnat_address("10.0.0.1") is True
        assert is_cgnat_address("172.16.0.1") is True
        assert is_cgnat_address("172.31.255.255") is True
        assert is_cgnat_address("192.168.0.1") is True

    def test_not_private_172(self):
        assert is_cgnat_address("172.32.0.1") is False

    def test_public_ip(self):
        assert is_cgnat_address("203.0.113.5") is False
        assert is_cgnat_address("8.8.8.8") is False

    def test_invalid_ip(self):
        assert is_cgnat_address("not-an-ip") is False
        assert is_cgnat_address("") is False
