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

## FLOW-02 Ingest resumes for a requisition

### ISS-20 Characterise FLOW-02 end to end against pgvector
Labels:       characterise, flow:FLOW-02, module:resume-processor
Column:       Backlog (hardening; does not block FLOW-02 slices)
Blocked by:   ISS-02
Finding:      Unit-level characterisation exists (`test_ingest_resumes_*.py`). It is not yet checked against a real Postgres + pgvector and the Celery round trip.
Acceptance criteria:
- REQ-117 `pg`-marked tests for `process_and_link_resume` run in CI against a pgvector service container.

### ISS-22 Candidates de-duplicated by name only
Labels:       slice, flow:FLOW-02, module:resume-processor, risky
Column:       Needs you (schema decision, see Finding)
Blocked by:   none
Finding:      `process_and_link_resume` updates any existing candidate with the same `name`. Two different people with the same name overwrite each other's data and applications.
Options:      match on file hash (simple; an updated resume becomes a new row) or on email/phone with hash fallback (needs extraction change + migration). No migration tool exists yet.
Acceptance criteria:
- REQ-121 Identity uses the resume file hash (or another approved key); same-name, different-file resumes create two candidates.

### ISS-28 Resume extraction prints candidate data to stdout
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       Ready
Blocked by:   none
Finding:      `extract_resume.py` still prints the validated resume and every responsibility (24 to 132 lines per resume), so candidate PII goes to worker logs. Extraction also varies run to run: the same resume gave 75 skills and then 28.
Acceptance criteria:
- REQ-143 No resume content is printed; details go to logging at DEBUG.
- REQ-144 Variance is measured across 3 runs per sample resume and recorded in takeover/test-health.md.

## FLOW-03 Score a candidate against a JD

### ISS-30 Characterise scoring with real pgvector in CI
Labels:       characterise, flow:FLOW-03, module:scoring
Column:       Backlog
Blocked by:   ISS-02
Finding:      `test_scores_against_real_pgvector` exists but is skipped without `TEST_DATABASE_URL`.
Acceptance criteria:
- REQ-128 The test runs in CI against a pgvector container.

## FLOW-04 View shortlist and skill evidence

### ISS-40 Characterise shortlist screen
Labels:       characterise, flow:FLOW-04, module:streamlit
Column:       Backlog
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
Column:       Backlog
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
Blocked by:   ISS-50
Finding:      `force_refresh_toggle` is never used. Ingestion always passes `force_refresh=False`.
Acceptance criteria:
- REQ-135 With the box ticked, each resume's cache entry is cleared and re-extracted.

## FLOW-06 Poll task status

### ISS-60 Non-terminal and unknown task states misreported
Labels:       slice, flow:FLOW-06, module:api
Column:       Ready
Blocked by:   none
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

| Area | Open issues |
| --- | --- |
| Cross-cutting | ISS-02 platform (Ready), ISS-03 question (Needs you), ISS-04 question (Needs you), ISS-05 platform (Ready) |
| FLOW-01 | – (none open) |
| FLOW-02 | ISS-20 characterise (Backlog), ISS-22 slice (Needs you), ISS-28 slice (Ready) |
| FLOW-03 | ISS-30 characterise (Backlog) |
| FLOW-04 | ISS-40 characterise (Backlog), ISS-41 question (Needs you), ISS-42 slice (Backlog) |
| FLOW-05 | ISS-50 characterise (Backlog), ISS-51 slice (Backlog), ISS-52 slice (Backlog) |
| FLOW-06 | ISS-60 slice (Ready), ISS-61 question (Needs you) |

Done: ISS-01, ISS-10, ISS-11, ISS-12, ISS-13, ISS-14, ISS-21, ISS-23, ISS-24, ISS-25, ISS-26, ISS-27 (see `takeover/issues-done.md`).
