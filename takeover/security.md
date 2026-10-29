# Security scans

Results for ISS-05 (REQ-109, REQ-110). Scans ran on 2026-10-29 against branch `platform/iss-05` (based on `platform/iss-02`), from pinned Docker images so nothing was installed on the host.

| Scan | Tool and version | Scope | Result |
| --- | --- | --- | --- |
| Secrets, full history | gitleaks v8.21.2 (`zricethezav/gitleaks:v8.21.2`), `gitleaks git --redact` | All 85 commits on every ref | 0 findings |
| SAST | Semgrep 1.95.0 (`semgrep/semgrep:1.95.0`), rulesets `p/python` and `p/secrets` | Working tree, excluding `.venv`, `.env*`, `temp_uploads` | 6 findings, all false positives (below) |
| Dependencies | OSV-Scanner v1.9.2 (`ghcr.io/google/osv-scanner:v1.9.2`) | `requirements.lock` (94 packages), `requirements-dev.lock` (103 packages) | 0 known vulnerabilities |

The gitleaks scan read git objects only, never the working tree, so `.env` was not read (AGENTS.md). The only env file ever committed is `.env.example`.

## Semgrep findings

All six are `python.sqlalchemy.security.audit.avoid-sqlalchemy-text` in offline maintenance scripts, which the PRD lists as out of scope. Each one interpolates a table or column name from a literal in the same file, never user input, so none is injectable.

| File | Line | Interpolated value comes from |
| --- | --- | --- |
| `app/utils/768_migrate.py` | 47 | `row_count(conn, table)`, called with names from `ALTERS` (line 14) |
| `app/utils/768_migrate.py` | 98 | `ALTERS` literal list |
| `app/utils/clear_all.py` | 20, 25, 31 | Literal tuples of table names |
| `app/utils/clear_stale.py` | 75 | Literal tuple of table names |

No action needed. If these scripts come back into scope, quote identifiers with `sqlalchemy.sql.quoted_name` or a fixed allowlist.

## Secrets inventory

No secret has appeared in git history, so none is listed for rotation (REQ-110). The live code reads these, all from the environment (`.env` locally):

| Variable | Used by | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `app/database/db.py` | Neon in production. Tests never use it; they use `TEST_DATABASE_URL`. |
| `TEST_DATABASE_URL` | `tests/` pg tests | Local pgvector only (`manalot_test` role on the local `pg` container). |
| `GROQ_API_KEY` | `app/services/gemini_service.py` | Tests use a fake value. |
| `REDIS_URL` | `worker.py`, `app/utils/redis_config.py` | |
| `MANALOT_API_KEY` | `app/utils/api_key.py`, `streamlit_app.py` | Added by ISS-61. The API refuses all requests when it is unset. |

## Rerun

```
docker run --rm -v "$PWD:/repo:ro" zricethezav/gitleaks:v8.21.2 git /repo --redact
docker run --rm -v "$PWD:/src:ro" semgrep/semgrep:1.95.0 semgrep scan --config p/python --config p/secrets --metrics=off --exclude .venv --exclude '.env*' /src
docker run --rm -v "$PWD:/src:ro" ghcr.io/google/osv-scanner:v1.9.2 -L requirements.txt:/src/requirements.lock -L requirements.txt:/src/requirements-dev.lock
```
