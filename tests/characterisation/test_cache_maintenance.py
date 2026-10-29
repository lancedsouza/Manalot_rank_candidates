"""FLOW-05 Cache maintenance — sidebar "Maintenance Controls" in streamlit_app.py (ISS-50).

Runs the real script with Streamlit AppTest. Redis is fakeredis; the dashboard
below the sidebar reads a throwaway pgvector schema (TEST_DATABASE_URL).
"""
import os
from pathlib import Path

import fakeredis
import pytest
import redis

from tests.characterisation import test_ingest_resumes_pg as _pg

pg_session = _pg.pg_session  # shared fixture: throwaway pgvector schema
ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="needs TEST_DATABASE_URL (pgvector)"),
]

CLEAR = "🧹 Clear Entire Redis Cache"


@pytest.fixture
def app(pg_session, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    from streamlit.testing.v1 import AppTest

    import app.database.db as db

    eng = pg_session.get_bind()
    monkeypatch.setattr(db, "engine", eng)
    monkeypatch.setattr(db, "SessionLocal", sessionmaker(bind=eng))
    return lambda: AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()


@pytest.fixture
def fake(monkeypatch):
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis.Redis, "from_url", classmethod(lambda cls, url, **kw: r))
    return r


def _button(at, label):
    return next(b for b in at.sidebar.button if b.label == label)


def test_controls_render_with_force_reparse_off(app, fake):
    at = app()
    assert not at.exception
    box = next(c for c in at.sidebar.checkbox if c.label == "Force Re-parse (Bypass Cache)")
    assert box.value is False
    assert _button(at, CLEAR).proto.type == "secondary"


def test_clear_cache_success_keeps_celery_keys(app, fake):
    for k in ("resume_extract:a", "jd_cache:b", "emb:c", "celery-task-meta-1", "_kombu.binding.celery"):
        fake.set(k, "x")
    fake.rpush("celery", "queued-task")
    at = app()
    at = _button(at, CLEAR).click().run()
    assert [s.value for s in at.sidebar.success] == ["Redis cache flushed!"]
    # ISS-51 fixed: only cache keys go; the Celery queue and results survive
    assert sorted(fake.keys("*")) == ["_kombu.binding.celery", "celery", "celery-task-meta-1"]
    assert fake.lrange("celery", 0, -1) == ["queued-task"]


def test_clear_cache_error_shows_message(app, monkeypatch):
    def boom(cls, url, **kw):
        raise redis.ConnectionError("redis down")
    monkeypatch.setattr(redis.Redis, "from_url", classmethod(boom))
    at = app()
    at = _button(at, CLEAR).click().run()
    assert [e.value for e in at.sidebar.error] == ["Error: redis down"]
    assert not at.sidebar.success
