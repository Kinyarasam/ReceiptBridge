#!/usr/bin/env python3
"""Configuration management
"""
import os

from dotenv import load_dotenv

from config.development import DevelopmentConfig


load_dotenv(verbose=True)

configs = {
    'default': DevelopmentConfig,
}

def get_config():
    """Get configuration based on environment
    """
    env = os.getenv("ENV", 'default')
    return configs.get(env, configs['default'])()

config = get_config()
