import os
import dj_database_url
from .base import *
import logging


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Read secret key from environment variable
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# Read the DATABASE_URL environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    logging.info("Configuring Django to use the DATABASE_URL environment variable")
    # Configure database from DATABASE_URL
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Fallback configuration (should never be used in production)
    logging.warning("DATABASE_URL not found, falling back to default database settings")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "postgres"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

# Log the database config for debugging (remove in production)
logging.info(f"Database config: {DATABASES['default']['ENGINE']}")


ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# Static files - App Platform specific
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Additional locations of static files for collectstatic
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

# Media files - use DO Spaces for production media
if "SPACES_KEY" in os.environ:
    # Settings for DigitalOcean Spaces
    AWS_ACCESS_KEY_ID = os.environ.get("SPACES_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.environ.get("SPACES_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("SPACES_BUCKET_NAME", "intothemoss-media")
    AWS_S3_ENDPOINT_URL = "f{AWS_STORAGE_BUCKET_NAME}.lon1.digitaloceanspaces.com"
    AWS_S3_CUSTOM_DOMAIN = "f{AWS_STORAGE_BUCKET_NAME}.lon1.cdn.digitaloceanspaces.com"

    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # Set your media URL to use the Spaces CDN
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
else:
    # Local media settings (not recommended for production)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    MEDIA_URL = "/media/"

# Security settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
