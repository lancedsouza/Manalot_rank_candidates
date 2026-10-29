"""FLOW-02 Ingest resumes — process_and_link_resume and structural texts."""
import pytest

from app.models.resume import Education, Experience, Resume
from app.services import resume_processor as rp


def test_structural_texts():
    r = Resume(
        skills=["Python", "SQL"],
        experience=[Experience(title="FP&A Lead", company="Acme", responsibilities=["Budget", "Forecast"]),
                    Experience()],
        education=[Education(degree="MBA", institution="IIM"), Education(institution="Only Inst")],
    )
    skills, exp, edu = rp._build_structural_texts(r)
    assert skills == "Python SQL"
    assert exp == "Title: FP&A Lead\nCompany: Acme\nResponsibilities: Budget Forecast"
    assert edu == "Degree: MBA\nInstitution: IIM\n\nInstitution: Only Inst"


def test_structural_texts_empty_resume():
    assert rp._build_structural_texts(Resume()) == ("", "", "")


class RecordingSession:
    def __init__(self, existing_candidate=None):
        self.sql = []
        self.existing_candidate = existing_candidate
        self.committed = self.rolled_back = False

    def execute(self, stmt, params=None):
        q = " ".join(str(stmt).split())
        self.sql.append((q, params))
        session = self

        class R:
            def first(self_inner):
                if q.startswith("SELECT id FROM candidates"):
                    return (session.existing_candidate,) if session.existing_candidate else None
                return None

            def scalar(self_inner):
                return 42

        return R()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@pytest.fixture
def wired(monkeypatch, fake_vectors):
    monkeypatch.setattr(rp, "extract_text", lambda p: "resume text")
    monkeypatch.setattr(rp, "process_resume",
                        lambda p: Resume(name=None, skills=["SQL", " SQL ", "", "Python"]))
    monkeypatch.setattr(rp, "create_embeddings", fake_vectors)
    monkeypatch.setattr(rp, "calculate_candidate_scores_for_jd",
                        lambda s, j, c: {"hybrid": 0.5, "parent": 0.4, "skill": 0.3,
                                         "coverage": 0.0, "matched_skills": 0, "total_jd_skills": 0})


def test_new_candidate_inserted_name_from_filename(wired, upload, tmp_path):
    s = RecordingSession()
    cand_id, name = rp.process_and_link_resume(s, upload("anup_dubey.pdf"), jd_id=7)

    assert (cand_id, name) == (42, "Anup Dubey")
    stmts = [q for q, _ in s.sql]
    assert any(q.startswith("INSERT INTO candidates") for q in stmts)
    skills = sorted(p["skill"] for q, p in s.sql if q.startswith("INSERT INTO cand_skill"))
    assert skills == ["Python", "SQL"]  # stripped + de-duplicated
    assert any(q.startswith("INSERT INTO applications") for q in stmts)
    assert s.committed and not (tmp_path / "temp_uploads" / "anup_dubey.pdf").exists()


def test_existing_email_updates_and_replaces_skills(wired, upload, monkeypatch):
    # ISS-22 (owner-approved change): identity is email (+ phone), not name
    monkeypatch.setattr(rp, "extract_text", lambda p: "resume text ada@example.com")
    s = RecordingSession(existing_candidate=9)
    rp.process_and_link_resume(s, upload("x.pdf"), jd_id=7)
    stmts = [q for q, _ in s.sql]
    assert any(q.startswith("UPDATE candidates") for q in stmts)
    assert "DELETE FROM cand_skill WHERE cand_id = :cand_id" in stmts


def test_empty_pdf_text_raises_and_rolls_back(monkeypatch, upload):
    monkeypatch.setattr(rp, "extract_text", lambda p: "  ")
    s = RecordingSession()
    with pytest.raises(ValueError, match="Could not extract text from x.pdf."):
        rp.process_and_link_resume(s, upload("x.pdf"), jd_id=1)
    assert s.rolled_back and not s.committed
