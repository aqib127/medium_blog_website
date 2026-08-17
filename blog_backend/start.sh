#!/bin/sh
set -e

# Apply migrations before starting the web server.
python manage.py migrate --noinput

# Collect static files (skipped when S3 storage is configured via USE_S3).
if [ "${USE_S3:-False}" != "True" ]; then
  python manage.py collectstatic --noinput
fi

# Run the ASGI-capable WSGI app with gunicorn.
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 3 --timeout 120
