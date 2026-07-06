#!/usr/bin/env bash
set -e

(cd models && FLASK_DEBUG=False python app.py) &
python manage.py migrate
gunicorn crop_disease_detection.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --timeout 180 --workers 1
