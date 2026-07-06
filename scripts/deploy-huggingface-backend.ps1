$ErrorActionPreference = "Stop"

if (!$env:HF_TOKEN) {
    throw "HF_TOKEN is missing. Create a Hugging Face token at https://huggingface.co/settings/tokens and run: `$env:HF_TOKEN='your_token'"
}

if (!$env:HF_USERNAME) {
    throw "HF_USERNAME is missing. Run: `$env:HF_USERNAME='your_huggingface_username'"
}

if (!$env:DATABASE_URL) {
    throw "DATABASE_URL is missing. Set it to your Supabase Postgres URL before deploying."
}

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Hf = Join-Path $ProjectRoot ".venv\Scripts\hf.exe"
$RepoId = "$env:HF_USERNAME/cropguard-plant-disease-backend"

if (!(Test-Path $Hf)) {
    throw "Hugging Face CLI not found. Run: .\.venv\Scripts\pip install huggingface_hub"
}

& $Hf repos create $RepoId `
    --repo-type space `
    --space-sdk docker `
    --public `
    --exist-ok `
    --token $env:HF_TOKEN `
    --flavor cpu-basic `
    --env DEBUG=False `
    --env ALLOWED_HOSTS=* `
    --env CORS_ALLOWED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app `
    --env CSRF_TRUSTED_ORIGINS=https://cropguard-plant-disease-detection.vercel.app `
    --env FLASK_SERVICE_URL=http://127.0.0.1:5000 `
    --env SESSION_COOKIE_SECURE=True `
    --env SESSION_COOKIE_SAMESITE=None `
    --secrets DATABASE_URL=$env:DATABASE_URL `
    --secrets SECRET_KEY=$([System.Guid]::NewGuid().ToString("N"))

& $Hf upload $RepoId $ProjectRoot . `
    --repo-type space `
    --token $env:HF_TOKEN `
    --exclude ".git/*" `
    --exclude ".venv/*" `
    --exclude "frontend/node_modules/*" `
    --exclude "frontend/build/*" `
    --exclude "db.sqlite3" `
    --exclude "*.log" `
    --commit-message "Deploy CropGuard backend"

Write-Host "Backend Space:"
Write-Host "https://huggingface.co/spaces/$RepoId"
Write-Host "Backend API URL:"
Write-Host "https://$($env:HF_USERNAME)-cropguard-plant-disease-backend.hf.space"
