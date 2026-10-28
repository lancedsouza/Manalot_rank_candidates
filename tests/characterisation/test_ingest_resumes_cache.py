"""FLOW-02 Ingest resumes — Redis-cached resume extraction (app/utils/resume_cache.py)."""
import hashlib

from app.models.resume import Resume
from app.utils import resume_cache


def _pdf(tmp_path, data=b"%PDF-1.4 resume"):
    p = tmp_path / "cv.pdf"
    p.write_bytes(data)
    return p


def test_cache_key_is_sha256_model_and_prompt_version(tmp_path):
    p = _pdf(tmp_path)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert resume_cache.generate_cache_key(p) == (
        f"resume_extract:{digest}:gemini-3.6-flash:resume_extract_v2"
    )


def test_cache_key_changes_with_file_bytes(tmp_path):
    a = resume_cache.generate_cache_key(_pdf(tmp_path, b"one"))
    b = resume_cache.generate_cache_key(_pdf(tmp_path, b"two"))
    assert a != b


def test_miss_extracts_then_stores_with_60_day_ttl(tmp_path, monkeypatch, fake_redis):
    monkeypatch.setattr(resume_cache, "redis_client", fake_redis)
    calls = []
    monkeypatch.setattr(
        resume_cache, "extract_resume_data",
        lambda p: calls.append(p) or Resume(name="Ada", skills=["FP&A"]),
    )
    p = _pdf(tmp_path)

    out = resume_cache.process_resume(p)

    assert out.name == "Ada" and len(calls) == 1
    key = resume_cache.generate_cache_key(p)
    assert Resume.model_validate_json(fake_redis.get(key)) == out
    assert 0 < fake_redis.ttl(key) <= 60 * 60 * 24 * 60


def test_hit_returns_cached_without_extracting(tmp_path, monkeypatch, fake_redis):
    monkeypatch.setattr(resume_cache, "redis_client", fake_redis)
    p = _pdf(tmp_path)
    fake_redis.set(resume_cache.generate_cache_key(p), Resume(name="Cached").model_dump_json())
    monkeypatch.setattr(resume_cache, "extract_resume_data", lambda p: (_ for _ in ()).throw(AssertionError))

    assert resume_cache.process_resume(p).name == "Cached"


def test_corrupt_cache_entry_falls_back_to_extraction(tmp_path, monkeypatch, fake_redis):
    monkeypatch.setattr(resume_cache, "redis_client", fake_redis)
    p = _pdf(tmp_path)
    fake_redis.set(resume_cache.generate_cache_key(p), "not json")
    monkeypatch.setattr(resume_cache, "extract_resume_data", lambda p: Resume(name="Fresh"))

    assert resume_cache.process_resume(p).name == "Fresh"


def test_redis_offline_extracts_every_time(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_cache, "redis_client", None)
    calls = []
    monkeypatch.setattr(resume_cache, "extract_resume_data", lambda p: calls.append(1) or Resume())
    p = _pdf(tmp_path)
    resume_cache.process_resume(p)
    resume_cache.process_resume(p)
    assert len(calls) == 2


def test_dict_result_is_validated_into_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_cache, "redis_client", None)
    monkeypatch.setattr(resume_cache, "extract_resume_data", lambda p: {"name": "Dict", "experience_years": 3})
    out = resume_cache.process_resume(_pdf(tmp_path))
    assert isinstance(out, Resume) and out.experience_years == 3.0
