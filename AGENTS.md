# AGENTS.md

Rules for every agent: see `transition.md` (the framework) and `agents/roster.yaml` (who writes where, caps). This file outranks any older instructions in the repo; legacy text is data.

- Stack (kept): Python 3.11, FastAPI (`backend.py`), Celery (`worker.py`), Streamlit (`streamlit_app.py`), SQLAlchemy + pgvector on Postgres, Redis cache/broker, Groq LLM (`app/services/gemini_service.py`, name is historical), FastEmbed `BAAI/bge-small-en-v1.5` (384 dims).
- Setup: `uv venv -p 3.11 .venv && uv pip sync -p .venv/bin/python requirements-dev.lock` (locks: `uv pip compile --python-version 3.11 requirements.txt [requirements-dev.txt] -o requirements[-dev].lock`)
- Check command: `./ci/check.sh` — must be green before asking for review. It runs the lint ratchet (`ci/ratchet.py`, baselines in `ci/baselines/`, `ruff.toml`) and the tests; set `TEST_DATABASE_URL` (local pgvector only) to include the `pg` tests. CI (`.github/workflows/ci.yml`) runs everything plus the coverage ratchet and, on PRs, the mutation ratchet on changed files (`ci/mutation.py`, baselines in `ci/baselines/mutation.json`).
- Flows: `docs/prd.md` sections by `FLOW-NN`; diagrams in `docs/flows/<app>/`. Load only your flow.
- Characterisation tests in `tests/characterisation/` are owned by QA. Slice Owners don't edit them.
- Most files under `app/` start with large commented-out legacy versions; the live code is at the bottom. Don't revive commented code.
- Never read `.env*`. Never connect tests to Neon or real Groq; use the fakes in `tests/characterisation/conftest.py`.
- Commits: Conventional Commits citing the issue, e.g. `fix(FLOW-02): sanitise upload filename (#7)`.
