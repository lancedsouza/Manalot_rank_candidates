"""ISS-61: both API endpoints need X-API-Key; the check fails closed."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import backend

ENDPOINTS = [
    ("post", "/api/v1/extract-resume/async", {"files": {"file": ("cv.pdf", b"%PDF")}}),
    ("get", "/api/v1/task/abc", {}),
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("MANALOT_API_KEY", "right-key")
    return TestClient(backend.app)


@pytest.mark.parametrize("method, path, kw", ENDPOINTS)
@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong-key"}, {"X-API-Key": ""}])
def test_missing_or_wrong_key_is_401(client, method, path, kw, headers):
    r = getattr(client, method)(path, headers=headers, **kw)
    assert r.status_code == 401


@pytest.mark.parametrize("method, path, kw", ENDPOINTS)
def test_unconfigured_key_fails_closed_503(monkeypatch, method, path, kw):
    monkeypatch.delenv("MANALOT_API_KEY", raising=False)
    r = getattr(TestClient(backend.app), method)(path, headers={"X-API-Key": "anything"}, **kw)
    assert r.status_code == 503


def test_right_key_reaches_endpoint(client, monkeypatch):
    monkeypatch.setattr(backend, "AsyncResult", lambda tid: SimpleNamespace(state="PENDING", info=None, result=None))
    r = client.get("/api/v1/task/abc", headers={"X-API-Key": "right-key"})
    assert r.status_code == 200 and r.json() == {"status": "Processing..."}


def test_streamlit_sends_the_key():
    src = open("streamlit_app.py").read()
    assert 'API_HEADERS = {"X-API-Key": os.getenv("MANALOT_API_KEY", "")}' in src
    assert src.count("headers=API_HEADERS") == 2
