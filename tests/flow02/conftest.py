"""Reuse the shared offline fakes."""
import pytest
from tests.characterisation.conftest import _isolate_cwd, fake_redis, fake_vectors, upload  # noqa: F401
from tests.characterisation.test_ingest_resumes_pg import pg_session, wired  # noqa: F401


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    """ISS-61: the API needs a key; tests send "test-key"."""
    monkeypatch.setenv("MANALOT_API_KEY", "test-key")
