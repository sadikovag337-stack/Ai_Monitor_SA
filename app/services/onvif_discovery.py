import ipaddress
import socket
import time
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import unquote


DISCOVERY_ADDRESS = ("239.255.255.250", 3702)
DISCOVERY_TIMEOUT = 3.0
MAX_RESPONSES = 128

PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
 xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
 xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
 <e:Header>
  <w:MessageID>uuid:{message_id}</w:MessageID>
  <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
  <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
 </e:Header>
 <e:Body><d:Probe><d:Types>dn:NetworkVideoTransmitter</d:Types></d:Probe></e:Body>
</e:Envelope>"""


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


def _parse_response(payload, source_ip):
    try:
        address = ipaddress.ip_address(source_ip)
        if address.version != 4 or not address.is_private or address.is_loopback:
            return None
        root = ET.fromstring(payload)
    except (ValueError, ET.ParseError):
        return None

    scopes = ""
    xaddrs = ""
    for element in root.iter():
        if _local_name(element.tag) == "Scopes":
            scopes = element.text or ""
        elif _local_name(element.tag) == "XAddrs":
            xaddrs = element.text or ""

    name = None
    for scope in scopes.split():
        marker = "/name/"
        if marker in scope:
            name = unquote(scope.split(marker, 1)[1])
            break

    return {
        "ip": str(address),
        "name": name or "ONVIF-камера",
        "service": xaddrs.split()[0] if xaddrs.split() else "",
    }


def discover_onvif_cameras():
    message = PROBE.format(message_id=uuid.uuid4()).encode("utf-8")
    cameras = {}
    deadline = time.monotonic() + DISCOVERY_TIMEOUT

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(message, DISCOVERY_ADDRESS)

        while len(cameras) < MAX_RESPONSES:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            try:
                payload, (source_ip, _) = sock.recvfrom(65535)
            except socket.timeout:
                break

            camera = _parse_response(payload, source_ip)
            if camera:
                cameras[camera["ip"]] = camera

    return sorted(cameras.values(), key=lambda camera: camera["ip"])
