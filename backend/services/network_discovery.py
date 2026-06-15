#!/usr/bin/env python3
"""Network discovery service for finding printers and devices on local network
"""
import socket
import subprocess
import re
from typing import List, Dict, Any
from datetime import datetime
import json

from utils.logger import logger


class NetworkDiscovery:
    """Discover network printers and devices on local network"""

    # Common ESC/POS printer ports
    PRINTER_PORTS = [9100, 515, 631, 9101, 9102]

    # Common printer SNMP OIDs
    SNMP_OIDS = {
        'printer_name': '1.3.6.1.2.1.25.3.2.1.3.1',
        'printer_model': '1.3.6.1.2.1.25.3.2.1.5.1',
        'printer_status': '1.3.6.1.2.1.25.3.2.1.5.1'
    }

    @classmethod
    def get_local_network(cls) -> str:
        """Get local network subnet"""
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Extract subnet
            subnet = '.'.join(local_ip.split('.')[:-1])
            return subnet
        except Exception as e:
            logger.error(f"Failed to get local network: {e}")
            return "192.168.1"  # Default fallback

    @classmethod
    def scan_network_for_printers(cls, subnet: str = None, timeout: float = 0.5) -> List[Dict[str, Any]]:
        """Scan local network for printers"""
        if not subnet:
            subnet = cls.get_local_network()

        printers = []

        for i in range(1, 255):
            ip = f"{subnet}.{i}"

            for port in cls.PRINTER_PORTS:
                logger.info(f'Checking ip {ip}:{port}')
                if cls.check_port(ip, port, timeout):
                    printer_info = cls.get_printer_info(ip, port)
                    if printer_info:
                        printers.append(printer_info)
                    else:
                        # Add basic info if SNMP not available
                        printers.append({
                            'ip': ip,
                            'port': port,
                            'name': f'Printer at {ip}:{port}',
                            'model': 'Unknown',
                            'status': 'online',
                            'interface': 'network',
                            'discovery_method': 'port_scan'
                        })
                    break  # Found printer on this IP, no need to check other ports

        return printers

    @classmethod
    def check_port(cls, ip: str, port: int, timeout: float = 0.5) -> bool:
        """Check if a port is open on an IP address"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False

    @classmethod
    def get_printer_info(cls, ip: str, port: int) -> Dict[str, Any]:
        """Get detailed printer information via SNMP if available"""
        try:
            # Try SNMP to get printer info (requires snmp package)
            # For now, return basic info
            return {
                'ip': ip,
                'port': port,
                'name': f'ESC/POS Printer at {ip}',
                'model': cls.detect_printer_model(ip, port),
                'status': 'online',
                'interface': 'network',
                'discovery_method': 'snmp'
            }
        except:
            return None

    @classmethod
    def detect_printer_model(cls, ip: str, port: int) -> str:
        """Attempt to detect printer model by probing"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((ip, port))

            # Send status command
            sock.send(b'\x10\x04\x01')
            response = sock.recv(1024)
            sock.close()

            # Look for model identifiers in response
            response_str = str(response)
            if 'XP-Q80' in response_str or 'XPrinter' in response_str:
                return 'XPrinter XP-Q80'
            elif 'TM-T20' in response_str:
                return 'Epson TM-T20'
            elif 'Bixolon' in response_str:
                return 'Bixolon SRP-350'
            else:
                return 'Generic ESC/POS Printer'
        except:
            return 'Unknown'

    @classmethod
    def discover_tablets(cls, subnet: str = None, timeout: float = 0.5) -> List[Dict[str, Any]]:
        """Discover potential tablet devices on network"""
        if not subnet:
            subnet = cls.get_local_network()

        tablets = []

        for i in range(1, 255):
            ip = f"{subnet}.{i}"

            # Check for common tablet ports (SSH, HTTP, custom)
            if cls.check_port(ip, 22, timeout) or cls.check_port(ip, 8080, timeout):
                tablet_info = cls.get_tablet_info(ip)
                if tablet_info:
                    tablets.append(tablet_info)

        return tablets

    @classmethod
    def get_tablet_info(cls, ip: str) -> Dict[str, Any]:
        """Get information about a potential tablet on the network"""
        # Try to get hostname
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = f"Device at {ip}"

        return {
            'ip': ip,
            'hostname': hostname,
            'type': 'tablet',
            'status': 'online'
        }


class MDNSDiscovery:
    """mDNS/Bonjour discovery for printers"""

    @staticmethod
    def discover_bonjour_printers(timeout: int = 5) -> List[Dict[str, Any]]:
        """Discover printers using mDNS (Bonjour/Avahi)"""
        printers = []

        try:
            # Try to use avahi-browse (Linux)
            result = subprocess.run(
                ['avahi-browse', '-r', '-t', '_ipp._tcp', '--terminate', '--timeout', str(timeout)],
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )

            # Parse output
            for line in result.stdout.split('\n'):
                if 'address' in line.lower():
                    # Extract IP and name
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        printers.append({
                            'ip': match.group(1),
                            'port': 631,
                            'name': 'IPP Printer',
                            'protocol': 'ipp',
                            'discovery_method': 'bonjour'
                        })
        except FileNotFoundError:
            logger.debug("avahi-browse not available")
        except Exception as e:
            logger.debug(f"mDNS discovery failed: {e}")

        return printers


class USBDeviceDiscovery:
    """Discover USB printers connected to the system"""

    @staticmethod
    def discover_usb_printers() -> List[Dict[str, Any]]:
        """Discover USB printers connected to the system"""
        printers = []

        try:
            # On Linux, check /dev/usb/lp*
            import glob
            usb_devices = glob.glob('/dev/usb/lp*')

            for device in usb_devices:
                printers.append({
                    'device_path': device,
                    'name': f'USB Printer {device}',
                    'interface': 'usb',
                    'discovery_method': 'udev'
                })
        except:
            pass

        try:
            # On Windows, use win32print
            import win32print
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 2):
                printers.append({
                    'name': printer[2],
                    'interface': 'usb',
                    'discovery_method': 'win32'
                })
        except ImportError:
            pass

        return printers