#!/usr/bin/env python3
import logging
import sys

from config import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

__all__ = ['logger']
