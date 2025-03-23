import os
import sys
import dj_database_url
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

# Read secret key from environment variable
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")

# Allow all host headers from App Platform
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# Development mode for local testing
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"

# Database configuration
if DEVELOPMENT_MODE is True:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
elif len(sys.argv) > 0 and sys.argv[1] != "collectstatic":
    if os.getenv("DATABASE_URL", None) is None:
        raise Exception("DATABASE_URL environment variable not defined")
    DATABASES = {
        "default": dj_database_url.parse(os.environ.get("DATABASE_URL")),
    }

# Static files configuration
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Media files - use DO Spaces for production media
if "SPACES_KEY" in os.environ:
    # Settings for DigitalOcean Spaces
    AWS_ACCESS_KEY_ID = os.environ.get("SPACES_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.environ.get("SPACES_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("SPACES_BUCKET_NAME", "intothemoss-media")
    AWS_S3_ENDPOINT_URL = (
        f"https://{os.environ.get('SPACES_REGION', 'fra1')}.digitaloceanspaces.com"
    )
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # Generate the URL for media files
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.{os.environ.get('SPACES_REGION', 'fra1')}.cdn.digitaloceanspaces.com"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
else:
    # Local media settings (not recommended for production)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    MEDIA_URL = "/media/"

# Security settings
CSRF_TRUSTED_ORIGINS = [
    "https://*.ondigitalocean.app",
    "https://dev.intothemoss.com",
    "https://www.intothemoss.com",
]
