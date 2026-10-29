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
Column:       In review (branch platform/iss-02)
Blocked by:   none
Finding:      No CI, `requirements.txt` unpinned, no lockfile, no lint/coverage/mutation baselines.
Acceptance criteria:
- REQ-103 GitHub Actions runs `./ci/check.sh` on every PR on Python 3.11.
- REQ-104 Dependencies are locked (`uv pip compile`), and the build passes from a clean checkout.
- REQ-105 ruff findings per file, coverage and mutation score are recorded in `ci/baselines/` and can only fall.

### ISS-62 Loop keeps PR branches current and merges on green + approval
Labels:       platform, flow:FLOW-01, module:ci
Column:       In review (branch platform/iss-62)
Blocked by:   none
Finding:      Several PRs are open at once and nothing keeps them current with main, starts reviews or merges them.
Acceptance criteria:
- REQ-147 `ci/loop.sh` merges origin/main into each open PR branch in its own worktree (merge, never rebase, never force-push), runs `./ci/check.sh`, then pushes.
- REQ-148 On conflict it runs `slice-owner` (30 turns) to resolve; if it cannot or the check fails, it aborts the merge, labels the PR `needs-you` and comments why.
- REQ-149 On green CI with no review it starts `reviewer` (plus `security-reviewer` on `risky_paths` from `agents/roster.yaml`); non-risky, approved, green PRs get `gh pr merge --squash --auto`; risky PRs get `needs-you` and are never merged.
- REQ-150 `ci/loop.sh --dry-run` only prints actions; turns and cost are posted on the PR when `claude` reports them.

### ISS-05 Secret and history scan
Labels:       platform, flow:FLOW-02, module:security, risky
Column:       In review (branch platform/iss-05, stacked)
Blocked by:   none
Finding:      No history scan has run yet. Keys for Groq, Neon and Redis may have been in readable files or old commits.
Acceptance criteria:
- REQ-109 gitleaks (all history), Semgrep and OSV-Scanner results are in `takeover/security.md`.
- REQ-110 Any exposed key is listed for rotation before its first real use.

### ISS-15 Mutation score on changed files
Labels:       platform, flow:FLOW-02, module:ci
Column:       In review (branch platform/iss-15, stacked)
Blocked by:   none
Finding:      Split from ISS-02, which landed the lint and coverage ratchets. No mutation testing runs yet, so tests that can never fail would not be caught.
Acceptance criteria:
- REQ-145 CI runs mutmut on the Python files a PR changes and records the score in `ci/baselines/mutation.json`.
- REQ-146 The score on changed files may not fall.

## FLOW-02 Ingest resumes for a requisition

### ISS-20 Characterise FLOW-02 end to end against pgvector
Labels:       characterise, flow:FLOW-02, module:resume-processor
Column:       In review (branch platform/iss-02)
Blocked by:   ISS-02
Finding:      Unit-level characterisation exists (`test_ingest_resumes_*.py`). It is not yet checked against a real Postgres + pgvector and the Celery round trip.
Acceptance criteria:
- REQ-117 `pg`-marked tests for `process_and_link_resume` run in CI against a pgvector service container.

### ISS-22 Candidates de-duplicated by name only
Labels:       slice, flow:FLOW-02, module:resume-processor, risky
Column:       In review (branch slice/iss-22, stacked)
Blocked by:   none
Finding:      `process_and_link_resume` updates any existing candidate with the same `name`. Two different people with the same name overwrite each other's data and applications.
Decision:     Owner, 2026-10-29: match on email + phone; if no match, match on email alone. Name is no longer an identity key.
Note:         Contacts are parsed from raw resume text (`app/utils/contact_extractor.py`), not the LLM. A resume with no email always creates a new candidate. Existing rows have no email until re-ingested.
Acceptance criteria:
- REQ-121 A resume updates an existing candidate only when email and phone both match, or failing that when email matches; same-name resumes with different contacts create two candidates.

### ISS-28 Resume extraction prints candidate data to stdout
Labels:       slice, flow:FLOW-02, module:llm, risky
Column:       In review (branch slice/iss-28, stacked)
Blocked by:   none
Finding:      `extract_resume.py` still prints the validated resume and every responsibility (24 to 132 lines per resume), so candidate PII goes to worker logs. Extraction also varies run to run: the same resume gave 75 skills and then 28.
Open part:    REQ-144 (variance across 3 real Groq runs per resume) not done; needs real Groq calls, which tests may not make. Run it by hand and record in takeover/test-health.md.
Acceptance criteria:
- REQ-143 No resume content is printed; details go to logging at DEBUG.
- REQ-144 Variance is measured across 3 runs per sample resume and recorded in takeover/test-health.md.

## FLOW-03 Score a candidate against a JD

### ISS-30 Characterise scoring with real pgvector in CI
Labels:       characterise, flow:FLOW-03, module:scoring
Column:       In review (branch platform/iss-02)
Blocked by:   ISS-02
Finding:      `test_scores_against_real_pgvector` exists but is skipped without `TEST_DATABASE_URL`.
Acceptance criteria:
- REQ-128 The test runs in CI against a pgvector container.

## FLOW-04 View shortlist and skill evidence

### ISS-40 Characterise shortlist screen
Labels:       characterise, flow:FLOW-04, module:streamlit
Column:       In review (branch characterise/iss-40, stacked)
Blocked by:   ISS-02
Finding:      The queries and badge thresholds (80/65) are inline in `streamlit_app.py`, with no tests.
Note:         Uses Streamlit AppTest + pgvector instead of Playwright; covers every case in REQ-129.
Acceptance criteria:
- REQ-129 Playwright and pg tests cover: no JDs, no candidates, badge tiers, coverage and evidence rows.

