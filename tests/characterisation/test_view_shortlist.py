"""FLOW-04 View shortlist and skill evidence — streamlit_app.py dashboard (ISS-40).

Runs the real script with Streamlit's AppTest against a throwaway pgvector
schema (TEST_DATABASE_URL). The app's engine and SessionLocal are swapped for
ones bound to that schema; no upload, Redis or LLM path is exercised.
"""
import os
from pathlib import Path

import pytest

from tests.characterisation import test_ingest_resumes_pg as _pg

_vec = _pg._vec
pg_session = _pg.pg_session  # shared fixture: throwaway pgvector schema

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL (pgvector)"),
]


@pytest.fixture
def app(pg_session, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    from streamlit.testing.v1 import AppTest

    import app.database.db as db

    eng = pg_session.get_bind()
    monkeypatch.setattr(db, "engine", eng)
    monkeypatch.setattr(db, "SessionLocal", sessionmaker(bind=eng))

    def run():
        at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
        return at.run()
    return run


def _sql(session, q, **p):
    from sqlalchemy import text
    r = session.execute(text(q), p)
    session.commit()
    return r


def _jd(session, title="FP&A Lead", skills=("SQL", "Tableau")):
    jd_id = _sql(session, "INSERT INTO jds (title, description, required_skills, responsibilities, embedding, "
                          "responsibilities_embedding, education_embedding) "
                          "VALUES (:t, 'jd', :s, ARRAY['x'], CAST(:e AS vector), CAST(:e AS vector), CAST(:e AS vector)) "
                          "RETURNING id",
                 t=title, s=list(skills), e=str(_vec("jd"))).scalar()
    session.commit()
    for s in skills:
        _sql(session, "INSERT INTO jd_skill (jd_id, skill, skill_embedding) VALUES (:j, :s, CAST(:e AS vector))",
             j=jd_id, s=s, e=str(_vec(s)))
    return jd_id


def _candidate(session, jd_id, name, hybrid, skills=()):
    cid = _sql(session, "INSERT INTO candidates (name, resume_text, embedding, skills, education, experience, projects) "
                        "VALUES (:n, 'cv', CAST(:e AS vector), :s, '[]', '[]', ARRAY[]::text[]) RETURNING id",
               n=name, e=str(_vec(name)), s=list(skills)).scalar()
    session.commit()
    for s in skills:
        _sql(session, "INSERT INTO cand_skill (cand_id, skill, skill_embedding) VALUES (:c, :s, CAST(:e AS vector))",
             c=cid, s=s, e=str(_vec(s)))
    _sql(session, "INSERT INTO applications (jd_id, candidate_id, hybrid_score, parent_score, skill_score) "
                  "VALUES (:j, :c, :h, 0.5, 0.25)", j=jd_id, c=cid, h=hybrid)
    return cid


def _cards(at):
    return [m.value for m in at.markdown if 'class="card"' in m.value]


def test_no_jds_shows_upload_prompt(app):
    at = app()
    assert not at.exception
    assert [i.value for i in at.info] == [
        "No Job Descriptions found in the database. Please upload a JD PDF via the sidebar."]


def test_jd_without_candidates_warns(app, pg_session):
    _jd(pg_session)
    at = app()
    assert not at.exception
    assert at.selectbox[0].options == ["FP&A Lead"]
    assert [w.value for w in at.warning] == [
        "No candidates have applied to this requisition yet. Upload resumes above to begin."]


def test_ranked_by_hybrid_with_badge_tiers_and_top_n_default_5(app, pg_session):
    jd = _jd(pg_session)
    for i, h in enumerate([0.50, 0.85, 0.80, 0.65, 0.6499, 0.70]):
        _candidate(pg_session, jd, f"Cand {i}", h)
    at = app()
    cards = _cards(at)
    assert at.slider[0].value == 5 and len(cards) == 5
    ranks = [(c.split("</h3>")[0].split(": ")[1], c) for c in cards]
    assert [n for n, _ in ranks] == ["Cand 1", "Cand 2", "Cand 5", "Cand 3", "Cand 4"]
    tiers = ["Top Tier" if "badge-top" in c else "Strong" if "badge-strong" in c else "Moderate" for _, c in ranks]
    # boundaries: >= 80 Top, >= 65 Strong, else Moderate
    assert tiers == ["Top Tier", "Top Tier", "Strong", "Strong", "Moderate"]
    assert "<b>Hybrid Match Score:</b> 85.0%" in cards[0]


def test_coverage_metric_and_evidence_rows(app, pg_session):
    jd = _jd(pg_session, skills=("SQL", "Tableau"))
    _candidate(pg_session, jd, "Ada", 0.9, skills=("SQL", "Python"))
    at = app()
    metrics = {m.label: (m.value, m.delta) for m in at.metric}
    assert metrics["Overall Profile Fit"][0] == "50.0%"
    assert metrics["Skill Score"][0] == "25.0%"
    assert metrics["JD Skill Coverage"] == ("1/2", "50%")
    evidence = [m.value for m in at.markdown if m.value.startswith("- **JD Requirement:**")]
    assert evidence == ['- **JD Requirement:** *"SQL"*  \n  ↳ **Candidate Match:** *"SQL"* (`100%` match)']


def test_no_evidence_above_threshold(app, pg_session):
    jd = _jd(pg_session, skills=("SQL",))
    _candidate(pg_session, jd, "Bo", 0.3, skills=("Cooking",))
    at = app()
    assert "No primary skill evidence matches above threshold." in [i.value for i in at.info]
    assert {m.label: m.value for m in at.metric}["JD Skill Coverage"] == "0/1"


def test_candidate_name_html_is_escaped(app, pg_session):
    # ISS-42 fixed: names come from resume text, so markup renders as text
    jd = _jd(pg_session)
    _candidate(pg_session, jd, '<script>alert("x")</script>', 0.9)
    at = app()
    card = _cards(at)[0]
    assert "<script>" not in card
    assert "Rank #1: &lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;</h3>" in card
