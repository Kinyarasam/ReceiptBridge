#!/usr/bin/env python3
from flask import Blueprint


device_bp = Blueprint('device_bp', __name__, url_prefix='/devices')

from .device import *