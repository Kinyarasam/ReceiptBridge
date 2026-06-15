#!/usr/bin/env python3
"""Device registration endpoints for tablet agents
"""
from flask import request, make_response, jsonify, abort

import models
from models.device.device import Device, Platform
from models.shopify.shopify_store import ShopifyStore
from services.device_service import DeviceService
from utils.logger import logger
from api.v1.views.device import device_bp
from utils.pagination import PaginationParams, PaginatedResponse


@device_bp.route('/register', methods=['POST'], strict_slashes=False)
def register_device():
    """Register a new tablet device

    Expected payload:
    {
        "shop_domain": "store.myshopify.com",
        "device_name": "Front Counter Tablet",
        "device_id": "unique-device-id",
        "device_type": "tablet",
        "os_version": "Android 13",
        "app_version": "1.0.0",
        "printer_model": "XP-Q80",
        "printer_interface": "usb",
        "printer_connection_string": "usb://VID:PID"
    }
    """
    data = request.get_json()

    if not data:
        return make_response(jsonify({'error': 'Request body required'}), 400)

    shop_domain = data.get('shop_domain')
    if not shop_domain:
        return make_response(jsonify({'error': 'shop_domain is required'}), 400)

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain)
    if not shop:
        return make_response(jsonify({'error': 'Shop not found'}), 404)

    try:
        device_service = DeviceService(shop_id=shop.id)
        device = device_service.register_device(shop_domain=shop_domain, device_data=data)

        if not device:
            return make_response(jsonify({'error': 'Registration failed. Shop not found'}), 404)

        return make_response(jsonify({
            'success': True,
            'message': 'Device successfully registered',
            'device': device.to_dict(save_fs='yes')
        }), 201)
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)


@device_bp.route('/<device_id>', methods=['GET'], strict_slashes=False)
def get_device(device_id):
    """Get device information"""
    # Authenticate
    api_key = request.headers.get('X-Device-API-Key')
    shop_domain = request.headers.get('X-Shop-Domain')

    if not api_key or not shop_domain:
        return make_response(jsonify({'error': 'Authentication required'}), 401)

    device_service = DeviceService()
    device = device_service.authenticate_device(api_key, shop_domain)


    if not device or device.device_id != device_id:
        return make_response(jsonify({'error': 'Unauthorized'}), 401)

    return make_response(jsonify({
        'success': True,
        'device': device.to_dict()
    }), 200)


@device_bp.route('/<device_id>', methods=['PUT'], strict_slashes=False)
def update_device(device_id):
    """Update device information"""
    # Authenticate
    api_key = request.headers.get('X-Device-API-Key')
    shop_domain = request.headers.get('X-Shop-Domain')

    if not api_key or not shop_domain:
        return make_response(jsonify({'error': 'Authentication required'}), 401)

    device_service = DeviceService()
    device = device_service.authenticate_device(api_key, shop_domain)

    if not device or device.device_id != device_id:
        return make_response(jsonify({'error': 'Unauthorized'}), 401)

    update_data = request.get_json()
    updated_device = device_service.update_device(device_id, update_data)

    return make_response(jsonify({
        'success': True,
        'device': updated_device.to_dict()
    }), 200)


@device_bp.route('/<device_id>/ping', methods=['POST'], strict_slashes=False)
def ping_device(device_id):
    """Update device last ping time"""
    # Authenticate
    api_key = request.headers.get('X-Device-API-Key')
    shop_domain = request.headers.get('X-Shop-Domain')

    if not api_key or not shop_domain:
        return make_response(jsonify({'error': 'Authentication required'}), 401)

    device_service = DeviceService()
    device = device_service.authenticate_device(api_key, shop_domain)

    if not device or device.device_id != device_id:
        return make_response(jsonify({'error': 'Unauthorized'}), 401)

    device_service.ping_device(device_id)

    return make_response(jsonify({
        'success': True,
        'message': 'Ping received'
    }), 200)


@device_bp.route('/<device_id>/rotate-key', methods=['POST'], strict_slashes=False)
def rotate_api_key(device_id):
    """Rotate device API key"""
    # Authenticate (using old key)
    api_key = request.headers.get('X-Device-API-Key')
    shop_domain = request.headers.get('X-Shop-Domain')

    if not api_key or not shop_domain:
        return make_response(jsonify({'error': 'Authentication required'}), 401)

    device_service = DeviceService()
    device = device_service.authenticate_device(api_key, shop_domain)

    if not device or device.device_id != device_id:
        return make_response(jsonify({'error': 'Unauthorized'}), 401)

    new_api_key, new_api_secret = device_service.rotate_api_key(device_id)

    return make_response(jsonify({
        'success': True,
        'message': 'API key rotated successfully',
        'new_api_key': new_api_key,
        'new_api_secret': new_api_secret
    }), 200)


@device_bp.route('/', methods=['GET'], strict_slashes=False)
def list_devices():
    """List all devices for a shop (admin endpoint)"""
    pagination_params = PaginationParams.from_request(default_per_page=20, max_per_page=100)

    # Get filters
    shop_domain = request.headers.get('X-Shop-Domain')
    platform = request.args.get('platform')
    is_active = request.args.get('is_active')

    # Build query
    query = models.storage.query(Device)

    if shop_domain:
        shop: ShopifyStore = models.storage.find(ShopifyStore, shop_domain=shop_domain)
        if shop:
            query = query.filter(Device.shop_id == shop.id)

    if platform:
        query = query.filter(Device.platform == Platform(platform))

    # Get total count
    total_items = query.count()

    # Apply pagination
    devices = query.offset(pagination_params.offset).limit(pagination_params.per_page).all()

    response = PaginatedResponse(devices, pagination_params, total_items)
    def serialize_device(device):
        return device.to_dict()

    return response.to_dict(item_serializer=serialize_device)


@device_bp.route('/<device_id>', methods=['DELETE'], strict_slashes=False)
def deactivate_device(device_id):
    """Deactivate device
    """
    shop_domain = request.headers.get('X-Shop-Domain')
    if not shop_domain:
        abort(403, description='shop_domain is required')

    shop: ShopifyStore = models.storage.find(ShopifyStore, shop_domain)
    if not shop:
        abort(404, description='shop not found')

    device_service = DeviceService(shop_id=shop.id)
    if device_service.deactivate_device(device_id=device_id):
        return make_response(jsonify({
            'success': True,
            'message': f'Device {device_id} has been deactivated'
        }), 200)
    else:
        return make_response(jsonify({
            'success': False,
            'message': f'Device {device_id} not found'
        }), 404)


# =================================================================================
# =================================================================================

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