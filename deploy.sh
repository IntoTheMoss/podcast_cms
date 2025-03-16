#!/bin/bash

# Set up environment variables
export DJANGO_SETTINGS_MODULE=intothemoss_cms.settings.production
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
sudo systemctl restart gunicorn

# Restart Nginx
sudo systemctl restart nginx

# Run the legacy SPA deploy script for backward compatibility
# This ensures the old site's RSS feed is updated
if [ -f /path/to/old/deploy.sh ]; then
    /path/to/old/deploy.sh
fi

echo "Deployment completed successfully!"
