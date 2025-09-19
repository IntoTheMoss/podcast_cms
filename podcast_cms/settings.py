import environ
import os
import sys
from pathlib import Path
from django.core.management.utils import get_random_secret_key

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY", default=get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = [
    f"dev.{env('PODCAST_DOMAIN')}",
    f"{env('PODCAST_DOMAIN')}",
    f"www.{env('PODCAST_DOMAIN')}",
    "localhost",
    "127.0.0.1",
]

# Application definition
INSTALLED_APPS = [
    "home",
    "search",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "podcast",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "podcast_cms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "podcast_cms", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "podcast_cms.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "podcast_cms", "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Media files
if env("SPACES_KEY", default=None):
    # Settings for DigitalOcean Spaces
    AWS_ACCESS_KEY_ID = env("SPACES_KEY")
    AWS_SECRET_ACCESS_KEY = env("SPACES_SECRET")
    AWS_STORAGE_BUCKET_NAME = env("SPACES_BUCKET")
    AWS_S3_ENDPOINT_URL = (
        f"https://{env('SPACES_REGION', default='fra1')}.digitaloceanspaces.com"
    )
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

    # Generate the URL for media files
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.{env('SPACES_REGION', default='fra1')}.cdn.digitaloceanspaces.com"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    MEDIA_URL = "/media/"

# Default storage settings
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# Django sets a maximum of 1000 fields per form by default
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Wagtail settings
WAGTAIL_SITE_NAME = env("SITE_NAME", default="Podcast CMS")

# Search backend
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

# Base URL for Wagtail admin
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL", default="http://localhost:8000")

# Podcast configuration
PODCAST_TITLE = env("PODCAST_TITLE", default="Your Podcast")
PODCAST_SUBTITLE = env(
    "PODCAST_SUBTITLE",
    default="A sunken raft of weeds woven into a verdant morass of sound, song and story",
)
PODCAST_SUMMARY = env(
    "PODCAST_SUMMARY",
    default="Your podcast is a 14 minute drift through original music, soundscapes and liminal yarns",
)
PODCAST_DESCRIPTION = env(
    "PODCAST_DESCRIPTION",
    default="A sunken raft of weeds woven into a verdant morass of sound, song and story. Broadcast on London's Resonance FM every Friday, Your podcast is a 14 minute drift through original music, soundscapes and liminal yarns.",
)
PODCAST_AUTHOR = env("PODCAST_AUTHOR", default="Your Name")
PODCAST_OWNER_NAME = env("PODCAST_OWNER_NAME", default="Your Name")
PODCAST_EMAIL = env("PODCAST_EMAIL", default="your@email.com")
PODCAST_DOMAIN = env("PODCAST_DOMAIN", default="yoursite.com")
PODCAST_COVER_IMAGE = env(
    "PODCAST_COVER_IMAGE", default="/media/original_images/cover.jpg"
)
PODCAST_COPYRIGHT = env("PODCAST_COPYRIGHT", default="© Your Podcast 2025")

# Allowed file extensions for documents in the document library
WAGTAILDOCS_EXTENSIONS = [
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]

# Security settings for production
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = env.list(
        "CSRF_TRUSTED_ORIGINS",
        default=[
            f"https://{env('PODCAST_DOMAIN')}",
            f"https://www.{env('PODCAST_DOMAIN')}",
        ],
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Don't force SSL redirect on localhost
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
if "localhost" in ALLOWED_HOSTS or "127.0.0.1" in ALLOWED_HOSTS:
    SECURE_SSL_REDIRECT = False
