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

## Flow states

Per `transition.md` ("Steady state"), a flow is steady once its characterisation tests pass and every issue found is logged. Set 2026-10-29.

| Flow | State | Why |
| --- | --- | --- |
| FLOW-01 | steady | Characterisation passes; ISS-10..13 fixed |
| FLOW-02 | steady | Characterisation passes; ISS-21..26 logged (ISS-20 pg hardening open) |
| FLOW-03 | steady | Characterisation passes, including the pg test on local pgvector |
| FLOW-04 | takeover | No characterisation tests yet (ISS-40 blocks its slices) |
| FLOW-05 | takeover | No characterisation tests yet (ISS-50 blocks its slices) |
| FLOW-06 | steady | Characterisation passes; ISS-60, ISS-61 logged |

The takeover finishes when FLOW-04 and FLOW-05 are steady. Slice Owner parallelism stays at 1 until the first release (no deploy pipeline yet, ISS-02).

## FLOW-01 Upload and embed a job description
State: steady
What it does: a recruiter uploads a JD PDF; if identical JD text is already stored, that row is reused; otherwise the text is LLM-extracted into `JDRequirements` (Redis-cached 7 days), embedded locally (bge-small, 384 dims) and stored in `jds` plus one `jd_skill` row per required skill.
Acceptance criteria: REQ-001 to REQ-004 (see characterisation tests)
Diagram: [FLOW-01](flows/web/upload-jd-flow.md)
Characterisation tests: tests/characterisation/test_upload_jd.py, test_embedding_service.py; fixes in tests/flow01/
Known issues: none open. Fixed: ISS-10 (same JD text reuses its row), ISS-11 (per-field embeddings), ISS-12 (no debug prints), ISS-13 (one shared Redis URL default, `app/utils/redis_config.py`).

## FLOW-02 Ingest resumes for a requisition
State: steady
What it does: resumes (PDF, max 10 MB) are saved under unique sanitised names and queued via FastAPI to a Celery worker that extracts them (Redis-cached). Streamlit polls for up to 600 s, then links each completed task's parsed resume without a second LLM call: it upserts the candidate by email + phone (else email alone; a resume without an email is always a new candidate), stores skill embeddings and scores the application.
Acceptance criteria: REQ-005 to REQ-010
Diagram: [FLOW-02](flows/web/ingest-resumes-flow.md)
Characterisation tests: tests/characterisation/test_ingest_resumes_*.py, test_section_extractor.py; fixes in tests/flow02/
Known issues: none open. Fixed: ISS-22 (identity by email + phone, then email), ISS-28 (no resume content on stdout; counts at DEBUG), ISS-01, ISS-21, ISS-23, ISS-24, ISS-25, ISS-26, ISS-27.

## FLOW-03 Score a candidate against a JD
State: steady
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
Known issues: ISS-42 (unescaped names). Evidence threshold 0.72 vs coverage 0.75 is intended (owner, ISS-41).

## FLOW-05 Cache maintenance
State: takeover
What it does: "Clear Entire Redis Cache" runs FLUSHALL.
Acceptance criteria: REQ-014
Diagram: [FLOW-05](flows/web/cache-maintenance-flow.md)
Characterisation tests: none yet.
Known issues: FLUSHALL also wipes the Celery broker and results; "Force Re-parse" checkbox is not wired.

## FLOW-06 Poll task status
State: steady
What it does: `GET /api/v1/task/{id}` maps Celery state to Processing / Completed / Failed.
Acceptance criteria: REQ-015
Diagram: [FLOW-06](flows/api/task-status-flow.md)
Characterisation tests: tests/characterisation/test_ingest_resumes_api.py
Known issues: ISS-60 (STARTED/RETRY reported as Failed; unknown IDs report Processing forever), ISS-61 (no auth). Worker failures now report Failed (ISS-23).
