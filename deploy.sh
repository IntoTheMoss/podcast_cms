#!/bin/bash

# Set up environment variables
export DJANGO_SETTINGS_MODULE=intothemoss_cms.settings
export PYTHONPATH=/var/www/intothemoss_cms

# Go to the project directory
cd /var/www/intothemoss_cms

echo "Starting deployment..."

# Pull the latest changes
echo "Pulling latest changes..."
git pull

# Check if there were any changes
if [ $? -ne 0 ]; then
    echo "Git pull failed! Exiting..."
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing/updating dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Clear old static files to prevent caching issues
echo "Clearing old static files..."
rm -rf staticfiles/*

# Collect static files with cache busting
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run system check
echo "Running Django system check..."
python manage.py check --deploy

# Restart Gunicorn
echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn-intothemoss

# Check Gunicorn status
if ! sudo systemctl is-active --quiet gunicorn-intothemoss; then
    echo "Error: Gunicorn failed to restart!"
    sudo systemctl status gunicorn-intothemoss
    exit 1
fi

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

# Check Nginx status
if ! sudo systemctl is-active --quiet nginx; then
    echo "Error: Nginx failed to restart!"
    sudo systemctl status nginx
    exit 1
fi

echo "Deployment completed successfully!"
echo "Services status:"
echo "  Gunicorn: $(sudo systemctl is-active gunicorn-intothemoss)"
echo "  Nginx: $(sudo systemctl is-active nginx)"