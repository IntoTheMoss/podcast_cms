#!/bin/bash

# Set up environment variables
export DJANGO_SETTINGS_MODULE=intothemoss_cms.settings
export PYTHONPATH=/var/www/intothemoss_cms

# Go to the project directory
cd /var/www/intothemoss_cms

# Pull the latest changes
git pull

# Activate the virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart gunicorn-intothemoss

# Restart Nginx
sudo systemctl restart nginx

echo "Deployment completed successfully!"