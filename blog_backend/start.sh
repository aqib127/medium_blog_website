#!/bin/sh

set -e

# Apply database migrations
python manage.py migrate --noinput

# Collect static files unless S3 storage is enabled
if [ "${USE_S3:-False}" != "True" ]; then
    python manage.py collectstatic --noinput
fi

# Start Gunicorn
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120

