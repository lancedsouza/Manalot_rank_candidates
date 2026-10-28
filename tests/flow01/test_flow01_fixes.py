"""FLOW-01 fixes: ISS-10 duplicate JD, ISS-11 field embeddings, ISS-12 no prints, ISS-13 shared Redis URL."""
import importlib
from types import SimpleNamespace

from app.pydantic_models.jd_pydantic_models import JDRequirements
from app.services import jd_processor as jp
from tests.characterisation.test_upload_jd import AddSession


def _wire(monkeypatch, jd, calls=None):
    monkeypatch.setattr(jp, "extract_text", lambda p: "JD body")
    monkeypatch.setattr(jp, "extract_structured_jd", lambda t: jd)

    def embed(texts):
        if calls is not None:
            calls.append(list(texts))
        return [[float(i + 1)] * 384 for i in range(len(texts))]

    monkeypatch.setattr(jp, "create_embeddings", embed)


def test_iss10_same_jd_text_returns_existing_row_without_reembedding(monkeypatch, upload):
    calls = []
    _wire(monkeypatch, JDRequirements(title="New"), calls)
    s = AddSession(existing=SimpleNamespace(id=5, title="Stored Title"))

    assert jp.process_pdf_jd(s, upload("other_name.pdf")) == (5, "Stored Title")
    assert s.added == [] and calls == [] and not s.committed


def test_iss11_each_field_gets_its_own_embedding(monkeypatch, upload):
    calls = []
    _wire(monkeypatch, JDRequirements(
        title="T", required_skills=["Excel"], preferred_skills=["SQL"],
        responsibilities=["Budget"], preferred_education=["MBA"],
        domain=["FinTech"], industries=["Banking"]), calls)
    s = AddSession()
    jp.process_pdf_jd(s, upload("jd.pdf"))
    jd, skill = s.added

    assert calls == [["JD body", "Excel", "Budget", "MBA", "FinTech", "Banking", "Excel", "SQL"]]
    assert [v[0] for v in (jd.embedding, jd.responsibilities_embedding, jd.education_embedding,
                           jd.domain_embedding, jd.industries_embedding,
                           jd.required_skills_embeddings, jd.preferred_skills_embeddings)] == [1, 3, 4, 5, 6, 7, 8]
    assert skill.skill_embedding[0] == 2.0


def test_iss11_empty_fields_are_none_except_not_null_education(monkeypatch, upload):
    _wire(monkeypatch, JDRequirements(title="T", required_skills=["Excel"]))
    s = AddSession()
    jp.process_pdf_jd(s, upload("jd.pdf"))
    jd = s.added[0]
    assert jd.education_embedding == [0.0] * 384
    assert jd.domain_embedding is None and jd.industries_embedding is None
    assert jd.preferred_skills_embeddings is None
    assert jd.responsibilities_embedding is not None  # default responsibility text is embedded


def test_iss12_no_stdout(monkeypatch, upload, capsys):
    _wire(monkeypatch, JDRequirements(title="T", required_skills=["Excel"]))
    jp.process_pdf_jd(AddSession(), upload("jd.pdf"))
    assert capsys.readouterr().out == ""


def test_iss13_all_caches_share_one_default(monkeypatch):
    from app.utils import redis_config
    monkeypatch.delenv("REDIS_URL", raising=False)
    assert redis_config.redis_url() == "redis://localhost:6380"
    monkeypatch.setenv("REDIS_URL", "redis://example:1")
    import app.utils.extract_jd as ej
    assert importlib.reload(ej).REDIS_URL == "redis://example:1"
