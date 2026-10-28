#!/usr/bin/env bash
# One check command. Stops at first failure. Target: under a minute.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
"$PY" -m compileall -q app backend.py worker.py streamlit_app.py
"$PY" -m pytest -q -m "not pg" "$@" 2>&1 | tail -80
