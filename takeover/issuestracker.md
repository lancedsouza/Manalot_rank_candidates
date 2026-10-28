# Issues tracker

Staging list for the GitHub Projects board, grouped by flow. Each issue uses the board fields from `transition.md` ("The board"): type label, `flow:<FLOW-ID>`, `module:<name>`, `risky` on risky paths, a column, and blocked-by links. Issue numbers are local (`ISS-NN`) until they are created on GitHub; keep them when they move.

Template:

```
### ISS-NN <title>
Labels:       <slice | characterise | platform | question>, flow:<FLOW-ID>, module:<name>[, risky]
Column:       <Backlog | Ready | Needs you>
Blocked by:   <ISS-NN, ... | none>
Finding:      <what happens today, with file:line evidence>
Acceptance criteria:
- <REQ-NNN> <observable, testable outcome>
```

Usual chain per flow: `characterise` → first `slice` → later slices. A slice on a flow in takeover state is blocked by that flow's `characterise` issue. Completed issues move to `takeover/issues-done.md`.

## Cross-cutting (platform and questions)

### ISS-01 API cannot start: `backend_api:app` module does not exist
Labels:       platform, flow:FLOW-02, module:deploy, risky
Column:       In review (branch fix/flow-02)
Blocked by:   none
Finding:      `start.sh:7` and `docker-compose.yml` run `uvicorn backend_api:app`, but the module is `backend.py`. FLOW-02 and FLOW-06 cannot run in Docker or on HF Spaces.
Acceptance criteria:
- REQ-101 `docker compose up api` serves `GET /docs` with 200.
- REQ-102 `start.sh` starts the API on :8000.

### ISS-02 CI, pinned toolchain and ratchet baselines
Labels:       platform, flow:FLOW-01, module:ci
Column:       Ready
Blocked by:   none
Finding:      No CI, `requirements.txt` unpinned, no lockfile, no lint/coverage/mutation baselines.
Acceptance criteria:
- REQ-103 GitHub Actions runs `./ci/check.sh` on every PR on Python 3.11.
- REQ-104 Dependencies are locked (`uv pip compile`), and the build passes from a clean checkout.
- REQ-105 ruff findings per file, coverage and mutation score are recorded in `ci/baselines/` and can only fall.

### ISS-03 Committed resume PDFs (personal data)
Labels:       question, flow:FLOW-02, module:data, risky
Column:       Needs you
Blocked by:   none
Finding:      `app/pdf/*.pdf` (4 candidate resumes) and `app/jd_data/*.pdf` are in git, with `:Zone.Identifier` files.
Acceptance criteria:
- REQ-106 Owner decides: keep, remove from the tree, or remove from history (force-push).
- REQ-107 If removed, tests use synthetic fixture PDFs only.

### ISS-04 Kickoff decisions
Labels:       question, flow:FLOW-02, module:process
Column:       Needs you
Blocked by:   none
Finding:      Kickoff brief not filled in. First flow, budget, caps, review rhythm and current deployment target (HF Spaces / Streamlit Cloud / Docker) are unknown.
Acceptance criteria:
- REQ-108 Kickoff brief approved; first flow recorded (recommended: FLOW-02).

### ISS-05 Secret and history scan
Labels:       platform, flow:FLOW-02, module:security, risky
Column:       Ready
Blocked by:   none
Finding:      No history scan has run yet. Keys for Groq, Neon and Redis may have been in readable files or old commits.
Acceptance criteria:
- REQ-109 gitleaks (all history), Semgrep and OSV-Scanner results are in `takeover/security.md`.
- REQ-110 Any exposed key is listed for rotation before its first real use.

## FLOW-01 Upload and embed a job description

## FLOW-02 Ingest resumes for a requisition

### ISS-20 Characterise FLOW-02 end to end against pgvector
Labels:       characterise, flow:FLOW-02, module:resume-processor
Column:       Ready (hardening; no longer blocks FLOW-02 slices since FLOW-02 is steady)
Blocked by:   ISS-02
Finding:      Unit-level characterisation exists (`test_ingest_resumes_*.py`). It is not yet checked against a real Postgres + pgvector and the Celery round trip.
Acceptance criteria:
- REQ-117 `pg`-marked tests for `process_and_link_resume` run in CI against a pgvector service container.

