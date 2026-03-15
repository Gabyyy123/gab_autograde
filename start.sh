#!/bin/bash

# 1. Build the database tables
echo "Applying migrations..."
python manage.py migrate --noinput

# 2. Start the web server
echo "Starting server..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000