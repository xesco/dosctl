"""Tests for UPnP port mapping."""

from unittest.mock import patch, MagicMock, call
from dosctl.lib.upnp import UPnPPortMapper, UPnPError

import pytest


# Minimal valid SSDP response
_SSDP_RESPONSE = (
    "HTTP/1.1 200 OK\r\n"
    "LOCATION: http://192.168.1.1:1780/InternetGatewayDevice.xml\r\n"
    "ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n"
    "\r\n"
)

# Minimal valid device XML with WANIPConnection service
_DEVICE_XML = """<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <URLBase>http://192.168.1.1:1780/</URLBase>
  <device>
    <deviceType>urn:schemas-upnp-org:device:InternetGatewayDevice:1</deviceType>
    <deviceList>
      <device>
        <deviceType>urn:schemas-upnp-org:device:WANDevice:1</deviceType>
        <deviceList>
          <device>
            <deviceType>urn:schemas-upnp-org:device:WANConnectionDevice:1</deviceType>
            <serviceList>
              <service>
                <serviceType>urn:schemas-upnp-org:service:WANIPConnection:1</serviceType>
                <controlURL>/control/WANIPConnection</controlURL>
              </service>
            </serviceList>
          </device>
        </deviceList>
      </device>
    </deviceList>
  </device>
</root>"""

# SOAP response for GetExternalIPAddress
_EXTERNAL_IP_RESPONSE = """<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:GetExternalIPAddressResponse xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
      <NewExternalIPAddress>203.0.113.5</NewExternalIPAddress>
    </u:GetExternalIPAddressResponse>
  </s:Body>
</s:Envelope>"""


class TestSSDPDiscovery:
    """Test SSDP gateway discovery."""

    @patch("dosctl.lib.upnp.urlopen")
    @patch("dosctl.lib.upnp.socket.socket")
    def test_discover_gateway_success(self, mock_socket_class, mock_urlopen):
        """Should find a gateway via SSDP and parse its XML."""
        # Mock SSDP socket
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (_SSDP_RESPONSE.encode(), ("192.168.1.1", 1900)),
            OSError("timeout"),
        ]

        # Mock HTTP fetch of device XML
        mock_response = MagicMock()
        mock_response.read.return_value = _DEVICE_XML.encode()
        mock_urlopen.return_value = mock_response

        mapper = UPnPPortMapper()
        result = mapper.discover_gateway(timeout=1.0)

        assert result is True
        assert mapper._control_url is not None
        assert "WANIPConnection" in mapper._control_url
        assert mapper._service_type == "urn:schemas-upnp-org:service:WANIPConnection:1"

    @patch("dosctl.lib.upnp.socket.socket")
    def test_discover_gateway_timeout(self, mock_socket_class):
        """Should return False when no gateway responds."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.side_effect = OSError("timeout")

        mapper = UPnPPortMapper()
        result = mapper.discover_gateway(timeout=0.1)

        assert result is False
        assert mapper._control_url is None

    @patch("dosctl.lib.upnp.socket.socket")
    def test_discover_gateway_no_location(self, mock_socket_class):
        """Should return False when SSDP response has no LOCATION."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.recvfrom.side_effect = [
            (b"HTTP/1.1 200 OK\r\n\r\n", ("192.168.1.1", 1900)),
            OSError("timeout"),
        ]

        mapper = UPnPPortMapper()
        result = mapper.discover_gateway(timeout=0.1)

        assert result is False


class TestPortMapping:
    """Test add/delete port mapping operations."""

    def _create_discovered_mapper(self):
        """Create a mapper with pre-set control URL and service type."""
        mapper = UPnPPortMapper()
        mapper._control_url = "http://192.168.1.1:1780/control/WANIPConnection"
        mapper._service_type = "urn:schemas-upnp-org:service:WANIPConnection:1"
        return mapper

    @patch("dosctl.lib.upnp.urlopen")
    def test_add_port_mapping_success(self, mock_urlopen):
        """Should send SOAP AddPortMapping request."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<ok/>"
        mock_urlopen.return_value = mock_response

        mapper = self._create_discovered_mapper()
        result = mapper.add_port_mapping(19900, "192.168.1.42")

        assert result is True
        assert (19900, "UDP") in mapper._registered_mappings

        # Verify SOAP request was made
        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode("utf-8")
        assert "AddPortMapping" in body
        assert "19900" in body
        assert "192.168.1.42" in body
        assert "UDP" in body

    @patch("dosctl.lib.upnp.urlopen")
    def test_add_port_mapping_failure(self, mock_urlopen):
        """Should return False on SOAP error."""
        mock_urlopen.side_effect = Exception("SOAP fault")

        mapper = self._create_discovered_mapper()
        result = mapper.add_port_mapping(19900, "192.168.1.42")

        assert result is False
        assert len(mapper._registered_mappings) == 0

    def test_add_port_mapping_no_gateway(self):
        """Should raise UPnPError when no gateway is discovered."""
        mapper = UPnPPortMapper()
        with pytest.raises(UPnPError, match="No gateway"):
            mapper.add_port_mapping(19900, "192.168.1.42")

    @patch("dosctl.lib.upnp.urlopen")
    def test_delete_port_mapping_success(self, mock_urlopen):
        """Should send SOAP DeletePortMapping request."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<ok/>"
        mock_urlopen.return_value = mock_response

        mapper = self._create_discovered_mapper()
        mapper._registered_mappings = [(19900, "UDP")]
        result = mapper.delete_port_mapping(19900)

        assert result is True
        assert (19900, "UDP") not in mapper._registered_mappings

        req = mock_urlopen.call_args[0][0]
        body = req.data.decode("utf-8")
        assert "DeletePortMapping" in body
        assert "19900" in body

    @patch("dosctl.lib.upnp.urlopen")
    def test_delete_port_mapping_failure(self, mock_urlopen):
        """Should return False on SOAP error."""
        mock_urlopen.side_effect = Exception("SOAP fault")

        mapper = self._create_discovered_mapper()
        result = mapper.delete_port_mapping(19900)

        assert result is False

    def test_delete_no_gateway(self):
        """Should return False when no gateway is discovered."""
        mapper = UPnPPortMapper()
        result = mapper.delete_port_mapping(19900)
        assert result is False


