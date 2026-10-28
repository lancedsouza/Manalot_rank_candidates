# Survey

## Flows
See `docs/prd.md` FLOW-01..06. All in takeover state.

## Integrations
| Integration | Where | Real or fake | Notes |
| --- | --- | --- | --- |
| Groq LLM (`openai/gpt-oss-20b`) | `app/services/gemini_service.py` | Real (GROQ_API_KEY) | Gemini code is commented out; README is outdated |
| FastEmbed bge-small (384d) | `app/embedding/embedding_service.py` | Real, local CPU | README still says Gemini 768d |
| Postgres + pgvector (Neon) | `app/database/db.py` | Real (DATABASE_URL) | `create_all` at Streamlit start; no migrations tool |
| Redis | cache + Celery broker/backend | Real (REDIS_URL) | Default ports differ: 6380 (resume/embeddings) vs 6379 (JD cache) |

## Platform findings (→ `platform` issues)
1. `start.sh` / `docker-compose.yml` run `backend_api:app`; module is `backend.py` — the API cannot start.
2. `requirements.txt` unpinned; no lockfile; no CI.
3. `pytest` would collect `app/**/test_*.py` scripts that hit live services — `pytest.ini` restricts to `tests/`.

## Security findings (→ Security Reviewer, `risky`)
1. Path traversal: `backend.py` and both processors join `file.filename` into `temp_uploads/`.
2. FLUSHALL button wipes broker + results.
3. Resume PDFs (PII) committed to git.
4. Prompt injection surface: raw JD/resume text in LLM prompts.
5. No auth on API; no upload size limit.

## Open questions for the owner (batched)
1. Which flow goes first? Recommendation: FLOW-02 (fix the filename sanitisation slice) — highest risk, best tested.
2. Remove committed resume PDFs from history? (requires secret/PII rotation thinking, force-push)
3. Where is this deployed today (HF Spaces, Streamlit Cloud, Docker)?
4. Budget, caps and review rhythm (kickoff brief).
