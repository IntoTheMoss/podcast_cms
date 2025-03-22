import os
import dj_database_url
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Read secret key from environment variable
SECRET_KEY = os.environ.get("SECRET_KEY", "")

# Parse database configuration from $DATABASE_URL
DATABASES = {"default": dj_database_url.config(default=os.environ.get("DATABASE_URL"))}

# Allow all host headers from App Platform
ALLOWED_HOSTS = ["*.ondigitalocean.app", "dev.intothemoss.com", "www.intothemoss.com"]

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
    AWS_ACCESS_KEY_ID = os.environ.get("SPACES_KEY")
    AWS_SECRET_ACCESS_KEY = os.environ.get("SPACES_SECRET")
    AWS_STORAGE_BUCKET_NAME = os.environ.get("SPACES_BUCKET", "intothemoss-media")
    AWS_S3_ENDPOINT_URL = "https://fra1.digitaloceanspaces.com"
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.fra1.digitaloceanspaces.com"
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
