#!/usr/bin/env python3
from flask import Blueprint


print_jobs_bp = Blueprint('print_jobs_bp', __name__, url_prefix='/jobs')

from .print_job import *