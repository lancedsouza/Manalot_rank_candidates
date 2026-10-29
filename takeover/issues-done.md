# Issues done

Completed issues moved from `takeover/issuestracker.md`. IDs are kept, never reused.

### ISS-03 Committed resume PDFs (personal data)
Labels:       question, flow:FLOW-02, module:data, risky
Column:       Done (owner decision 2026-10-29: keep the PDFs in git)
Blocked by:   none
Finding:      `app/pdf/*.pdf` (4 candidate resumes) and `app/jd_data/*.pdf` are in git, with `:Zone.Identifier` files.
Acceptance criteria:
- REQ-106 Owner decides: keep, remove from the tree, or remove from history (force-push).
- REQ-107 If removed, tests use synthetic fixture PDFs only.


### ISS-04 Kickoff decisions
Labels:       question, flow:FLOW-02, module:process
Column:       Done (owner decision 2026-10-29: kickoff settled, FLOW-02 already delivered; move remaining flows to steady state and fix issues flow by flow)
Blocked by:   none
Finding:      Kickoff brief not filled in. First flow, budget, caps, review rhythm and current deployment target (HF Spaces / Streamlit Cloud / Docker) are unknown.
Acceptance criteria:
- REQ-108 Kickoff brief approved; first flow recorded (recommended: FLOW-02).


### ISS-41 Evidence threshold (0.72) differs from coverage threshold (0.75)
Labels:       question, flow:FLOW-04, module:scoring
Column:       Done (owner decision 2026-10-29: keep 0.72 evidence and 0.75 coverage as intended)
Blocked by:   none
Finding:      `get_candidate_evidence` shows matches ≥ 0.72, but coverage counts only matches ≥ 0.75. Evidence can list skills that coverage does not count.
Acceptance criteria:
- REQ-130 Owner chooses a single threshold or confirms the difference is intended.


### ISS-14 Postgres driver missing under SQLAlchemy 2.1
Labels:       platform, flow:FLOW-01, module:deps
Column:       Done (merged to main in f4a2f73, 2026-10-29)
Blocked by:   none
Finding:      `requirements.txt` is unpinned, so it installs SQLAlchemy 2.1.6, which uses the `psycopg` (v3) driver for a plain `postgresql://` URL. Only `psycopg2-binary` was listed, so `app/database/db.py` failed with `ModuleNotFoundError: psycopg`.
Acceptance criteria:
- REQ-139 `requirements.txt` includes `psycopg[binary]`, so a plain `postgresql://` URL connects.
- REQ-140 `.env.example` documents every variable the live code reads.

### ISS-10 JD can be embedded twice: duplicate check compares different titles
Labels:       slice, flow:FLOW-01, module:streamlit
Column:       Done (merged to main in 4d6ccc8, 2026-10-29)
Blocked by:   ISS-02
Finding:      `streamlit_app.py` hides "Embed" only when the filename-derived title is in `jds.title`, but `process_pdf_jd` stores the LLM title (`jd_processor.py`, step 3). The same PDF can create a second `jds` row.
Acceptance criteria:
- REQ-111 Uploading the same JD PDF twice creates one `jds` row.
- REQ-112 The duplicate check uses the stored title or a content hash, not the filename.

### ISS-11 Placeholder zero vectors stored for JD sub-embeddings
Labels:       slice, flow:FLOW-01, module:jd-processor, risky
Column:       Done (merged to main in 4d6ccc8, 2026-10-29)
Blocked by:   ISS-04
Finding:      `education_embedding`, `domain_embedding`, `industries_embedding` and both skill-list embeddings are `[0.0]*384`, and `responsibilities_embedding` copies the full JD embedding. A cosine search on them is meaningless. Characterised in `test_upload_jd.py`.
Acceptance criteria:
- REQ-113 Each sub-embedding is computed from its own field, or the column is null when the field is empty.
- REQ-114 Characterisation expectation change approved by owner (risky PR).

### ISS-12 Debug `print` of extracted JD content
Labels:       slice, flow:FLOW-01, module:jd-processor
Column:       Done (merged to main in 4d6ccc8, 2026-10-29)
Blocked by:   ISS-02
Finding:      `jd_processor.py` prints the title, skills and responsibilities to stdout ("remove once you've confirmed it works").
Acceptance criteria:
- REQ-115 Uses `logging` at DEBUG; nothing is printed at the default level.

