#!/bin/bash
set -e

# Ensure static directory exists and has right permissions
mkdir -p /code/static
chmod -R 777 /code/static

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic command failed"

# Run migrations
echo "Applying database migrations..."
python manage.py migrate || echo "Warning: migrate command failed"

# Fix tree structure if needed
echo "Fixing tree structure..."
python manage.py fixtree || echo "Warning: fixtree command failed"

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn intothemoss_cms.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120