class TestGetExternalIP:
    """Test external IP retrieval via UPnP."""

    @patch("dosctl.lib.upnp.urlopen")
    def test_get_external_ip_success(self, mock_urlopen):
        """Should parse the external IP from SOAP response."""
        mock_response = MagicMock()
        mock_response.read.return_value = _EXTERNAL_IP_RESPONSE.encode()
        mock_urlopen.return_value = mock_response

        mapper = UPnPPortMapper()
        mapper._control_url = "http://192.168.1.1:1780/control/WANIPConnection"
        mapper._service_type = "urn:schemas-upnp-org:service:WANIPConnection:1"

        result = mapper.get_external_ip()
        assert result == "203.0.113.5"

    @patch("dosctl.lib.upnp.urlopen")
    def test_get_external_ip_failure(self, mock_urlopen):
        """Should return None on failure."""
        mock_urlopen.side_effect = Exception("error")

        mapper = UPnPPortMapper()
        mapper._control_url = "http://192.168.1.1:1780/control/WANIPConnection"
        mapper._service_type = "urn:schemas-upnp-org:service:WANIPConnection:1"

        result = mapper.get_external_ip()
        assert result is None

    def test_get_external_ip_no_gateway(self):
        """Should return None when no gateway is discovered."""
        mapper = UPnPPortMapper()
        result = mapper.get_external_ip()
        assert result is None


class TestVerifyPortMapping:
    """Test port mapping verification via GetSpecificPortMappingEntry."""

    def _create_discovered_mapper(self):
        """Create a mapper with pre-set control URL and service type."""
        mapper = UPnPPortMapper()
        mapper._control_url = "http://192.168.1.1:1780/control/WANIPConnection"
        mapper._service_type = "urn:schemas-upnp-org:service:WANIPConnection:1"
        return mapper

    @patch("dosctl.lib.upnp.urlopen")
    def test_verify_success(self, mock_urlopen):
        """Should return True when the router confirms the mapping."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<ok/>"
        mock_urlopen.return_value = mock_response

        mapper = self._create_discovered_mapper()
        result = mapper.verify_port_mapping(19900)

        assert result is True
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode("utf-8")
        assert "GetSpecificPortMappingEntry" in body
        assert "19900" in body
        assert "UDP" in body

    @patch("dosctl.lib.upnp.urlopen")
    def test_verify_failure(self, mock_urlopen):
        """Should return False when the router rejects the query."""
        mock_urlopen.side_effect = Exception("SOAP fault: 714 NoSuchEntryInArray")

        mapper = self._create_discovered_mapper()
        result = mapper.verify_port_mapping(19900)

        assert result is False

    def test_verify_no_gateway(self):
        """Should return False when no gateway is discovered."""
        mapper = UPnPPortMapper()
        result = mapper.verify_port_mapping(19900)
        assert result is False

    @patch("dosctl.lib.upnp.urlopen")
    def test_verify_tcp_protocol(self, mock_urlopen):
        """Should pass the correct protocol in the SOAP request."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<ok/>"
        mock_urlopen.return_value = mock_response

        mapper = self._create_discovered_mapper()
        result = mapper.verify_port_mapping(8080, protocol="TCP")

        assert result is True
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode("utf-8")
        assert "TCP" in body
        assert "8080" in body


class TestCleanup:
    """Test cleanup of registered port mappings."""

    @patch("dosctl.lib.upnp.urlopen")
    def test_cleanup_removes_all_mappings(self, mock_urlopen):
        """Should delete all registered mappings."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"<ok/>"
        mock_urlopen.return_value = mock_response

        mapper = UPnPPortMapper()
        mapper._control_url = "http://192.168.1.1:1780/control/WANIPConnection"
        mapper._service_type = "urn:schemas-upnp-org:service:WANIPConnection:1"
        mapper._registered_mappings = [(19900, "UDP"), (19901, "UDP")]

        mapper.cleanup()

        assert len(mapper._registered_mappings) == 0
        assert mock_urlopen.call_count == 2


class TestParseSSDP:
    """Test SSDP response parsing."""

    def test_parse_location_header(self):
        mapper = UPnPPortMapper()
        location = mapper._parse_ssdp_location(_SSDP_RESPONSE)
        assert location == "http://192.168.1.1:1780/InternetGatewayDevice.xml"

    def test_parse_missing_location(self):
        mapper = UPnPPortMapper()
        location = mapper._parse_ssdp_location("HTTP/1.1 200 OK\r\n\r\n")
        assert location is None

    def test_parse_case_insensitive(self):
        mapper = UPnPPortMapper()
        response = "HTTP/1.1 200 OK\r\nlocation: http://example.com/desc.xml\r\n\r\n"
        location = mapper._parse_ssdp_location(response)
        assert location == "http://example.com/desc.xml"
