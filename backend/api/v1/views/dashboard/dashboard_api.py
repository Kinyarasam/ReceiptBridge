from datetime import datetime, UTC, timedelta

from flask import request, make_response, jsonify

import models
from api.v1.views import api_bp
from models.device.device import Device
from models.shopify.shopify_store import ShopifyStore
from models.print.print_job import PrintJob, JobStatus


@api_bp.route('/dashboard/stats', methods=['GET'], strict_slashes=False)
def dashboard_stats():
    """Get dashboard statistics as JSON"""
    shop_domain = request.args.get('shop')

    # Get all shops or filter by domain
    if shop_domain:
        shops = models.storage.find_all(ShopifyStore, shop_domain=shop_domain, is_active=True)
    else:
        shops = models.storage.find_all(ShopifyStore, is_active=True)

    total_shops = len(shops)

    # Get all devices
    devices = models.storage.find_all(Device, is_active=True)
    total_devices = len(devices)

    # Calculate online devices (pinged in last 5 minutes)
    cutoff = datetime.now(UTC) - timedelta(minutes=5)
    online_devices = len([d for d in devices if d.last_ping_at and d.last_ping_at > cutoff])

    # Job statistics
    pending_jobs = len(models.storage.find_all(PrintJob, status=JobStatus.PENDING))
    processing_jobs = len(models.storage.find_all(PrintJob, status=JobStatus.PRINTING))
    completed_jobs = len(models.storage.find_all(PrintJob, status=JobStatus.COMPLETED))
    failed_jobs = len(models.storage.find_all(PrintJob, status=JobStatus.FAILED))

    # Today's jobs
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    today_jobs = len([j for j in models.storage.find_all(PrintJob)
                      if j.created_at and j.created_at > today])

    total_processed = completed_jobs + failed_jobs
    success_rate = round((completed_jobs / total_processed * 100) if total_processed > 0 else 0)

    return make_response(jsonify({
        'success': True,
        'stats': {
            'shops': total_shops,
            'devices': {
                'total': total_devices,
                'online': online_devices,
                'offline': total_devices - online_devices
            },
            'jobs': {
                'pending': pending_jobs,
                'processing': processing_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'today': today_jobs
            },
            'performance': {
                'success_rate': success_rate,
                'total_processed': total_processed
            }
        },
        'timestamp': datetime.now(UTC).isoformat()
    }), 200)
