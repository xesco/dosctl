"""Tests for network utilities."""

from dosctl.lib.network import is_cgnat_address


class TestIsCgnatAddress:
    """Test CGNAT and private address detection."""

    def test_cgnat_range_low(self):
        """100.64.0.0 is the start of the CGNAT range."""
        assert is_cgnat_address("100.64.0.0") is True

    def test_cgnat_range_high(self):
        """100.127.255.255 is the end of the CGNAT range."""
        assert is_cgnat_address("100.127.255.255") is True

    def test_cgnat_typical_starlink(self):
        """Typical Starlink CGNAT address."""
        assert is_cgnat_address("100.78.42.1") is True

    def test_not_cgnat_adjacent_low(self):
        """100.63.255.255 is just below the CGNAT range."""
        assert is_cgnat_address("100.63.255.255") is False

    def test_not_cgnat_adjacent_high(self):
        """100.128.0.0 is just above the CGNAT range."""
        assert is_cgnat_address("100.128.0.0") is False

    def test_private_10(self):
        """10.0.0.0/8 private range."""
        assert is_cgnat_address("10.0.0.1") is True
        assert is_cgnat_address("10.255.255.255") is True

    def test_private_172(self):
        """172.16.0.0/12 private range."""
        assert is_cgnat_address("172.16.0.1") is True
        assert is_cgnat_address("172.31.255.255") is True

    def test_not_private_172(self):
        """172.32.0.0 is outside the private range."""
        assert is_cgnat_address("172.32.0.1") is False

    def test_private_192(self):
        """192.168.0.0/16 private range."""
        assert is_cgnat_address("192.168.0.1") is True
        assert is_cgnat_address("192.168.255.255") is True

    def test_public_ip(self):
        """Public IP addresses should return False."""
        assert is_cgnat_address("203.0.113.5") is False
        assert is_cgnat_address("8.8.8.8") is False
        assert is_cgnat_address("1.1.1.1") is False

    def test_invalid_ip(self):
        """Invalid IP strings should return False."""
        assert is_cgnat_address("not-an-ip") is False
        assert is_cgnat_address("") is False
