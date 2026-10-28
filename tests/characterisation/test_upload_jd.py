"""FLOW-01 Upload and embed a job description — jd_processor + extract_jd."""
import hashlib

import pytest

from app.pydantic_models.jd_pydantic_models import JDRequirements
from app.services import jd_processor as jp
from app.utils import extract_jd


class AddSession:
    def __init__(self):
        self.added, self.committed, self.rolled_back = [], False, False

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.added[0].id = 11

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _wire(monkeypatch, fake_vectors, jd):
    monkeypatch.setattr(jp, "extract_text", lambda p: "JD body")
    monkeypatch.setattr(jp, "extract_structured_jd", lambda t: jd)
    monkeypatch.setattr(jp, "create_embeddings", fake_vectors)


def test_persists_jd_and_one_row_per_required_skill(monkeypatch, fake_vectors, upload):
    _wire(monkeypatch, fake_vectors, JDRequirements(title="Sr Manager FP&A", required_skills=["Excel", "SAP"]))
    s = AddSession()

    assert jp.process_pdf_jd(s, upload("jd.pdf")) == (11, "Sr Manager FP&A")

    jd, *skills = s.added
    assert jd.embedding == [1.0] * 384
    assert jd.responsibilities_embedding == jd.embedding
    assert jd.education_embedding == [0.0] * 384  # placeholder vectors today
    assert jd.responsibilities == ["General responsibilities per job description"]
    assert [(k.skill, k.skill_embedding[0]) for k in skills] == [("Excel", 2.0), ("SAP", 3.0)]
    assert s.committed


def test_title_falls_back_to_filename_and_skills_to_title(monkeypatch, fake_vectors, upload):
    _wire(monkeypatch, fake_vectors, JDRequirements(title="  "))
    s = AddSession()
    _, title = jp.process_pdf_jd(s, upload("sr_finance_lead.pdf"))
    assert title == "Sr Finance Lead"
    assert s.added[0].required_skills == ["Sr Finance Lead"]


def test_empty_text_raises_and_rolls_back(monkeypatch, upload, tmp_path):
    monkeypatch.setattr(jp, "extract_text", lambda p: "")
    s = AddSession()
    with pytest.raises(ValueError, match="Could not extract text from the JD PDF."):
        jp.process_pdf_jd(s, upload("jd.pdf"))
    assert s.rolled_back
    assert not (tmp_path / "temp_uploads" / "jd.pdf").exists()


def test_extract_jd_cache_key():
    assert extract_jd.get_cache_key("abc") == "jd_cache:" + hashlib.sha256(b"abc").hexdigest()


def test_extract_jd_miss_calls_llm_then_hit_uses_cache(monkeypatch, fake_redis):
    monkeypatch.setattr(extract_jd, "redis_client", fake_redis)
    calls = []

    class Resp:
        parsed = JDRequirements(title="T", required_skills=["A"])

    monkeypatch.setattr(extract_jd, "generate_structured_response",
                        lambda prompt, schema: calls.append(prompt) or Resp)

    first = extract_jd.extract_structured_jd("jd text")
    second = extract_jd.extract_structured_jd("jd text")

    assert first == second and len(calls) == 1
    assert "jd text" in calls[0]
    assert 0 < fake_redis.ttl(extract_jd.get_cache_key("jd text")) <= 60 * 60 * 24 * 7
