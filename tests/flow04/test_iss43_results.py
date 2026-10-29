"""ISS-43: after processing, the shortlist shows JD keywords and per-candidate keyword matches."""
import os
from collections import namedtuple

import pytest

from app.utils.results_format import format_keywords_header, format_result_row
from tests.characterisation import test_view_shortlist as _sv
from tests.characterisation.test_view_shortlist import ROOT, _candidate, _jd, _sql

app, pg_session = _sv.app, _sv.pg_session  # shared fixtures: AppTest runner on throwaway pgvector

Match = namedtuple("Match", "jd_skill candidate_skill similarity")


def test_keywords_header_lists_keywords_and_total():
    assert format_keywords_header(["SQL", "Tableau"]) == "JD Keywords: SQL, Tableau [2 keywords]"


def test_result_row_matches_owner_format():
    matches = [
        Match("Cloud Run", "AWS", 0.80),
        Match("Scrum Lead", "Agile Lead", 0.95),
        Match("HealthInsurance", "Healthcare", 0.40),
    ]
    assert format_result_row("Bob Farrell", "bob@gmail.com", matches, 10) == (
        "Bob Farrell bob@gmail.com | 30% or 3/10 | "
        "AWS vs Cloud Run (80%), Agile Lead vs Scrum Lead (95%), Healthcare vs HealthInsurance (40%)"
    )


def test_result_row_without_email_or_matches():
    assert format_result_row("Ann", None, [], 4) == "Ann | 0% or 0/4 | no keyword matches"


def test_result_row_with_no_jd_keywords():
    assert format_result_row(None, None, [], 0) == "Unknown candidate | 0% or 0/0 | no keyword matches"


@pytest.mark.pg
@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL (pgvector)")
class TestResultsView:
    def test_results_show_keywords_and_best_match_per_keyword(self, app, pg_session):
        jd = _jd(pg_session, skills=("SQL", "Tableau"))
        cid = _candidate(pg_session, jd, "Bob Farrell", 0.9, skills=("SQL", "Excel"))
        _sql(pg_session, "UPDATE candidates SET email = 'bob@gmail.com' WHERE id = :c", c=cid)
        at = app()
        assert not at.exception
        texts = [t.value for t in at.text]
        assert texts[0] == "JD Keywords: SQL, Tableau [2 keywords]"
        assert texts[1] == "Bob Farrell bob@gmail.com | 50% or 1/2 | SQL vs SQL (100%)"

    def test_last_run_errors_survive_rerun(self, app, pg_session):
        from streamlit.testing.v1 import AppTest
        _jd(pg_session)
        at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
        at.session_state["last_run"] = {"linked": 1, "total": 2, "errors": ["Failed on b.pdf: boom"]}
        at.run()
        assert not at.exception
        assert "**Last run:** 1/2 resumes linked." in [m.value for m in at.markdown]
        assert "Failed on b.pdf: boom" in [e.value for e in at.error]
