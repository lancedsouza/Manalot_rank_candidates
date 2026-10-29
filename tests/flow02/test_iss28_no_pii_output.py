"""ISS-28: resume extraction writes no candidate data to stdout or above DEBUG."""
import logging

import pytest
from pydantic import ValidationError

from app.models.resume import Experience, Resume
from app.services import extract_resume as er

PII = "Ada Lovelace"
SECRET = "Cut costs at Acme by 40%"


class _Resp:
    text = Resume(name=PII, skills=["SQL"],
                  experience=[Experience(company="Acme", responsibilities=[SECRET])]).model_dump_json()


def test_parse_prints_nothing_and_logs_no_content_above_debug(monkeypatch, capsys, caplog):
    monkeypatch.setattr(er, "generate_structured_response", lambda prompt, schema: _Resp)
    with caplog.at_level(logging.INFO, logger=er.__name__):
        resume = er.parse_resume_to_pydantic(PII, "EXP", "EDU")

    assert resume.experience[0].responsibilities == [SECRET]
    assert capsys.readouterr().out == ""
    logged = " ".join(r.getMessage() for r in caplog.records)
    assert SECRET not in logged and PII not in logged


def test_invalid_response_content_only_at_debug(monkeypatch, caplog):
    class Bad:
        text = '{"name": "Ada Lovelace", "skills": 5}'
    monkeypatch.setattr(er, "generate_structured_response", lambda prompt, schema: Bad)
    with caplog.at_level(logging.INFO, logger=er.__name__):
        with pytest.raises(ValidationError):
            er.parse_resume_to_pydantic(PII, "EXP", "EDU")
    assert PII not in " ".join(r.getMessage() for r in caplog.records)
