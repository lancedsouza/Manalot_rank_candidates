"""ISS-27: Groq call uses low reasoning effort and a token cap so long resumes return JSON."""
from types import SimpleNamespace

from app.models.resume import Resume
from app.services import gemini_service as gs


def test_groq_call_sets_reasoning_and_cap(monkeypatch):
    seen = {}

    class FakeGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def create(self, **kw):
            seen.update(kw)
            msg = SimpleNamespace(content='{"name": "Ada"}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)])

    monkeypatch.setattr(gs, "Groq", FakeGroq)
    out = gs.generate_structured_response("prompt", Resume)

    assert out.parsed.name == "Ada" and out.text == '{"name": "Ada"}'
    assert seen["reasoning_effort"] == "low"
    assert seen["max_completion_tokens"] == 4096
    assert seen["response_format"] == {"type": "json_object"}
