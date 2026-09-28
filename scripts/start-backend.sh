#!/usr/bin/env bash
set -e

(cd models && FLASK_DEBUG=False python app.py) &

# Keep the public demo online if a managed database is temporarily unavailable.
# When DATABASE_URL works, this remains the normal Supabase-backed startup.
if python manage.py migrate; then
  exec gunicorn crop_disease_detection.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --timeout 180 --workers 1
fi

echo "Database connection failed; starting with the bundled SQLite demo database." >&2
unset DATABASE_URL
python manage.py migrate
exec gunicorn crop_disease_detection.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --timeout 180 --workers 1
