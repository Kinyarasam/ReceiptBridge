#!/usr/bin/env python3
from flask import Blueprint

from api.v1.views.shopify.webhooks import webhook_bp

shopify_bp = Blueprint("shopify_bp", __name__, url_prefix="/shopify")

shopify_auth_bp = Blueprint("shopify_auth", __name__, url_prefix="/auth")

from api.v1.views.shopify.auth import *

shopify_bp.register_blueprint(shopify_auth_bp)
shopify_bp.register_blueprint(webhook_bp)