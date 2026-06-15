#!/usr/bin/env python3
"""Device discovery endpoints for network scanning
"""
import socket
from datetime import datetime, UTC

from flask import request, make_response, jsonify
from api.v1.views.device import device_bp
from services.network_discovery import NetworkDiscovery, MDNSDiscovery, USBDeviceDiscovery
from utils.logger import logger


@device_bp.route('/discover/printers', methods=['GET'], strict_slashes=False)
def discover_printers():
    """Discover network printers on local network

    Query params:
    - subnet: Optional subnet to scan (default: auto-detect)
    - timeout: Scan timeout in seconds (default: 0.5)
    """
    subnet = request.args.get('subnet')
    timeout = float(request.args.get('timeout', 0.5))

    try:
        # Scan network for printers
        printers = NetworkDiscovery.scan_network_for_printers(subnet, timeout)

        # Also try mDNS discovery
        bonjour_printers = MDNSDiscovery.discover_bonjour_printers()
        for printer in bonjour_printers:
            if printer not in printers:
                printers.append(printer)

        return make_response(jsonify({
            'success': True,
            'printers': printers,
            'count': len(printers),
            'message': f'Found {len(printers)} printer(s) on network'
        }), 200)

    except Exception as e:
        logger.error(f"Printer discovery failed: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'error': str(e),
            'printers': []
        }), 500)


@device_bp.route('/discover/tablets', methods=['GET'], strict_slashes=False)
def discover_tablets():
    """Discover potential tablets on local network"""
    subnet = request.args.get('subnet')

    try:
        tablets = NetworkDiscovery.discover_tablets(subnet)

        return make_response(jsonify({
            'success': True,
            'tablets': tablets,
            'count': len(tablets)
        }), 200)

    except Exception as e:
        logger.error(f"Tablet discovery failed: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'error': str(e)
        }), 500)


@device_bp.route('/discover/usb-printers', methods=['GET'], strict_slashes=False)
def discover_usb_printers():
    """Discover locally connected USB printers"""
    try:
        printers = USBDeviceDiscovery.discover_usb_printers()

        return make_response(jsonify({
            'success': True,
            'printers': printers,
            'count': len(printers)
        }), 200)

    except Exception as e:
        logger.error(f"USB printer discovery failed: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'error': str(e)
        }), 500)


@device_bp.route('/discover/all', methods=['GET'], strict_slashes=False)
def discover_all():
    """Discover all devices (printers and tablets) on network"""
    subnet = request.args.get('subnet')
    timeout = float(request.args.get('timeout', 0.5))

    try:
        # Discover printers
        printers = NetworkDiscovery.scan_network_for_printers(subnet, timeout)

        # Discover tablets
        tablets = NetworkDiscovery.discover_tablets(subnet)

        # Discover USB printers
        usb_printers = USBDeviceDiscovery.discover_usb_printers()

        return make_response(jsonify({
            'success': True,
            'devices': {
                'network_printers': printers,
                'network_tablets': tablets,
                'usb_printers': usb_printers
            },
            'summary': {
                'total_network_printers': len(printers),
                'total_tablets': len(tablets),
                'total_usb_printers': len(usb_printers)
            },
            'timestamp': datetime.now(UTC).isoformat()
        }), 200)

    except Exception as e:
        logger.error(f"Device discovery failed: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'error': str(e)
        }), 500)


@device_bp.route('/test-connection', methods=['POST'], strict_slashes=False)
def test_printer_connection():
    """Test connection to a printer"""
    data = request.get_json()

    ip = data.get('ip')
    port = data.get('port', 9100)
    printer_type = data.get('printer_type', 'network')

    if printer_type == 'network' and not ip:
        return make_response(jsonify({'error': 'IP address required'}), 400)

    try:
        if printer_type == 'network':
            # Test TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                # Try to get printer status
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((ip, port))
                    sock.send(b'\x10\x04\x01')  # Status request
                    response = sock.recv(1024)
                    sock.close()

                    return make_response(jsonify({
                        'success': True,
                        'connected': True,
                        'message': f'Successfully connected to printer at {ip}:{port}',
                        'response_received': len(response) > 0,
                        'printer_ready': True
                    }), 200)
                except:
                    return make_response(jsonify({
                        'success': True,
                        'connected': True,
                        'message': f'Connected to printer at {ip}:{port}',
                        'printer_ready': True
                    }), 200)
            else:
                return make_response(jsonify({
                    'success': False,
                    'connected': False,
                    'error': f'Cannot connect to {ip}:{port}'
                }), 200)

        elif printer_type == 'usb':
            # For USB, just acknowledge
            return make_response(jsonify({
                'success': True,
                'connected': True,
                'message': 'USB printer selected',
                'printer_ready': True
            }), 200)

    except Exception as e:
        return make_response(jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 500)