### ISS-42 Unescaped HTML from candidate names
Labels:       slice, flow:FLOW-04, module:streamlit, risky
Column:       In review (branch slice/iss-42, stacked)
Blocked by:   ISS-40
Finding:      Candidate names come from resume text and are interpolated into `st.markdown(..., unsafe_allow_html=True)`.
Acceptance criteria:
- REQ-131 A name containing `<script>` or other HTML renders as text (test).

### ISS-43 Results not shown after "Process Resumes in Background"
Labels:       slice, flow:FLOW-04, module:streamlit
Column:       In review (branch docs/iss-43, GitHub #16)
Blocked by:   ISS-40
Finding:      Owner report (2026-10-29): after clicking "🚀 Process Resumes in Background" (`streamlit_app.py:1051`) the resumes are parsed, but no results appear. The handler ends in `st.rerun()` (`streamlit_app.py:1111`), which also clears any `st.error`/`st.warning` shown during linking, so failures are invisible. The shortlist below (`streamlit_app.py:1119`) shows no JD keywords and no per-keyword matches.
Acceptance criteria:
- REQ-151 After processing, the results show `JD Keywords: <list> [<total> keywords]` for the selected requisition.
- REQ-152 One row per candidate: `<name> <email> | <pct>% or <matched>/<total> | <resume keyword> vs <JD keyword> (<similarity>%), ...`, e.g. `Bob Farrell bob@gmail.com | 30% or 3/10 | AWS vs Cloud Run (80%), Agile Lead vs Scrum Lead (95%), Healthcare vs HealthInsurance (40%)`.
- REQ-153 Errors and timeouts from a run stay visible after the page refreshes.

## FLOW-05 Cache maintenance

### ISS-50 Characterise cache maintenance controls
Labels:       characterise, flow:FLOW-05, module:streamlit
Column:       In review (branch characterise/iss-50, stacked)
Blocked by:   ISS-02
Finding:      No tests cover the sidebar maintenance controls.
Acceptance criteria:
- REQ-132 Tests cover the clear-cache button's success and error paths.

### ISS-51 "Clear Entire Redis Cache" runs FLUSHALL on the broker
Labels:       slice, flow:FLOW-05, module:cache, risky
Column:       In review (branch slice/iss-51, stacked)
Blocked by:   ISS-50
Finding:      `r.flushall()` also deletes the Celery queue and task results, so in-flight ingestion is lost.
Acceptance criteria:
- REQ-133 Clearing deletes only `resume_extract:*`, `jd_cache:*` and `emb:*` keys.
- REQ-134 The Celery queue and results survive a clear (test with fakeredis).

### ISS-52 "Force Re-parse" checkbox is not wired
Labels:       slice, flow:FLOW-05, module:streamlit
Column:       In review (branch slice/iss-52, stacked)
Blocked by:   ISS-50
Finding:      `force_refresh_toggle` is never used. Ingestion always passes `force_refresh=False`.
Acceptance criteria:
- REQ-135 With the box ticked, each resume's cache entry is cleared and re-extracted.

## FLOW-06 Poll task status

### ISS-60 Non-terminal and unknown task states misreported
Labels:       slice, flow:FLOW-06, module:api
Column:       In review (branch slice/iss-60, stacked)
Blocked by:   none
Finding:      `GET /task/{id}` reports STARTED and RETRY as "Failed". An unknown id stays "Processing..." forever (Celery reports PENDING). Characterised in `test_task_status_mapping`.
Acceptance criteria:
- REQ-136 STARTED and RETRY return "Processing...".
- REQ-137 Characterisation expectation change approved by owner (approved 2026-10-29).

### ISS-61 API has no authentication
Labels:       slice, flow:FLOW-06, module:api, risky
Column:       In review (branch slice/iss-61, stacked)
Blocked by:   none
Finding:      Both endpoints are open. Anyone who can reach :8000 can upload files and read results, which include candidate PII.
Acceptance criteria:
Decision:     Owner, 2026-10-29: API key.
- REQ-138 Both endpoints reject requests without a valid API key (401); Streamlit sends the key.

## Summary

| Area | Open issues |
| --- | --- |
| Cross-cutting | ISS-02 platform, ISS-05 platform, ISS-15 platform, ISS-62 platform (all In review) |
| FLOW-01 | – (none open) |
| FLOW-02 | ISS-20 characterise, ISS-22 slice, ISS-28 slice (all In review; ISS-28 REQ-144 open) |
| FLOW-03 | ISS-30 characterise (In review) |
| FLOW-04 | ISS-40 characterise, ISS-42 slice (In review); ISS-43 slice (In review) |
| FLOW-05 | ISS-50 characterise, ISS-51 slice, ISS-52 slice (In review) |
| FLOW-06 | ISS-60 slice, ISS-61 slice (In review) |

Merge order (each branch is one commit on the previous): platform/iss-02 → slice/iss-22 → slice/iss-28 → slice/iss-60 → slice/iss-61 → characterise/iss-40 → slice/iss-42 → characterise/iss-50 → slice/iss-51 → slice/iss-52 → platform/iss-05 → platform/iss-15 → docs/tracker-2026-10-29.

Done: ISS-01, ISS-03, ISS-04, ISS-41, ISS-10, ISS-11, ISS-12, ISS-13, ISS-14, ISS-21, ISS-23, ISS-24, ISS-25, ISS-26, ISS-27 (see `takeover/issues-done.md`).
