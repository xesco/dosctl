"""UPnP IGD port mapper using only Python stdlib.

Implements the minimum UPnP Internet Gateway Device protocol needed to
add and remove UDP port mappings on a home router. This allows the host
player's DOSBox IPX server to be reachable from the internet without
manual port forwarding.

The protocol flow is:
  1. SSDP discovery (UDP multicast) to find the gateway device
  2. HTTP GET to fetch the device's XML descriptor
  3. Parse the descriptor to find the WANIPConnection control URL
  4. SOAP POST to add/delete port mappings
"""

import socket
import struct
import re
import atexit

from typing import Optional

# Python 2/3 compat is not needed (>=3.8) but keep imports clean
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse

from xml.etree import ElementTree as ET

# SSDP constants
_SSDP_ADDR = "239.255.255.250"
_SSDP_PORT = 1900

# UPnP service types we look for (WANIPConnection covers most routers,
# WANPPPConnection covers DSL routers)
_SERVICE_TYPES = [
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANPPPConnection:1",
    "urn:schemas-upnp-org:service:WANIPConnection:2",
]

# Search targets for SSDP discovery
_SEARCH_TARGETS = [
    "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
]

_SSDP_TEMPLATE = (
    "M-SEARCH * HTTP/1.1\r\n"
    "HOST: 239.255.255.250:1900\r\n"
    'MAN: "ssdp:discover"\r\n'
    "MX: {mx}\r\n"
    "ST: {st}\r\n"
    "\r\n"
)

_SOAP_ENVELOPE = (
    '<?xml version="1.0"?>'
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
    ' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    "<s:Body>{body}</s:Body>"
    "</s:Envelope>"
)

_ADD_PORT_MAPPING_BODY = (
    '<u:AddPortMapping xmlns:u="{service_type}">'
    "<NewRemoteHost></NewRemoteHost>"
    "<NewExternalPort>{external_port}</NewExternalPort>"
    "<NewProtocol>{protocol}</NewProtocol>"
    "<NewInternalPort>{internal_port}</NewInternalPort>"
    "<NewInternalClient>{internal_ip}</NewInternalClient>"
    "<NewEnabled>1</NewEnabled>"
    "<NewPortMappingDescription>{description}</NewPortMappingDescription>"
    "<NewLeaseDuration>{lease_duration}</NewLeaseDuration>"
    "</u:AddPortMapping>"
)

_DELETE_PORT_MAPPING_BODY = (
    '<u:DeletePortMapping xmlns:u="{service_type}">'
    "<NewRemoteHost></NewRemoteHost>"
    "<NewExternalPort>{external_port}</NewExternalPort>"
    "<NewProtocol>{protocol}</NewProtocol>"
    "</u:DeletePortMapping>"
)

_GET_EXTERNAL_IP_BODY = (
    '<u:GetExternalIPAddress xmlns:u="{service_type}"></u:GetExternalIPAddress>'
)


class UPnPError(Exception):
    """Raised when a UPnP operation fails."""

    pass


