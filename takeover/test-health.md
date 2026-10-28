# Test health

Updated 2026-10-29 (ISS-02).

- Suite: 60 tests. 57 offline; 3 `pg` tests (FLOW-02 linking x2, FLOW-03 scoring) run when TEST_DATABASE_URL is set, and always in CI.
- Flakiness: offline suite green on 3 consecutive runs after each change; no flaky tests seen.
- Coverage (offline, app + backend + worker): 47.53%. Baseline 47.5% in `ci/baselines/coverage.json`; CI fails if it drops.
- Lint: 60 legacy ruff findings across the untouched files, baselined per file in `ci/baselines/ruff.json`. New files must have 0.
- Mutation score: not yet measured (ISS-15).
- Gaps: FLOW-04 and FLOW-05 (ISS-40, ISS-50). The streamlit polling timeout (ISS-25) has no automated test.
