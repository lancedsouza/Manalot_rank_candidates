# Manalot Rank Candidates — PRD

## Purpose
Help a recruiter shortlist candidates for a job description (JD): upload a JD PDF and resume PDFs, extract structured fields with an LLM, embed them, and rank candidates by a hybrid of semantic similarity and JD-skill coverage, with the matching skills shown as evidence.

## Users
- Recruiter (single user, no login) using the Streamlit UI.
- Internal API clients of the FastAPI service.

## Out of scope (for now)
- Evidence matching beyond skills (responsibilities, education, domain) — the README's "planned" stages.
- Offline scripts: `app/services/rank_candidates.py` CLI, `app/utils/clear_all.py`, `clear_stale.py`, `768_migrate.py`, `app/database/create_tables.py`.
- Ad-hoc scripts named `test_*.py` under `app/` (they call live services; they are not tests).

## FLOW-01 Upload and embed a job description
State: takeover
What it does: a recruiter uploads a JD PDF; the text is LLM-extracted into `JDRequirements` (Redis-cached 7 days), embedded locally (bge-small, 384 dims) and stored in `jds` plus one `jd_skill` row per required skill.
Acceptance criteria: REQ-001 to REQ-004 (see characterisation tests)
Diagram: [FLOW-01](flows/web/upload-jd-flow.md)
Characterisation tests: tests/characterisation/test_upload_jd.py, test_embedding_service.py
Known issues: duplicate check compares the filename-derived title with the LLM title, so the same JD can be re-embedded; non-skill embeddings are zero placeholders.

## FLOW-02 Ingest resumes for a requisition
State: takeover
What it does: resumes are queued via FastAPI to a Celery worker that warms the Redis resume cache; Streamlit then re-processes each file locally, upserts the candidate by name, stores skill embeddings and scores the application.
Acceptance criteria: REQ-005 to REQ-010
Diagram: [FLOW-02](flows/web/ingest-resumes-flow.md)
Characterisation tests: tests/characterisation/test_ingest_resumes_*.py, test_section_extractor.py
Known issues: candidates de-duplicated by name only; upload filename used unsanitised as a path; worker failures report as task SUCCESS; extraction runs twice when worker and UI use different Redis.

## FLOW-03 Score a candidate against a JD
State: takeover
What it does: hybrid = 0.20·parent cosine + 0.55·coverage (JD skills with best match ≥ 0.75) + 0.25·mean matched depth.
Acceptance criteria: REQ-011, REQ-012
Diagram: [FLOW-03](flows/web/score-candidate-flow.md)
Characterisation tests: tests/characterisation/test_score_candidate.py
Known issues: none logged.

## FLOW-04 View shortlist and skill evidence
State: takeover
What it does: lists top-N applications by hybrid score with badges (≥80 Top, ≥65 Strong, else Moderate), coverage and up to 10 skill matches ≥ 0.72.
Acceptance criteria: REQ-013
Diagram: [FLOW-04](flows/web/view-shortlist-flow.md)
Characterisation tests: none yet — queries live inline in `streamlit_app.py` (needs pg + Playwright).
Known issues: evidence threshold (0.72) differs from coverage threshold (0.75).

## FLOW-05 Cache maintenance
State: takeover
What it does: "Clear Entire Redis Cache" runs FLUSHALL.
Acceptance criteria: REQ-014
Diagram: [FLOW-05](flows/web/cache-maintenance-flow.md)
Characterisation tests: none yet.
Known issues: FLUSHALL also wipes the Celery broker and results; "Force Re-parse" checkbox is not wired.

## FLOW-06 Poll task status
State: takeover
What it does: `GET /api/v1/task/{id}` maps Celery state to Processing / Completed / Failed.
Acceptance criteria: REQ-015
Diagram: [FLOW-06](flows/api/task-status-flow.md)
Characterisation tests: tests/characterisation/test_ingest_resumes_api.py
Known issues: STARTED/RETRY reported as Failed; unknown IDs report Processing forever.