class UPnPPortMapper(object):
    """UPnP IGD port mapper using only stdlib.

    Usage:
        mapper = UPnPPortMapper()
        if mapper.discover_gateway():
            mapper.add_port_mapping(19900, "192.168.1.42")
            # ... later ...
            mapper.delete_port_mapping(19900)
    """

    def __init__(self):
        self._control_url = None  # type: Optional[str]
        self._service_type = None  # type: Optional[str]
        self._registered_mappings = []  # type: list

    def discover_gateway(self, timeout=3.0):
        """Discover a UPnP IGD gateway on the local network.

        Args:
            timeout: Maximum seconds to wait for SSDP responses.

        Returns:
            True if a gateway was found, False otherwise.
        """
        location = self._ssdp_discover(timeout)
        if not location:
            return False

        try:
            self._control_url, self._service_type = self._parse_device_xml(location)
            return self._control_url is not None
        except Exception:
            return False

    def add_port_mapping(
        self,
        external_port,
        internal_ip,
        internal_port=None,
        protocol="UDP",
        description="dosctl",
        lease_duration=3600,
    ):
        """Add a port mapping on the gateway.

        Args:
            external_port: External port number to map.
            internal_ip: LAN IP of this machine.
            internal_port: Internal port (defaults to external_port).
            protocol: "UDP" or "TCP".
            description: Human-readable description for the mapping.
            lease_duration: Lease time in seconds (0 = permanent on some routers).

        Returns:
            True if the mapping was added successfully.

        Raises:
            UPnPError: If no gateway has been discovered.
        """
        if not self._control_url or not self._service_type:
            raise UPnPError("No gateway discovered. Call discover_gateway() first.")

        if internal_port is None:
            internal_port = external_port

        body = _ADD_PORT_MAPPING_BODY.format(
            service_type=self._service_type,
            external_port=external_port,
            protocol=protocol,
            internal_port=internal_port,
            internal_ip=internal_ip,
            description=description,
            lease_duration=lease_duration,
        )

        try:
            self._soap_request("AddPortMapping", body)
            self._registered_mappings.append((external_port, protocol))
            return True
        except Exception:
            return False

    def delete_port_mapping(self, external_port, protocol="UDP"):
        """Remove a port mapping from the gateway.

        Args:
            external_port: External port number to unmap.
            protocol: "UDP" or "TCP".

        Returns:
            True if the mapping was removed successfully.
        """
        if not self._control_url or not self._service_type:
            return False

        body = _DELETE_PORT_MAPPING_BODY.format(
            service_type=self._service_type,
            external_port=external_port,
            protocol=protocol,
        )

        try:
            self._soap_request("DeletePortMapping", body)
            try:
                self._registered_mappings.remove((external_port, protocol))
            except ValueError:
                pass
            return True
        except Exception:
            return False

    def get_external_ip(self):
        """Get the external IP address from the gateway.

        Returns:
            External IP string, or None on failure.
        """
        if not self._control_url or not self._service_type:
            return None

        body = _GET_EXTERNAL_IP_BODY.format(service_type=self._service_type)

        try:
            response = self._soap_request("GetExternalIPAddress", body)
            # Parse the response XML for NewExternalIPAddress
            root = ET.fromstring(response)
            for elem in root.iter():
                if elem.tag.endswith("NewExternalIPAddress"):
                    ip = elem.text
                    if ip and ip.strip():
                        return ip.strip()
            return None
        except Exception:
            return None

    def cleanup(self):
        """Remove all port mappings registered by this instance."""
        for external_port, protocol in list(self._registered_mappings):
            self.delete_port_mapping(external_port, protocol)

    def register_cleanup(self):
        """Register an atexit handler to clean up mappings on exit."""
        atexit.register(self.cleanup)

    # -- Private methods --

    def _ssdp_discover(self, timeout):
        """Send SSDP M-SEARCH and return the LOCATION of the first IGD found."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)

        # Set TTL for multicast
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL,
            struct.pack("b", 2),
        )

        try:
            # Try each search target
            for st in _SEARCH_TARGETS:
                msg = _SSDP_TEMPLATE.format(mx=2, st=st)
                try:
                    sock.sendto(msg.encode("utf-8"), (_SSDP_ADDR, _SSDP_PORT))
                except OSError:
                    continue

            # Collect responses
            while True:
                try:
                    data, _ = sock.recvfrom(4096)
                    response = data.decode("utf-8", errors="replace")
                    location = self._parse_ssdp_location(response)
                    if location:
                        return location
                except socket.timeout:
                    break
                except OSError:
                    break
        finally:
            sock.close()

        return None

    @staticmethod
    def _parse_ssdp_location(response):
        """Extract the LOCATION header from an SSDP response."""
        match = re.search(
            r"^LOCATION:\s*(.+?)\s*$", response, re.IGNORECASE | re.MULTILINE
        )
        if match:
            return match.group(1).strip()
        return None

    def _parse_device_xml(self, location):
        """Fetch and parse the device XML to find the WANIPConnection control URL.

        Returns:
            Tuple of (control_url, service_type) or (None, None).
        """
        req = Request(location)
        req.add_header("User-Agent", "dosctl UPnP/1.0")
        response = urlopen(req, timeout=5)
        xml_data = response.read()
        response.close()

        root = ET.fromstring(xml_data)

        # The XML uses namespaces; strip them for easier searching
        base_url = location.rsplit("/", 1)[0] + "/"

        # Also check for URLBase element
        for elem in root.iter():
            if elem.tag.endswith("URLBase") and elem.text:
                base_url = elem.text.strip()
                if not base_url.endswith("/"):
                    base_url += "/"
                break

        # Search for our target service types
        for service_type in _SERVICE_TYPES:
            control_url = self._find_service_control_url(
                root, service_type, base_url, location
            )
            if control_url:
                return control_url, service_type

        return None, None

    @staticmethod
    def _find_service_control_url(root, service_type, base_url, location):
        """Find the control URL for a specific service type in the device XML."""
        for elem in root.iter():
            if elem.tag.endswith("serviceType") and elem.text:
                if elem.text.strip() == service_type:
                    # Found our service; get the controlURL sibling
                    parent = None
                    # Walk the tree to find the parent service element
                    for p in root.iter():
                        for child in p:
                            if child is elem:
                                parent = p
                                break
                        if parent is not None:
                            break

                    if parent is not None:
                        for child in parent:
                            if child.tag.endswith("controlURL") and child.text:
                                url = child.text.strip()
                                if url.startswith("http"):
                                    return url
                                # Resolve relative URL
                                return urljoin(location, url)
        return None

    def _soap_request(self, action, body):
        """Send a SOAP request to the gateway's control URL.

        Returns:
            Response body as string.
        """
        envelope = _SOAP_ENVELOPE.format(body=body)
        soap_action = '"{service_type}#{action}"'.format(
            service_type=self._service_type, action=action
        )

        control_url = str(self._control_url)
        req = Request(control_url, data=envelope.encode("utf-8"))
        req.add_header("Content-Type", 'text/xml; charset="utf-8"')
        req.add_header("SOAPAction", soap_action)
        req.add_header("User-Agent", "dosctl UPnP/1.0")

        response = urlopen(req, timeout=5)
        result = response.read().decode("utf-8", errors="replace")
        response.close()
        return result
