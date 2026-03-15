#!/bin/bash

# 1. Build the database tables automatically
echo "BUILDING DATABASE..."
python manage.py migrate --noinput

# 2. Start the web server
echo "STARTING SERVER..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000