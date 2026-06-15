#!/usr/bin/env python3
"""Dashboard package initialization
"""
from flask import Blueprint

# Create blueprint here
dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')


# Import routes after blueprint creation
from api.v1.views.dashboard.dashboard import *