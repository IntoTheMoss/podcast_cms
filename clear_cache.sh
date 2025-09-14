#!/bin/bash

# Script to clear various caches that might prevent frontend updates

echo "Clearing caches..."

# Clear Nginx cache if it exists
if [ -d "/var/cache/nginx" ]; then
    echo "Clearing Nginx cache..."
    sudo rm -rf /var/cache/nginx/*
fi

# Clear browser cache headers by restarting Nginx
echo "Restarting Nginx to clear cache headers..."
sudo systemctl restart nginx

# Force Django to regenerate static file manifests
echo "Regenerating Django static file manifests..."
cd /var/www/intothemoss_cms
source venv/bin/activate
python manage.py collectstatic --noinput --clear

echo "Cache clearing completed!"
echo "You may also need to:"
echo "1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)"
echo "2. Clear browser cache manually"
echo "3. Check that your browser isn't caching aggressively"