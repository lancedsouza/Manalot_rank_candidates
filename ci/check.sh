#!/usr/bin/env bash
# One check command. Stops at first failure. Target: under a minute.
# Local: offline tests only. CI also sets TEST_DATABASE_URL, so the pg tests run too.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
"$PY" -m compileall -q app backend.py worker.py streamlit_app.py
"$PY" ci/ratchet.py lint
if [ -n "${TEST_DATABASE_URL:-}" ]; then MARK=""; else MARK="not pg"; fi
"$PY" -m pytest -q -m "$MARK" "$@" 2>&1 | tail -80
