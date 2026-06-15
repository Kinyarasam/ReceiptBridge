#!/usr/bin/env python3
"""PrintJob model for managing print queues
"""
import enum
from datetime import datetime, UTC

from sqlalchemy import Column, Integer, BigInteger, String, Enum, JSON, Text, DateTime

from models.base_model import BaseModel, Base


class JobStatus(enum.Enum):
    """Print job status enum
    """
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    PRINTING = 'printing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class PrintJob(BaseModel, Base):
    """PrintJob model for managing print queues
    """
    __tablename__ = 'print_jobs'

    job_number = Column(BigInteger, primary_key=True, autoincrement=True, unique=True)
    order_id = Column(String(60), nullable=False, index=True)
    shop_id = Column(String(60), nullable=False, index=True)
    receipt_id = Column(String(60), nullable=True, index=True)

    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    priority = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries= Column(Integer, default=3)

    order_data = Column(JSON, nullable=False)
    print_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    assigned_device_id = Column(String(60), nullable=True, index=True)
    assigned_at = Column(DateTime, default=datetime.now(UTC), nullable=True)

    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mark_as_assigned(self, device_id: str):
        """mark job as assigned to a device
        """
        self.status = JobStatus.ASSIGNED
        self.assigned_device_id = device_id
        self.assigned_at = datetime.now(UTC)

        self.save()

    def mark_as_printing(self):
        self.status = JobStatus.PRINTING

        self.save()

    def mark_as_completed(self):
        """Mark job as completed successfully
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

        self.save()

    def mark_as_failed(self, error_message: str):
        """Mark job as failed
        """
        self.status = JobStatus.FAILED
        self.failed_at = datetime.now(UTC)
        self.error_message = error_message
        self.retry_count += 1

    def can_retry(self) -> bool:
        """Check if job can be retried
        """
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED


    def to_dict(self, save_fs=None):
        new_dict = super().to_dict(save_fs)

        # Convert enum values to strings
        if 'status' in new_dict and new_dict['status']:
            if hasattr(new_dict['status'], 'value'):
                new_dict['status'] = new_dict['status'].value
        else:
            new_dict['status'] = None

        return new_dict