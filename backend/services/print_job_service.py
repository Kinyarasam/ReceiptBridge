#!/usr/bin/env python3
"""PrintJob service for managing print queues
"""
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, Optional, List

from shopify.resources import receipt

import models
from models.print.print_job import PrintJob, JobStatus
from services.escpos_generator import ESCPOSGenerator
from utils.logger import logger


class PrintJobService:
    """Service for managing print jobs
    """

    def __init__(self, shop_id: str = None):
        self.shop_id = shop_id

    def create_from_order(self, order_data: Dict[str, Any], receipt_id: str = '') -> Optional[PrintJob]:
        """Create a print job from shopify order
        """
        try:
            order_id = str(order_data.get('id'))

            # Check if print job already exists for this order
            existing_job = models.storage.find_first(PrintJob, order_id=order_id, shop_id=self.shop_id)
            if existing_job:
                logger.info(f'Print job already exists for order {order_id}: #{existing_job.job_number}')
                return existing_job

            # Create new print job
            print_job = PrintJob()
            print_job.order_id = order_id
            print_job.shop_id = self.shop_id
            print_job.receipt_id = receipt_id
            print_job.order_data = order_data
            print_job.status = JobStatus.PENDING
            print_job.priority = self._calculate_priority(order_data)

            print_job.save()

            logger.info(f'Created print job #{print_job.job_number} for order {order_id}')
            return print_job
        except Exception as e:
            logger.error(f'Error creating print job: {str(e)}')
            return None

    def _calculate_priority(self, order_data: Dict[str, Any]) -> int:
        """Calculate job priority based on order value and type
        """
        priority = 0

        # Higher value orders get higher priority
        total_price = float(order_data.get('total_price', 0))
        if total_price > 500:
            priority += 10
        elif total_price > 200:
            priority += 5
        elif total_price > 100:
            priority += 2

        return priority

    def get_pending_jobs(self, limit: int = 10) -> List[PrintJob]:
        """Get pending jobs for a shop
        """
        if not self.shop_id:
            raise ValueError('shop_id is required')

        jobs = models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.PENDING)

        # Sort by priority (higher first) then by created_at (older first)
        jobs.sort(key=lambda x: (-x.priority, x.created_at))

        return jobs[:limit]

    def get_job_for_device(self, device_id: str) -> Optional[PrintJob]:
        """Get a pending job and assign it to a device
        """
        if not self.shop_id:
            raise ValueError('shop_id is required')

        # Find oldest pending job with highest priority
        job: PrintJob = models.storage.find_first(PrintJob, shop_id=self.shop_id, status=JobStatus.PENDING, order_by='priority', descending=True)
        if job:
            job.mark_as_assigned(device_id)
            job.save()
            logger.info(f'Assigned job #{job.job_number} to device {device_id}')

        return job

    def update_job_status(self, job_id: str, status: str, error_message: str = None) -> Optional[PrintJob]:
        """Update job status
        """
        job: PrintJob = models.storage.find(PrintJob, id=job_id)
        if not job:
            logger.error(f'job {job_id} not found')
            return None

        if status == 'completed':
            job.mark_as_completed()
        elif status == 'failed':
            job.mark_as_failed(error_message or 'Unknown error')
        elif status == 'printing':
            job.mark_as_printing()
        else:
            job.status = JobStatus(status)

        models.storage.save()
        logger.info(f'Job #{job.job_number} status updated to {status}')

        return job

    def retry_failed_jobs(self) -> int:
        """Retry failed jobs that can be retried
        """
        if not self.shop_id:
            raise ValueError('shop_id is required')

        failed_jobs = models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.FAILED)

        retried = 0
        for job in failed_jobs:
            if job.can_retry():
                job.status = JobStatus.PENDING
                job.error_message = None
                job.save()
                retried += 1
                logger.info(f'Retrying job #{job.job_number} (attempt {job.retry_count + 1})')

        return retried

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Delete completed jobs older than specified days
        """
        if not self.shop_id:
            raise ValueError('shop_id is required')

        cutoff_date = datetime.now(UTC) - timedelta(days=days)

        old_jobs = models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.COMPLETED, order_by='created_at')
        deleted = 0
        for job in old_jobs:
            if job.completed_at and job.completed_at < cutoff_date:
                models.storage.delete(job)
                deleted += 1

        models.storage.save()
        logger.info(f'Cleaned up {deleted} old jobs')

        return deleted

    def get_job_stats(self) -> Dict[str, Any]:
        """Get statistics for jobs
        """
        if not self.shop_id:
            raise ValueError('shop_id is required')

        pending = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.PENDING))
        assigned = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.ASSIGNED))
        printing = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.PRINTING))
        completed = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.COMPLETED))
        cancelled = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.CANCELLED))
        failed = len(models.storage.find_all(PrintJob, shop_id=self.shop_id, status=JobStatus.FAILED))

        return {
            'pending': pending,
            'assigned': assigned,
            'printing': printing,
            'completed': completed,
            'failed': failed,
            'cancelled': cancelled,
            'total': pending + assigned + printing + completed + failed + cancelled
        }

    def generate_print_commands(self, print_job: PrintJob) -> Optional[bytes]:
        """Generate ESC/POS commands for a print job
        """
        try:
            order_data = print_job.order_data
            commands = ESCPOSGenerator.generate_receipt(order_data)

            # Store commands as hex
            print_job.print_data = {
                'commands': commands.hex(),
                'size': len(commands),
                'format': 'escpos',
                'generated_at': datetime.now(UTC).isoformat()
            }
            print_job.save()

            logger.info(f"Generated print commands for job {print_job.job_number} ({len(commands)} bytes)")
            return commands
        except Exception as e:
            logger.error(f"Failed to generate print commands: {str(e)}")
            return None

