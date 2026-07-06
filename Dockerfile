FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV FLASK_SERVICE_URL=http://127.0.0.1:5000
ENV DEBUG=False
ENV ALLOWED_HOSTS=*
ENV CORS_ALLOWED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
ENV CSRF_TRUSTED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
ENV SESSION_COOKIE_SECURE=True
ENV SESSION_COOKIE_SAMESITE=None

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["bash", "scripts/start-backend.sh"]
