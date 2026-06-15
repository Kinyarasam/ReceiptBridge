#!/usr/bin/env python3
"""Base configuration class with common settings.
"""
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(verbose=True)


class Config(object):
    """Base configuration class with common settings.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get('LOG_FILE', str(BASE_DIR / 'logs' / 'app.log'))

    DATABASE_TYPE = os.getenv("DATABASE_TYPE", 'sqlite')
    DATABASE_PATH = os.getenv("DATABASE_PATH", str('sqlite.db'))

    # Database URLs
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """Get database URL based on DATABASE_TYPE
        """
        user = os.getenv("DATABASE_USER")
        password = os.getenv("DATABASE_PASSWORD")
        port = os.getenv("DATABASE_PORT")
        db_name = os.getenv("DATABASE_NAME")
        host = os.getenv("DATABASE_HOST")

        if self.DATABASE_TYPE == 'sqlite':
            return f"sqlite:///{self.DATABASE_PATH}"
        elif self.DATABASE_TYPE == 'postgres':
            return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        elif self.DATABASE_TYPE == 'mysql':
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.DATABASE_TYPE}")

    # Flask Server
    SERVER_HOST = os.getenv("SERVER_HOST", '0.0.0.0')
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))
    SERVER_DEBUG = str(os.getenv("SERVER_DEBUG")).lower() == 'true'
    FLASK_ENV = os.getenv("FLASK_ENV", 'development')
    SECRET_KEY = os.getenv("SECRET_KEY", 'EaPbJMdF3XgMlxl8p75QKTGa3d3eLqipYI41mcaLkWAULQuY7RD8QzOjaIrWK9eSoN0WaOZG9V8qM19l9S1HJw==')

    # Session settings
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = os.environ.get('SESSION_KEY_PREFIX', 'home_apparel_')

    APP_URL = os.getenv('APP_URL', '')

    SHOPIFY_CLIENT_ID = os.getenv('SHOPIFY_CLIENT_ID')
    SHOPIFY_CLIENT_SECRET = os.getenv('SHOPIFY_CLIENT_SECRET')
    SHOPIFY_SCOPE = os.getenv('SHOPIFY_SCOPE')
    SHOPIFY_STATE_TOKEN = os.getenv('SHOPIFY_STATE_TOKEN')

    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration settings."""
        # Create necessary directories
        # os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

        # Set secret key
        app.config['SECRET_KEY'] = cls.SECRET_KEY
