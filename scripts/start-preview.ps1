$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Frontend = Join-Path $ProjectRoot "frontend"

if (!(Test-Path $Python)) {
    throw "Python virtual environment not found. Run: py -3.10 -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

$env:CORS_ALLOWED_ORIGINS = "https://cropguard-plant-disease-detection.vercel.app"
$env:CSRF_TRUSTED_ORIGINS = "https://cropguard-plant-disease-detection.vercel.app"
$env:SESSION_COOKIE_SECURE = "True"
$env:SESSION_COOKIE_SAMESITE = "None"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,.loca.lt,.trycloudflare.com"

Get-CimInstance Win32_Process |
    Where-Object {
        ($_.Name -eq "python.exe" -and $_.CommandLine -like "*001 7th sem project*") -or
        ($_.Name -eq "node.exe" -and ($_.CommandLine -like "*localtunnel*" -or $_.CommandLine -like "*serve*"))
    } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Start-Process -FilePath $Python `
    -ArgumentList "app.py" `
    -WorkingDirectory (Join-Path $ProjectRoot "models") `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $ProjectRoot "flask.out.log") `
    -RedirectStandardError (Join-Path $ProjectRoot "flask.err.log")

Start-Sleep -Seconds 12

Start-Process -FilePath $Python `
    -ArgumentList "manage.py runserver 127.0.0.1:8000" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $ProjectRoot "django.out.log") `
    -RedirectStandardError (Join-Path $ProjectRoot "django.err.log")

Start-Sleep -Seconds 8

Start-Process -FilePath "npx.cmd" `
    -ArgumentList "-y serve -s build -l 3000" `
    -WorkingDirectory $Frontend `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $ProjectRoot "serve.out.log") `
    -RedirectStandardError (Join-Path $ProjectRoot "serve.err.log")

Start-Process -FilePath "npx.cmd" `
    -ArgumentList "-y localtunnel --port 8000 --local-host 127.0.0.1 --subdomain cropguard-vatsal-demo" `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $ProjectRoot "tunnel.out.log") `
    -RedirectStandardError (Join-Path $ProjectRoot "tunnel.err.log")

Start-Sleep -Seconds 15

Write-Host "Local frontend:  http://localhost:3000"
Write-Host "Local backend:   http://127.0.0.1:8000"
Write-Host "Flask health:    http://127.0.0.1:5000/health"
Write-Host "Tunnel backend:  https://cropguard-vatsal-demo.loca.lt"
Write-Host "Vercel frontend: https://cropguard-plant-disease-detection.vercel.app"
