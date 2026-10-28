"""Shared fakes for characterisation tests.

All tests run offline: no Redis, Postgres, LLM or embedding model is contacted.
Env vars are set before any app module is imported, because several modules
connect or validate config at import time.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Unreachable Redis: module-level ping() fails fast, so redis_client is None.
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
# db.py raises at import without this; create_engine() never connects.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://u:p@127.0.0.1:1/none")
os.environ.setdefault("GROQ_API_KEY", "fake-key-for-tests")

import fakeredis  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


class FakeUpload:
    """Mimics streamlit's UploadedFile: .name and .getbuffer()."""

    def __init__(self, name: str, data: bytes = b"%PDF-1.4 fake"):
        self.name = name
        self._data = data

    def getbuffer(self):
        return memoryview(self._data)

    def getvalue(self):
        return self._data


@pytest.fixture
def upload():
    return FakeUpload


@pytest.fixture
def fake_vectors():
    """Deterministic fake embedder: vector i is [i+1]*384."""

    def _embed(texts):
        return [[float(i + 1)] * 384 for i in range(len(texts))]

    return _embed


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    # Processors write to ./temp_uploads; keep that out of the repo.
    monkeypatch.chdir(tmp_path)