### ISS-21 Path traversal through upload filename
Labels:       slice, flow:FLOW-02, module:api, risky
Column:       In review (branch fix/flow-02)
Blocked by:   ISS-01
Finding:      `backend.py` writes to `temp_uploads / file.filename`. `resume_processor.py` and `jd_processor.py` do the same with `uploaded_file.name`. A name like `../../x.pdf` writes outside the folder, and concurrent uploads with the same name overwrite each other.
Acceptance criteria:
- REQ-118 Uploads are stored under a generated unique name inside `temp_uploads/`.
- REQ-119 A filename containing `..` or `/` cannot write outside `temp_uploads/` (test).
- REQ-120 Uploads over a size limit get 413.

### ISS-22 Candidates de-duplicated by name only
Labels:       slice, flow:FLOW-02, module:resume-processor, risky
Column:       Needs you (schema decision: add `candidates.resume_hash` text UNIQUE and match on it; there is no migration tool yet, and `create_all` does not alter existing tables)
Blocked by:   none
Finding:      `process_and_link_resume` updates any existing candidate with the same `name`. Two different people with the same name overwrite each other's data and applications.
Acceptance criteria:
- REQ-121 Identity uses the resume file hash (or another approved key); same-name, different-file resumes create two candidates.

### ISS-23 Worker failures report as task SUCCESS
Labels:       slice, flow:FLOW-02, module:worker, risky
Column:       In review (branch fix/flow-02)
Blocked by:   none
Finding:      `worker.py` catches every exception and returns `{"status": "failed"}`, so Celery marks the task SUCCESS and the API answers "Completed". Characterised in `test_worker_failure_is_swallowed_into_result`.
Acceptance criteria:
- REQ-122 A pipeline failure makes `GET /task/{id}` return `"Failed"` with the error.

### ISS-24 Resume extracted twice: UI re-processes after the worker
Labels:       slice, flow:FLOW-02, module:streamlit
Column:       In review (branch fix/flow-02)
Blocked by:   ISS-23
Finding:      After polling, Streamlit calls `process_and_link_resume` locally and relies on a Redis cache hit. If the worker and UI use different Redis instances, or the worker failed, the LLM runs again in the UI. Failed tasks are still linked.
Acceptance criteria:
- REQ-123 The UI links candidates from the task result and skips failed tasks.
- REQ-124 The LLM is called at most once per resume per ingestion.

### ISS-25 Polling loop has no timeout
Labels:       slice, flow:FLOW-02, module:streamlit
Column:       In review (branch fix/flow-02)
Blocked by:   none
Finding:      `while pending_tasks:` in `streamlit_app.py` loops forever if a task stays PENDING (for example, an unknown id or a worker that is down).
Acceptance criteria:
- REQ-125 Polling stops after a configurable timeout and reports the files that timed out.

### ISS-26 Prompt injection from resume and JD text
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       In review (branch fix/flow-02)
Blocked by:   ISS-05
Finding:      Raw PDF text is pasted into LLM prompts (`extract_jd.py`, `extract_resume.py`) with no delimiting or output sanity checks.
Acceptance criteria:
- REQ-126 Document text is delimited as data in the prompt.
- REQ-127 A resume containing "ignore previous instructions…" still yields schema-valid output (contract test with the fake).

### ISS-27 Real resume extraction fails: Groq json_validate_failed
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       Ready
Blocked by:   none
Finding:      Found 2026-10-29 by a real run against Groq. `extract_resume_data` on `app/pdf/Manalot_Anup_Dubey.pdf` fails with `400 json_validate_failed`, `failed_generation: ''`. It is the same on `main` and on fix/flow-02 (not caused by the ISS-26 prompt change), and JD extraction works. The model (`openai/gpt-oss-20b`, JSON mode, no `max_tokens`) returns an empty generation for the long resume prompt. The old worker hid this by reporting failures as SUCCESS. `extract_resume.py` also prints the Pydantic schema to stdout.
Acceptance criteria:
- REQ-141 The four sample resumes extract successfully against the Groq sandbox (contract test, opt-in).
- REQ-142 Extraction failures carry the provider error code in the task result.

## FLOW-03 Score a candidate against a JD

### ISS-30 Characterise scoring with real pgvector in CI
Labels:       characterise, flow:FLOW-03, module:scoring
Column:       Ready
Blocked by:   ISS-02
Finding:      `test_scores_against_real_pgvector` exists but is skipped without `TEST_DATABASE_URL`.
Acceptance criteria:
- REQ-128 The test runs in CI against a pgvector container.

