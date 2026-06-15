#!/usr/bin/env python3
"""Print job endpoints for tablet agent
"""
from flask import request, make_response, jsonify, abort
from sqlalchemy import or_, and_

import models
from models.shopify.shopify_store import ShopifyStore
from models.print.print_job import PrintJob, JobStatus
from api.v1.views.print_job import print_jobs_bp
from services.device_service import DeviceService
from services.print_job_service import PrintJobService
from utils.logger import logger
from utils.pagination import PaginationParams, PaginatedResponse


@print_jobs_bp.route('', methods=['GET'], strict_slashes=False)
def list_jobs():
    """List all print jobs with pagination
    """
    shop_domain = request.headers.get('X-Shop-Domain')
    if not shop_domain:
        abort(401, description='Shop domain is not found')

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if not shop:
        abort(401, description='Shop not found')

    pagination_params = PaginationParams.from_request(default_per_page=20, max_per_page=100)

    # Get filters
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    search = request.args.get('search')


    query = models.storage.query(PrintJob)

    filters = [PrintJob.shop_id == shop.id]

    if status:
        try:
            status_enum = JobStatus(status)
            filters.append(PrintJob.status == status_enum)
        except ValueError:
            pass

    # Search filter
    if search:
        search_filter = or_(
            PrintJob.job_number.ilike(f'%{search}%'),
            PrintJob.order_id.ilike(f'%{search}%'),
        )
        filters.append(search_filter)

    # Handle sorting
    if sort_by == 'status':
        order_by = 'print_jobs.status'
    else:  # joined_at
        order_by = 'created_at'


    # Build query
    query = models.storage.query(PrintJob)

    if search:
        query = query.filter(and_(*filters))

    # # Get total count
    total_items = query.count()

    # apply sorting
    descending = sort_order == 'desc'
    order_column = getattr(PrintJob, order_by)
    if descending:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    jobs = query.offset(pagination_params.offset).limit(pagination_params.per_page).all()
    def serialize_job(job):
        return job.to_dict()

    response = PaginatedResponse(jobs, pagination_params, total_items)
    return response.to_response(item_serializer=serialize_job)


@print_jobs_bp.route('/pending', methods=['GET'])
def get_pending_jobs():
    """Get pending jobs for a shop (for tablet polling)
    """
    shop_domain = request.headers.get('X-Shop-Domain')
    if not shop_domain:
        return make_response(jsonify({
            'error': 'X-Shop-Domain header required'
        }), 400)

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if not shop:
        abort(401, description='Shop not found')

    print_service = PrintJobService(shop_id=shop.id)
    jobs = print_service.get_pending_jobs(limit=10)
    return make_response(jsonify({
        'success': True,
        'jobs': [job.to_dict() for job in jobs]
    }), 200)

@print_jobs_bp.route('/claim', methods=['POST'], strict_slashes=False)
def claim_job():
    """Claim a pending job for printing
    """
    shop_domain = request.headers.get('X-Shop-Domain')
    device_id = request.headers.get('X-Device-ID')

    if not shop_domain or not device_id:
        return make_response(jsonify({
            'error': 'X-Shop-Domain and X-Device-ID headers required'
        }), 400)

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if not shop:
        abort(401, description='Shop not found')

    device_api_key = request.headers.get('X-Device-API-Key')
    if not device_api_key:
        logger.error('X-Device-API-Key header required')
        abort(401)

    device_service = DeviceService(shop_id=shop.id)

    # Authenticate device
    if not device_service.authenticate_device(device_api_key, shop_domain):
        return make_response(jsonify({
            'error': 'unauthorized'
        }), 401)

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if not shop:
        abort(401, description='unauthorized')

    print_service = PrintJobService(shop_id=shop.id)
    job = print_service.get_job_for_device(device_id)

    if not job:
        return make_response(jsonify({
            'success': True,
            'job': None,
            'message': 'No pending jobs available'
        }), 200)

    return make_response(jsonify({
        'success': True,
        'job': job.to_dict()
    }), 200)

@print_jobs_bp.route('/<job_id>/status', methods=['PUT'], strict_slashes=False)
def update_job_status(job_id):
    """Update job status (completed/failed)
    """
    shop_domain = request.headers.get('X-Shop-Domain')
    device_id = request.headers.get('X-Device-ID')

    if not shop_domain or not device_id:
        return make_response(jsonify({
            'error': 'X-Shop-Domain and X-Device-ID headers required'
        }), 400)

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if not shop:
        abort(401, description='Shop not found')

    data = request.get_json()
    status = data.get('status')
    error_message = data.get('error_message')

    if not status or status not in ['completed', 'failed', 'printing']:
        return make_response(jsonify({
            'error': 'Invalid status'
        }), 400)

    print_service = PrintJobService(shop_id=shop.id)
    job = print_service.update_job_status(job_id, status, error_message)

    if not job:
        return make_response(jsonify({
            'error': 'job not found'
        }), 404)

    # Verify device owns the job
    if job.assigned_device_id != device_id:
        return make_response(jsonify({
            'error': 'Unauthorized'
        }), 403)

    return make_response(jsonify({
        'success': True,
        'job': job.to_dict()
    }), 200)

@print_jobs_bp.route('/stats', methods=['GET'], strict_slashes=False)
def get_job_stats():
    """Get job statistics for a shop
    """
    shop_domain = request.headers.get('X-Shop-Domain')

    if not shop_domain:
        return make_response(jsonify({
            'error': 'X-Shop-Domain header required'
        }), 400)

    shop: ShopifyStore = models.storage.find(ShopifyStore, is_active=True, shop_domain=shop_domain)
    if not shop:
        abort(401)

    print_service = PrintJobService(shop_id=shop.id)
    stats = print_service.get_job_stats()

    return make_response(jsonify({
        'success': True,
        'stats': stats
    }), 200)