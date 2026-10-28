# Test health (safety sweep)

- Suite: `tests/characterisation/` — 38 offline tests + 1 `pg` test (skipped without TEST_DATABASE_URL).
- Three full runs: 38/38 passed each time; no flaky tests.
- Pre-existing tests: none (files named `test_*.py` under `app/` are manual scripts against live services).
- Coverage / mutation score: not yet measured — add `pytest-cov` and `mutmut` in the Platform CI issue.
- Gaps: FLOW-04 and FLOW-05 live inline in `streamlit_app.py`; characterise with Playwright + pg in a `characterise` issue.