### ISS-13 Redis default port differs between caches
Labels:       slice, flow:FLOW-01, module:cache
Column:       Done (merged to main in 4d6ccc8, 2026-10-29)
Blocked by:   ISS-02
Finding:      `extract_jd.py` defaults `REDIS_URL` to :6379, while `resume_cache.py`, `embedding_service.py` and the UI default to :6380. Without the env var the JD cache silently goes offline.
Acceptance criteria:
- REQ-116 One shared Redis config; all caches use the same default.

### ISS-01 API cannot start: `backend_api:app` module does not exist
Labels:       platform, flow:FLOW-02, module:deploy, risky
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   none
Finding:      `start.sh:7` and `docker-compose.yml` run `uvicorn backend_api:app`, but the module is `backend.py`. FLOW-02 and FLOW-06 cannot run in Docker or on HF Spaces.
Acceptance criteria:
- REQ-101 `docker compose up api` serves `GET /docs` with 200.
- REQ-102 `start.sh` starts the API on :8000.

### ISS-21 Path traversal through upload filename
Labels:       slice, flow:FLOW-02, module:api, risky
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   ISS-01
Finding:      `backend.py` writes to `temp_uploads / file.filename`. `resume_processor.py` and `jd_processor.py` do the same with `uploaded_file.name`. A name like `../../x.pdf` writes outside the folder, and concurrent uploads with the same name overwrite each other.
Acceptance criteria:
- REQ-118 Uploads are stored under a generated unique name inside `temp_uploads/`.
- REQ-119 A filename containing `..` or `/` cannot write outside `temp_uploads/` (test).
- REQ-120 Uploads over a size limit get 413.

### ISS-23 Worker failures report as task SUCCESS
Labels:       slice, flow:FLOW-02, module:worker, risky
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   none
Finding:      `worker.py` catches every exception and returns `{"status": "failed"}`, so Celery marks the task SUCCESS and the API answers "Completed". Characterised in `test_worker_failure_is_swallowed_into_result`.
Acceptance criteria:
- REQ-122 A pipeline failure makes `GET /task/{id}` return `"Failed"` with the error.

### ISS-24 Resume extracted twice: UI re-processes after the worker
Labels:       slice, flow:FLOW-02, module:streamlit
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   ISS-23
Finding:      After polling, Streamlit calls `process_and_link_resume` locally and relies on a Redis cache hit. If the worker and UI use different Redis instances, or the worker failed, the LLM runs again in the UI. Failed tasks are still linked.
Acceptance criteria:
- REQ-123 The UI links candidates from the task result and skips failed tasks.
- REQ-124 The LLM is called at most once per resume per ingestion.

### ISS-25 Polling loop has no timeout
Labels:       slice, flow:FLOW-02, module:streamlit
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   none
Finding:      `while pending_tasks:` in `streamlit_app.py` loops forever if a task stays PENDING (for example, an unknown id or a worker that is down).
Acceptance criteria:
- REQ-125 Polling stops after a configurable timeout and reports the files that timed out.

### ISS-26 Prompt injection from resume and JD text
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       Done (merged to main in e68062c, 2026-10-29)
Blocked by:   ISS-05
Finding:      Raw PDF text is pasted into LLM prompts (`extract_jd.py`, `extract_resume.py`) with no delimiting or output sanity checks.
Acceptance criteria:
- REQ-126 Document text is delimited as data in the prompt.
- REQ-127 A resume containing "ignore previous instructions…" still yields schema-valid output (contract test with the fake).

### ISS-27 Real resume extraction fails: Groq json_validate_failed
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       Done (merged to main in f0273d7, 2026-10-29)
Blocked by:   none
Finding:      Found 2026-10-29 by a real run against Groq. `extract_resume_data` on `app/pdf/Manalot_Anup_Dubey.pdf` fails with `400 json_validate_failed`, `failed_generation: ''`. It is the same on `main` and on fix/flow-02 (not caused by the ISS-26 prompt change), and JD extraction works. The model (`openai/gpt-oss-20b`, JSON mode, no `max_tokens`) returns an empty generation for the long resume prompt. The old worker hid this by reporting failures as SUCCESS. `extract_resume.py` also prints the Pydantic schema to stdout.
Acceptance criteria:
- REQ-141 The four sample resumes extract successfully against the Groq sandbox (contract test, opt-in).
- REQ-142 Extraction failures carry the provider error code in the task result.

