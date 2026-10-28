"""FLOW-02 Ingest resumes / FLOW-06 Poll task status — FastAPI (backend.py) and Celery task (worker.py)."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import backend
import worker
from app.models.resume import Resume


@pytest.fixture
def client():
    return TestClient(backend.app)


def test_rejects_non_pdf_with_400(client):
    r = client.post("/api/v1/extract-resume/async", files={"file": ("cv.docx", b"x")})
    assert r.status_code == 400
    assert r.json() == {"detail": "Only PDF files are supported."}


def test_queues_pdf_and_returns_task_id(client, monkeypatch, tmp_path):
    sent = []
    monkeypatch.setattr(backend.process_resume_task, "delay",
                        lambda path: sent.append(path) or SimpleNamespace(id="task-123"))
    r = client.post("/api/v1/extract-resume/async", files={"file": ("CV.PDF", b"%PDF")})

    assert r.status_code == 200
    assert r.json() == {"message": "Resume queued for processing.", "task_id": "task-123"}
    # ISS-21 (owner-approved expectation change): unique, sanitised name inside temp_uploads/
    (path,) = sent
    assert path.startswith("temp_uploads/") and path.endswith("_CV.PDF")
    assert (tmp_path / path).read_bytes() == b"%PDF"


@pytest.mark.parametrize("state,info,result,expected", [
    ("PENDING", None, None, {"status": "Processing..."}),
    ("SUCCESS", None, {"status": "success"}, {"status": "Completed", "result": {"status": "success"}}),
    ("FAILURE", ValueError("boom"), None, {"status": "Failed", "error": "boom"}),
    ("STARTED", None, None, {"status": "Failed", "error": "None"}),  # KNOWN-ISSUE: non-terminal states reported as Failed
])
def test_task_status_mapping(client, monkeypatch, state, info, result, expected):
    monkeypatch.setattr(backend, "AsyncResult",
                        lambda tid: SimpleNamespace(state=state, info=info, result=result))
    assert client.get("/api/v1/task/abc").json() == expected


def test_worker_success_returns_candidate_and_deletes_file(monkeypatch, tmp_path):
    f = tmp_path / "cv.pdf"
    f.write_bytes(b"%PDF")
    monkeypatch.setattr(worker, "process_resume", lambda p: Resume(name="Ada"))

    out = worker.process_resume_task.apply(args=[str(f)]).get()

    assert out["status"] == "success" and out["candidate"]["name"] == "Ada"
    assert not f.exists()


def test_worker_failure_marks_task_failed(monkeypatch, tmp_path):
    # ISS-23 (owner-approved expectation change): errors propagate -> Celery FAILURE
    f = tmp_path / "cv.pdf"
    f.write_bytes(b"%PDF")

    def boom(p):
        raise RuntimeError("llm down")

    monkeypatch.setattr(worker, "process_resume", boom)
    res = worker.process_resume_task.apply(args=[str(f)])

    assert res.state == "FAILURE" and str(res.result) == "llm down"
    assert not f.exists()
