#!/usr/bin/env python3
from flask import Blueprint

webhook_bp = Blueprint("shopify_webhooks", __name__, url_prefix="/webhooks")

from .paid_orders import *