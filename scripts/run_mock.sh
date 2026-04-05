#!/usr/bin/env bash
# Run Dash UI with APP_MODE=mock (static data). From repo root.
set -euo pipefail
cd "$(dirname "$0")/.."
export APP_MODE=mock
exec python app.py
