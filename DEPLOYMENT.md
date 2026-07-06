# CropGuard Deployment

## Recommended Production Shape

- Frontend: Vercel
- Backend: Hugging Face Spaces Docker for zero-cost ML demo, or Render paid/larger instance for production
- Database: Supabase Postgres
- ML model: bundled with backend service as `models/trained_modelNew.h5`

Supabase is used as the database. It does not run the Django, Flask, or TensorFlow backend.

## Current Project Links

- GitHub: https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection
- Vercel frontend: https://cropguard-plant-disease-detection.vercel.app
- Hugging Face backend: https://vatsal765-cropguard-plant-disease-backend.hf.space
- Render blueprint: https://render.com/deploy?repo=https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection
- Supabase project ref: `ieukhjamaysxsmtigbfd`

## Hugging Face Spaces Backend

Create a Docker Space and push this repository. Set these Space variables/secrets:

```text
DATABASE_URL=postgresql://postgres.ieukhjamaysxsmtigbfd:<password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
SECRET_KEY=<generated secret>
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
CSRF_TRUSTED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
FLASK_SERVICE_URL=http://127.0.0.1:5000
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
```

Use the Supabase pooler URL for Hugging Face. The direct database host only returns an IPv6 address for this project and can fail on Hugging Face with `Network is unreachable`.

Then update Vercel:

```text
REACT_APP_API_BASE_URL=https://vatsal765-cropguard-plant-disease-backend.hf.space
```

Helper script:

```powershell
$env:HF_TOKEN="your_huggingface_token"
$env:HF_USERNAME="your_huggingface_username"
$env:DATABASE_URL="postgresql://postgres.ieukhjamaysxsmtigbfd:<password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"
.\scripts\deploy-huggingface-backend.ps1
```

## Render Backend Environment Variables

Set these on Render:

```text
DEBUG=False
SECRET_KEY=<generated secret>
ALLOWED_HOSTS=<your-render-host>
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>
CSRF_TRUSTED_ORIGINS=https://<your-vercel-app>
DATABASE_URL=postgresql://postgres.ieukhjamaysxsmtigbfd:<password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
FLASK_SERVICE_URL=http://localhost:5000
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

## Frontend Environment Variables

Set this on Vercel:

```text
REACT_APP_API_BASE_URL=https://vatsal765-cropguard-plant-disease-backend.hf.space
```

## Local Run

Terminal 1:

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project"
.\.venv\Scripts\Activate.ps1
cd models
python app.py
```

Terminal 2:

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project"
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

Terminal 3:

```powershell
cd "C:\Users\vatsa\OneDrive\Desktop\001 7th sem project\frontend"
npm start
```
