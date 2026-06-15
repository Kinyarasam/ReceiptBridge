#!/usr/bin/env python3
"""Device model for managing printing agents
"""
import enum
import secrets
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import Column, String, Enum, Text, Boolean, DateTime, BigInteger

from models.base_model import BaseModel, Base, t_format


class Platform(enum.Enum):
    """Print job status enum
    """
    ANDROID_TABLET = 'android_tablet'
    DESKTOP = 'desktop'


class PrinterInterface(enum.Enum):
    USB = 'usb'
    BLUETOOTH = 'bluetooth'
    NETWORK = 'network'


class Device(BaseModel, Base):
    """Device model for agents
    """
    __tablename__ = 'devices'

    name = Column(String(255), nullable=True)
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    shop_id = Column(String(60), nullable=False, index=True)

    api_key = Column(String(255), nullable=False, unique=True)
    api_secret = Column(String(255), nullable=False)

    platform = Column(Enum(Platform), nullable=False)
    os_version = Column(String(100), nullable=True)
    app_version = Column(String(50), nullable=True)
    ip_address = Column(String(50), nullable=True)

    printer_model = Column(String(100), nullable=True)
    printer_interface = Column(Enum(PrinterInterface), default=PrinterInterface.USB, nullable=False)
    printer_connection_string = Column(Text, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
    last_ping_at = Column(DateTime, nullable=True)
    last_job_processed_at = Column(DateTime, nullable=True)
    total_jobs_printed = Column(BigInteger, default=0)

    registered_at = Column(DateTime, default=datetime.now(UTC))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.device_id:
            self.device_id = f"device_{secrets.token_hex(16)}"
        if not self.api_key:
            self.api_key = f"rb_key_{secrets.token_urlsafe(32)}"
        if not self.api_secret:
            self.api_secret = secrets.token_urlsafe(48)

    def generate_new_api_key(self):
        """Generate new API key for device
        """
        self.api_key = f"rb_key_{secrets.token_urlsafe(32)}"
        self.api_secret = secrets.token_urlsafe(48)
        self.save()
        return self.api_key, self.api_secret

    def update_last_ping(self):
        """Update last ping timestamp
        """
        self.last_ping_at = datetime.now(UTC)
        self.save()

    def increment_job_count(self):
        """Increment total jobs printed
        """
        self.total_jobs_printed += 1
        self.save()

    def to_dict(self, save_fs=None):
        new_dict = super().to_dict(save_fs)
        if save_fs is None:
            if 'api_key' in new_dict:
                del new_dict['api_key']
            if 'api_secret' in new_dict:
                del new_dict['api_secret']

        # Convert enum values to strings
        if 'platform' in new_dict and new_dict['platform']:
            if hasattr(new_dict['platform'], 'value'):
                new_dict['platform'] = new_dict['platform'].value
        else:
            new_dict['platform'] = None

        if 'last_ping_at' in new_dict and new_dict['last_ping_at']:
            new_dict['last_ping_at'] = new_dict['last_ping_at'].strftime(t_format)

        if 'printer_interface' in new_dict and new_dict['printer_interface']:
            if hasattr(new_dict['printer_interface'], 'value'):
                new_dict['printer_interface'] = new_dict['printer_interface'].value
        else:
            new_dict['printer_interface'] = None

        new_dict['is_online'] = self.is_online

        return new_dict

    @property
    def is_online(self) -> bool:
        if self.last_ping_at:
            if self.last_ping_at.tzinfo is None:
                from datetime import timezone
                last_ping_at = self.last_ping_at.replace(tzinfo=timezone.utc)
            else:
                last_ping_at = self.last_ping_at

            return (datetime.now(UTC) - last_ping_at) < timedelta(minutes=5)
        return False