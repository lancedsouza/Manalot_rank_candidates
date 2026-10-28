# Issues done

Completed issues moved from `takeover/issuestracker.md`. IDs are kept, never reused.

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

