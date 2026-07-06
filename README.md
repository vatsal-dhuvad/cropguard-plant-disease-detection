---
title: CropGuard Plant Disease Backend
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# CropGuard - Plant Disease Detection System

CropGuard is a full-stack plant disease detection project for college/mentor demonstration. It lets users register, upload or capture plant leaf images, run AI-based disease detection, and view scan history with treatment and prevention suggestions.

## Tech Stack

- Frontend: React, Tailwind CSS, Axios
- Backend API: Django, Django REST Framework
- ML service: Flask, TensorFlow/Keras
- Database: SQLite for local demo, Supabase Postgres for production
- Deployment target: Vercel frontend, Hugging Face Spaces Docker backend, Supabase database

Zero-cost backend target for this ML project:

- Hugging Face Spaces Docker backend, because it provides enough free CPU/RAM for TensorFlow demos.

## Live Links

- GitHub Repository: https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection
- Frontend Preview: https://cropguard-plant-disease-detection.vercel.app
- Render Backend Blueprint: https://render.com/deploy?repo=https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection
- Hugging Face Backend: https://vatsal765-cropguard-plant-disease-backend.hf.space
- Supabase Project Ref: `ieukhjamaysxsmtigbfd`

## Main Features

- User registration and login
- Plant disease prediction from uploaded image
- Live camera capture flow
- Confidence score and disease class
- Treatment, prevention, description, and duration details
- User dashboard with total scans, healthy/diseased count, recent detections, and activity timeline

## Local Demo

Use three terminals.

### 1. Flask ML Service

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project"
.\.venv\Scripts\Activate.ps1
cd models
python app.py
```

Health check:

```text
http://127.0.0.1:5000/health
```

### 2. Django Backend

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project"
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver
```

API check:

```text
http://127.0.0.1:8000
```

### 3. React Frontend

For stable preview, use the production build:

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project\frontend"
npm run build
npx -y serve -s build -l 3000
```

Preview:

```text
http://localhost:3000
```

### One-Command Preview Restart

After the frontend has been built once, this script restarts Flask, Django, and the local static frontend for a local preview:

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project"
.\scripts\start-preview.ps1
```

## Demo Login

You can create a new account from the Register screen, or use the local smoke-test account after migrations and test setup:

```text
Email: mentor.demo@gmail.com
Password: DemoPass123
```

## Deployment

Recommended production setup:

- Vercel hosts the React frontend.
- Vercel also proxies `/api/*` requests to Hugging Face so registration/login cookies work from the public frontend URL.
- Hugging Face Spaces hosts the Django backend and local Flask ML service for the zero-cost mentor demo.
- Supabase provides the Postgres database.

See `DEPLOYMENT.md` and `render.yaml` for deployment configuration.

Deploy backend blueprint:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection)

## Environment Files

Copy examples before local customization:

```powershell
copy .env.example .env
copy frontend\.env.example frontend\.env
```

Important production variables:

```text
DATABASE_URL
SECRET_KEY
ALLOWED_HOSTS
CORS_ALLOWED_ORIGINS
CSRF_TRUSTED_ORIGINS
REACT_APP_API_BASE_URL
```

## Mentor Presentation Line

CropGuard is an AI-based plant disease detection platform using React, Django, Flask, TensorFlow, and a trained Keras model. It detects crop disease from plant leaf images, gives confidence and treatment suggestions, and stores user-specific scan history in a dashboard.

For the exact demo order and speaking script, use `PRESENTATION_GUIDE.md`.
