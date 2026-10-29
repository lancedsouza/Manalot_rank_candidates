"""ISS-52: with "Force Re-parse" ticked, each resume's cache entry is cleared before queueing."""
import ast
from pathlib import Path

import fakeredis

from app.utils import resume_cache as rc

ROOT = Path(__file__).resolve().parents[2]


def test_forget_deletes_only_those_resumes(monkeypatch, tmp_path):
    r = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(rc, "redis_client", r)
    a, b, other = b"%PDF a", b"%PDF b", b"%PDF other"
    for data in (a, b, other):
        r.set(rc.cache_key_for_bytes(data), "{}")
    r.set("jd_cache:x", "v")

    rc.forget_cached_resumes([a, b])

    assert sorted(r.keys("*")) == sorted([rc.cache_key_for_bytes(other), "jd_cache:x"])


def test_key_matches_the_workers_path_based_key(tmp_path):
    pdf = tmp_path / "cv.pdf"
    pdf.write_bytes(b"%PDF same bytes")
    assert rc.generate_cache_key(pdf) == rc.cache_key_for_bytes(b"%PDF same bytes")


def test_no_redis_is_a_no_op(monkeypatch):
    monkeypatch.setattr(rc, "redis_client", None)
    rc.forget_cached_resumes([b"x"])  # does not raise


def test_streamlit_clears_before_queueing_only_when_ticked():
    tree = ast.parse((ROOT / "streamlit_app.py").read_text())
    ifs = [n for n in ast.walk(tree) if isinstance(n, ast.If)
           and isinstance(n.test, ast.Name) and n.test.id == "force_refresh_toggle"]
    assert len(ifs) == 1
    call = ifs[0].body[0].value
    assert call.func.id == "forget_cached_resumes"
    src = (ROOT / "streamlit_app.py").read_text()
    assert src.index("forget_cached_resumes([") < src.index('requests.post(f"{API_BASE_URL}/extract-resume/async"')
