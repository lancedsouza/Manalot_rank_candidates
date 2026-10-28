"""FLOW-03 Score a candidate against a JD — calculate_candidate_scores_for_jd."""
import os
from types import SimpleNamespace

import pytest

from app.services import resume_processor as rp


class FakeSession:
    def __init__(self, parent, total, matched, avg_depth, avg_matched):
        self._parent = parent
        self._row = SimpleNamespace(total_jd_skills=total, matched=matched,
                                    avg_depth=avg_depth, avg_matched_depth=avg_matched)
        self.params = []

    def execute(self, sql, params):
        self.params.append(params)
        row = self._row
        return SimpleNamespace(scalar=lambda: self._parent, first=lambda: row)


def test_constants():
    assert (rp.W_PARENT, rp.W_COVERAGE, rp.W_DEPTH) == (0.20, 0.55, 0.25)
    assert rp.COVERAGE_THRESHOLD == 0.75
    assert rp.EMBED_DIM == 384


def test_hybrid_formula():
    s = FakeSession(parent=0.8, total=4, matched=3, avg_depth=0.7, avg_matched=0.9)
    out = rp.calculate_candidate_scores_for_jd(s, jd_id=1, cand_id=2)

    assert out["coverage"] == pytest.approx(0.75)
    assert out["skill"] == pytest.approx(0.5 * 0.75 + 0.5 * 0.9)
    assert out["hybrid"] == pytest.approx(0.20 * 0.8 + 0.55 * 0.75 + 0.25 * 0.9)
    assert out["parent"] == 0.8
    assert (out["matched_skills"], out["total_jd_skills"]) == (3, 4)
    assert s.params[1]["threshold"] == 0.75


def test_no_jd_skills_and_missing_parent_score_zero():
    s = FakeSession(parent=None, total=0, matched=0, avg_depth=None, avg_matched=None)
    out = rp.calculate_candidate_scores_for_jd(s, 1, 2)
    assert out == {"hybrid": 0.0, "parent": 0.0, "skill": 0.0, "coverage": 0.0,
                   "matched_skills": 0, "total_jd_skills": 0}


@pytest.mark.pg
@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL (pgvector)")
def test_scores_against_real_pgvector():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    eng = create_engine(os.environ["TEST_DATABASE_URL"])
    with Session(eng) as s:
        s.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        s.execute(text("CREATE TEMP TABLE candidates (id int, embedding vector(3))"))
        s.execute(text("CREATE TEMP TABLE jds (id int, embedding vector(3))"))
        s.execute(text("CREATE TEMP TABLE jd_skill (id int, jd_id int, skill_embedding vector(3))"))
        s.execute(text("CREATE TEMP TABLE cand_skill (cand_id int, skill_embedding vector(3))"))
        s.execute(text("INSERT INTO candidates VALUES (1, '[1,0,0]')"))
        s.execute(text("INSERT INTO jds VALUES (1, '[1,0,0]')"))
        s.execute(text("INSERT INTO jd_skill VALUES (1,1,'[1,0,0]'), (2,1,'[0,1,0]')"))
        s.execute(text("INSERT INTO cand_skill VALUES (1,'[1,0,0]')"))
        out = rp.calculate_candidate_scores_for_jd(s, 1, 1)
        s.rollback()

    assert out["parent"] == pytest.approx(1.0)
    assert (out["matched_skills"], out["total_jd_skills"]) == (1, 2)
    assert out["hybrid"] == pytest.approx(0.20 + 0.55 * 0.5 + 0.25 * 1.0)
