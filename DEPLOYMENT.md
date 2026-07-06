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
- Temporary backend tunnel: https://cropguard-vatsal-demo.loca.lt
- Hugging Face backend: pending Space deployment
- Render blueprint: https://render.com/deploy?repo=https://github.com/vatsal-dhuvad/cropguard-plant-disease-detection
- Supabase project ref: `ieukhjamaysxsmtigbfd`

## Hugging Face Spaces Backend

Create a Docker Space and push this repository. Set these Space variables/secrets:

```text
DATABASE_URL=postgresql://postgres:<password>@db.ieukhjamaysxsmtigbfd.supabase.co:5432/postgres
SECRET_KEY=<generated secret>
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
CSRF_TRUSTED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app
FLASK_SERVICE_URL=http://127.0.0.1:5000
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
```

Then update Vercel:

```text
REACT_APP_API_BASE_URL=https://<your-space-subdomain>.hf.space
```

## Render Backend Environment Variables

Set these on Render:

```text
DEBUG=False
SECRET_KEY=<generated secret>
ALLOWED_HOSTS=<your-render-host>
CORS_ALLOWED_ORIGINS=https://<your-vercel-app>
CSRF_TRUSTED_ORIGINS=https://<your-vercel-app>
DATABASE_URL=postgresql://postgres:<password>@db.ieukhjamaysxsmtigbfd.supabase.co:5432/postgres
FLASK_SERVICE_URL=http://localhost:5000
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=None
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

## Frontend Environment Variables

Set this on Vercel:

```text
REACT_APP_API_BASE_URL=https://<your-render-backend>
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
