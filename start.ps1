param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Create the virtual environment first. See docs/RUNBOOK.md.'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/node_modules'))) {
    throw 'Run npm ci in frontend first. See docs/RUNBOOK.md.'
}
$previousApiUrl = $env:VITE_API_BASE_URL
try {
    Push-Location (Join-Path $projectRoot 'frontend')
    $env:VITE_API_BASE_URL = '/api'
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally {
    Pop-Location
    $env:VITE_API_BASE_URL = $previousApiUrl
}
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
try {
    Push-Location (Join-Path $projectRoot 'backend')
    Write-Host "FacilityOps: http://127.0.0.1:$Port (loads backend/.env; Ctrl+C stops it)"
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
}
