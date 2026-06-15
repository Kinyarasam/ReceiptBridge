#!/usr/bin/env python3
"""Device service for managing tablet agents
"""
from datetime import timedelta, datetime, UTC
from typing import Dict, Optional, Any, List, Tuple

from werkzeug.exceptions import Unauthorized

import models
from models.device.device import Device, Platform, PrinterInterface
from models.shopify.shopify_store import ShopifyStore
from utils.logger import logger


class DeviceService:
    """Service for managing devices
    """

    def __init__(self, shop_id: str = None):
        self.shop_id = shop_id

    def register_device(self, shop_domain: str, device_data: Dict[str, Any]) -> Optional[Device]:
        """Register a new device for a shop
        """
        try:
            # Get shop
            shop: ShopifyStore = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
            if not shop:
                logger.error(f"Shop {shop_domain} not found or inactive")
                return None

            # Check if device already exists
            existing_device = models.storage.find_first(Device, device_id=device_data.get('device_id'))
            if existing_device:
                logger.info(f"Device {existing_device.device_id} already registered")
                return existing_device

            # platform_data = device_data.get('platform')
            # if str(platform_data).lower() == 'tablet':
            #     platform = Platform.ANDROID_TABLET

            # Create new Device
            device = Device()
            device.shop_id = shop.id
            device.name = device_data.get('name')
            device.platform = Platform(device_data.get('platform'))
            device.os_version = device_data.get('os_version')
            device.app_version = device_data.get('app_version')
            device.ip_address = device_data.get('ip_address')
            device.ip_address = device_data.get('ip_address')
            device.printer_model = device_data.get('printer_model')
            device.printer_interface = PrinterInterface(device_data.get('printer_interface', 'usb'))
            device.printer_connection_string = device_data.get('printer_connection_string')

            device.save()

            logger.info(f"Registered new device {device_data.get('device_id')} for shop {shop_domain}")

            return device

        except Exception as e:
            logger.error(f"Error registering device: {str(e)}")
            return None

    @staticmethod
    def authenticate_device(api_key, shop_domain: str = None) -> Optional[Device]:
        """Authenticate device using API key
        """
        try:
            shop: ShopifyStore = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
            if not shop:
                logger.warning(f"Authentication failed: Shop not found or inactive")
                return None

            # Find device using API key
            device: Device = models.storage.find_first(Device, api_key=api_key, shop_id=shop.id, is_active=True)
            if not device:
                logger.warning(f"Authentication failed: Device with API key not found")
                return None

            # Verify shop domain matches if provided
            if not shop_domain:
                shop = models.storage.find(ShopifyStore, is_active=True, id=device.shop_id)
                if not shop or shop.shop_domain != shop_domain:
                    logger.warning(f"Authentication failed: Shop domain mismatch for device {device.device_id}")
                    return None

            # Update last ping
            device.update_last_ping()
            return device

        except Exception as e:
            logger.error(f"Error authenticating device: {str(e)}")
            return None

    @staticmethod
    def get_device(device_id: str) -> Optional[Device]:
        """Get device by ID
        """
        return models.storage.find(Device, device_id=device_id)

    def get_devices_for_shop(self, include_inactive: bool = False) -> List[Device]:
        """"Get all devices for shop
        """
        if not self.shop_id:
            raise ValueError("shop_id is required")

        filters = {'shop_id': self.shop_id}
        if not include_inactive:
            filters['is_active'] = True

        devices = models.storage.find_all(Device, **filters)
        return devices

    @staticmethod
    def update_device(device_id: str, update_data: Dict[str, Any]) -> Optional[Device]:
        """Update device information
        """
        device: Device = models.storage.find_first(Device, device_id=device_id)
        if not device:
            logger.error(f"Device {device_id} not found")
            return None

        # Update allowed fields
        allowed_fields = ['name', 'os_version', 'app_version',
                          'printer_model', 'printer_interface',
                          'printer_connection_string', 'ip_address',]

        for field in allowed_fields:
            if field in update_data:
                setattr(device, field, update_data[field])

        device.save()
        logger.info(f"Updated device {device_id}")
        return device

    @staticmethod
    def deactivate_device(device_id: str) -> bool:
        """Deactivate a device
        """
        device: Device = models.storage.find(Device, device_id=device_id)
        if not device:
            logger.error(f"Device {device_id} not found")
            return False

        device.is_active = False
        device.save()

        logger.info(f"Deactivated device {device_id}")
        return True

    @staticmethod
    def rotate_api_key(device_id: str) -> Optional[Tuple[str, str]]:
        """Generate new API key for device
        """
        device: Device = models.storage.find(Device, device_id=device_id)
        if not device:
            logger.error(f"Device not found")
            return None

        api_key, api_secret = device.generate_api_key()
        logger.info(f"Rotated API key for device {device.device_id}")

        return api_key, api_secret

    def ping_device(self, device_id: str) -> bool:
        """Update device last ping time
        """
        device: Device = models.storage.find(Device, device_id=device_id)
        if not device:
            return False

        device.update_last_ping()
        return True

    def get_online_devices(self, minutes_threshold: int = 5) -> List[Device]:
        """Get devices that have pinged recently
        """
        if not self.shop_id:
            raise ValueError("shop_id is required")

        cutoff_time = datetime.now(UTC) - timedelta(minutes=minutes_threshold)

        devices = models.storage.find_all(
            Device,
            shop_id=self.shop_id,
            is_active=True
        )

        online = [d for d in devices if d.last_ping_at and d.last_ping_at > cutoff_time]
        return online