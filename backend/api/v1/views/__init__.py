#!/usr/bin/env python3
"""Blueprints for the views
"""
from flask import Blueprint

from api.v1.views.shopify import shopify_bp
from api.v1.views.dashboard import dashboard_bp
from api.v1.views.device import device_bp
from api.v1.views.print_job import print_jobs_bp

api_bp = Blueprint("app_views", __name__, url_prefix="/api/v1")

api_bp.register_blueprint(shopify_bp)
api_bp.register_blueprint(device_bp)
api_bp.register_blueprint(print_jobs_bp)

__all__ = ['api_bp', 'dashboard_bp']