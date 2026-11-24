"""
Professional Configuration Module for Smart E-Commerce Management System.
Handles environment variables, security configurations, database connections,
and business logic constants.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Base project directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment configuration from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Application configuration parameters."""

    # Security & Session Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "smart-ecommerce-production-secret-key-2026")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Database Configuration (Defaults to persistent local SQLite)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'ecommerce.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Application Settings
    APP_NAME = "SmartCommerce Health & Operations"
    APP_VERSION = "2.5.0"
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Business Health Thresholds & Defaults
    DEFAULT_LOW_STOCK_THRESHOLD = 10
    CRITICAL_STOCK_THRESHOLD = 3
    DEFAULT_PAGE_SIZE = 10
    CURRENCY_SYMBOL = "₹"
    CURRENCY_CODE = "INR"

    # Tax & Commercial Rates
    STANDARD_TAX_RATE = 0.18  # 18% GST standard

    # Export & File Storage Directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports", "exports")
