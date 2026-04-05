# Run Dash UI with APP_MODE=mock (static data). From repo root.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:APP_MODE = "mock"
python app.py
