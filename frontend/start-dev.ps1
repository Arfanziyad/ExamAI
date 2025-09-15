# start-dev.ps1 - starts backend and frontend in separate PowerShell windows
# Usage: .\start-dev.ps1

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $repoRoot '..\backend' | Resolve-Path -Relative

# Start backend in a new window
Start-Process powershell -ArgumentList "-NoProfile -NoExit -Command cd '$backendPath'; if (Test-Path 'venv') { .\venv\Scripts\Activate } ; python -m uvicorn main:app --reload --port 8000" -WorkingDirectory $backendPath

# Start frontend in a new window
Start-Process powershell -ArgumentList "-NoProfile -NoExit -Command cd '$PSScriptRoot'; npm run dev" -WorkingDirectory $PSScriptRoot
