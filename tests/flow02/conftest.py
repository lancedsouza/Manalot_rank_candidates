"""Reuse the shared offline fakes."""
from tests.characterisation.conftest import _isolate_cwd, fake_redis, fake_vectors, upload  # noqa: F401
from tests.characterisation.test_ingest_resumes_pg import pg_session, wired  # noqa: F401
