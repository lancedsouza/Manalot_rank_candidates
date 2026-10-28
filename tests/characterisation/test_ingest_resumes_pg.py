"""FLOW-02 Ingest resumes — process_and_link_resume against real Postgres + pgvector (ISS-20).

Runs only with TEST_DATABASE_URL. Each test gets its own schema, built from the
SQLAlchemy models the same way streamlit_app.py does (Base.metadata.create_all),
and dropped afterwards. Embeddings are fake but deterministic.
"""
import hashlib
import os
import uuid

import pytest

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL (pgvector)"),
]


def _vec(text):
    """Deterministic unit-ish 384-d vector per text; identical text -> identical vector."""
    h = hashlib.sha256(text.encode()).digest()
    v = [0.0] * 384
    for i in range(8):
        v[h[i] % 384] += 1.0
    return v


@pytest.fixture
def pg_session():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from app.database.db import Base
    from app.database import (application_models, candidate_skill_table,  # noqa: F401
                              jd_models, jd_skill_table, resume_models)

    schema = f"t_{uuid.uuid4().hex[:10]}"
    admin = create_engine(os.environ["TEST_DATABASE_URL"])
    with admin.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        c.execute(text(f"CREATE SCHEMA {schema}"))
    eng = create_engine(os.environ["TEST_DATABASE_URL"],
                        connect_args={"options": f"-csearch_path={schema},public"})
    Base.metadata.create_all(bind=eng)
    with Session(eng) as s:
        yield s
    eng.dispose()
    with admin.begin() as c:
        c.execute(text(f"DROP SCHEMA {schema} CASCADE"))
    admin.dispose()


@pytest.fixture
def wired(monkeypatch):
    from app.models.resume import Education, Experience, Resume
    from app.services import resume_processor as rp

    monkeypatch.setattr(rp, "extract_text", lambda p: "Ada Lovelace resume text")
    monkeypatch.setattr(rp, "create_embeddings", lambda texts: [_vec(t) for t in texts])
    resume = Resume(name="Ada Lovelace", skills=["SQL", "Python"], experience_years=7.5,
                    education=[Education(degree="MBA", institution="IIM")],
                    experience=[Experience(title="FP&A Lead", company="Acme", responsibilities=["Budget"])],
                    projects=["Forecast model"])
    return rp, resume


def _jd(session):
    from app.database.jd_models import JD
    from app.database.jd_skill_table import Jd_Skill

    jd = JD(title="FP&A", description="JD text", required_skills=["SQL", "Tableau"], responsibilities=["x"],
            embedding=_vec("Ada Lovelace resume text"), responsibilities_embedding=_vec("r"),
            education_embedding=_vec("e"))
    session.add(jd)
    session.flush()
    session.add_all([Jd_Skill(jd_id=jd.id, skill=s, skill_embedding=_vec(s)) for s in ("SQL", "Tableau")])
    session.commit()
    return jd.id


def test_new_candidate_row_skills_and_application(pg_session, wired, upload):
    from sqlalchemy import text

    rp, resume = wired
    jd_id = _jd(pg_session)
    cand_id, name = rp.process_and_link_resume(pg_session, upload("ada.pdf"), jd_id, structured_resume=resume)

    assert name == "Ada Lovelace"
    row = pg_session.execute(text("SELECT name, experience_years, skills, projects, education, experience "
                                  "FROM candidates WHERE id = :i"), {"i": cand_id}).mappings().one()
    assert row["experience_years"] == 7.5
    assert row["skills"] == ["SQL", "Python"] and row["projects"] == ["Forecast model"]
    assert row["education"][0]["degree"] == "MBA"
    assert row["experience"][0]["responsibilities"] == ["Budget"]
    skills = pg_session.execute(text("SELECT skill FROM cand_skill WHERE cand_id = :i ORDER BY skill"),
                                {"i": cand_id}).scalars().all()
    assert skills == ["Python", "SQL"]
    app = pg_session.execute(text("SELECT hybrid_score, parent_score, skill_score FROM applications "
                                  "WHERE jd_id = :j AND candidate_id = :c"), {"j": jd_id, "c": cand_id}).one()
    # parent cosine = 1 (same text); SQL matches exactly (1.0), Tableau does not -> coverage 0.5, depth 1.0
    assert app.parent_score == pytest.approx(1.0)
    assert app.hybrid_score == pytest.approx(0.20 * 1.0 + 0.55 * 0.5 + 0.25 * 1.0)
    assert app.skill_score == pytest.approx(0.5 * 0.5 + 0.5 * 1.0)


def test_same_name_updates_row_replaces_skills_and_upserts_application(pg_session, wired, upload):
    from sqlalchemy import text

    rp, resume = wired
    jd_id = _jd(pg_session)
    first, _ = rp.process_and_link_resume(pg_session, upload("ada.pdf"), jd_id, structured_resume=resume)
    second, _ = rp.process_and_link_resume(pg_session, upload("ada2.pdf"), jd_id,
                                           structured_resume=resume.model_copy(update={"skills": ["Tableau"]}))

    assert first == second  # ISS-22: same name -> same row
    assert pg_session.execute(text("SELECT count(*) FROM candidates")).scalar() == 1
    assert pg_session.execute(text("SELECT skill FROM cand_skill")).scalars().all() == ["Tableau"]
    assert pg_session.execute(text("SELECT count(*) FROM applications")).scalar() == 1