## FLOW-04 View shortlist and skill evidence

### ISS-40 Characterise shortlist screen
Labels:       characterise, flow:FLOW-04, module:streamlit
Column:       Ready
Blocked by:   ISS-02
Finding:      The queries and badge thresholds (80/65) are inline in `streamlit_app.py`, with no tests.
Acceptance criteria:
- REQ-129 Playwright and pg tests cover: no JDs, no candidates, badge tiers, coverage and evidence rows.

### ISS-41 Evidence threshold (0.72) differs from coverage threshold (0.75)
Labels:       question, flow:FLOW-04, module:scoring
Column:       Needs you
Blocked by:   none
Finding:      `get_candidate_evidence` shows matches ≥ 0.72, but coverage counts only matches ≥ 0.75. Evidence can list skills that coverage does not count.
Acceptance criteria:
- REQ-130 Owner chooses a single threshold or confirms the difference is intended.

### ISS-42 Unescaped HTML from candidate names
Labels:       slice, flow:FLOW-04, module:streamlit, risky
Column:       Backlog
Blocked by:   ISS-40
Finding:      Candidate names come from resume text and are interpolated into `st.markdown(..., unsafe_allow_html=True)`.
Acceptance criteria:
- REQ-131 A name containing `<script>` or other HTML renders as text (test).

## FLOW-05 Cache maintenance

### ISS-50 Characterise cache maintenance controls
Labels:       characterise, flow:FLOW-05, module:streamlit
Column:       Ready
Blocked by:   ISS-02
Finding:      No tests cover the sidebar maintenance controls.
Acceptance criteria:
- REQ-132 Tests cover the clear-cache button's success and error paths.

### ISS-51 "Clear Entire Redis Cache" runs FLUSHALL on the broker
Labels:       slice, flow:FLOW-05, module:cache, risky
Column:       Backlog
Blocked by:   ISS-50
Finding:      `r.flushall()` also deletes the Celery queue and task results, so in-flight ingestion is lost.
Acceptance criteria:
- REQ-133 Clearing deletes only `resume_extract:*`, `jd_cache:*` and `emb:*` keys.
- REQ-134 The Celery queue and results survive a clear (test with fakeredis).

### ISS-52 "Force Re-parse" checkbox is not wired
Labels:       slice, flow:FLOW-05, module:streamlit
Column:       Backlog
Blocked by:   ISS-50, ISS-24
Finding:      `force_refresh_toggle` is never used. Ingestion always passes `force_refresh=False`.
Acceptance criteria:
- REQ-135 With the box ticked, each resume's cache entry is cleared and re-extracted.

## FLOW-06 Poll task status

### ISS-60 Non-terminal and unknown task states misreported
Labels:       slice, flow:FLOW-06, module:api
Column:       Backlog
Blocked by:   ISS-01
Finding:      `GET /task/{id}` reports STARTED and RETRY as "Failed". An unknown id stays "Processing..." forever (Celery reports PENDING). Characterised in `test_task_status_mapping`.
Acceptance criteria:
- REQ-136 STARTED and RETRY return "Processing...".
- REQ-137 Characterisation expectation change approved by owner.

### ISS-61 API has no authentication
Labels:       question, flow:FLOW-06, module:api, risky
Column:       Needs you
Blocked by:   none
Finding:      Both endpoints are open. Anyone who can reach :8000 can upload files and read results, which include candidate PII.
Acceptance criteria:
- REQ-138 Owner decides: network-only access, API key, or SSO.

## Summary

| Flow | Characterise | Slices | Questions | Platform |
| --- | --- | --- | --- | --- |
| Cross-cutting | – | – | ISS-03, ISS-04 | ISS-01, ISS-02, ISS-05 |
| FLOW-01 | (done in sweep) | – (all done) | – | – |
| FLOW-02 | ISS-20 | ISS-21, 22, 23, 24, 25, 26, 27 | – | – |
| FLOW-03 | ISS-30 | – | – | – |
| FLOW-04 | ISS-40 | ISS-42 | ISS-41 | – |
| FLOW-05 | ISS-50 | ISS-51, 52 | – | – |
| FLOW-06 | (done in sweep) | ISS-60 | ISS-61 | – |

Done: ISS-10, 11, 12, 13, 14 (see `takeover/issues-done.md`).
