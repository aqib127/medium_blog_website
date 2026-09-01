#!/bin/sh

set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
# Railway uses ephemeral storage; using Whitenoise is better, but collecting is safe.
python manage.py collectstatic --noinput --clear

echo "Starting Gunicorn..."
# Bind to the dynamic Railway port. Default to 8000 for local testing.
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120 \
    --access-logfile '-' \
    --error-logfile '-'