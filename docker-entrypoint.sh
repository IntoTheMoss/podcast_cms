#!/bin/bash
set -e

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Applying database migrations..."
python manage.py migrate

# Fix tree structure if needed
echo "Fixing tree structure..."
python manage.py fixtree || echo "Warning: fixtree command failed, but continuing..."

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn intothemoss_cms.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 60 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info
