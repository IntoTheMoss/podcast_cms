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
python manage.py fixtree

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn intothemoss_cms.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120