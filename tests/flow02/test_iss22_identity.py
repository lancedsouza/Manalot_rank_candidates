"""ISS-22: candidates are identified by email + phone, then email; never by name."""
import pytest

from app.utils.contact_extractor import extract_contacts, normalise_phone
from tests.characterisation.test_ingest_resumes_pg import _jd


@pytest.mark.parametrize("text, expected", [
    ("Ada Lovelace | ADA@Example.com | +91 98200 12345", ("ada@example.com", "9820012345")),
    ("Phone: (098) 2001-2345\nada.l+cv@mail.co.uk", ("ada.l+cv@mail.co.uk", "9820012345")),
    ("Worked 2019 - 2021 2022 at Acme, no contacts", (None, None)),
    ("Account 1234567890123456789 only", (None, None)),
    ("", (None, None)),
])
def test_extract_contacts(text, expected):
    assert extract_contacts(text) == expected


def test_phone_formats_compare_equal():
    assert normalise_phone("+91 98200 12345") == normalise_phone("098200-12345") == "9820012345"
    assert normalise_phone("12345") is None



def _ingest(rp, session, upload, monkeypatch, resume, jd_id, raw, fname="cv.pdf"):
    monkeypatch.setattr(rp, "extract_text", lambda p: raw)
    return rp.process_and_link_resume(session, upload(fname), jd_id, structured_resume=resume)[0]


def _count(session):
    from sqlalchemy import text
    return session.execute(text("SELECT count(*) FROM candidates")).scalar()


@pytest.mark.pg
@pytest.mark.skipif("not __import__('os').getenv('TEST_DATABASE_URL')")
def test_same_name_different_contacts_creates_two(pg_session, wired, upload, monkeypatch):
    rp, resume = wired
    jd = _jd(pg_session)
    a = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@one.com 9820012345")
    b = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@two.com 9820054321")
    assert a != b and _count(pg_session) == 2


@pytest.mark.pg
@pytest.mark.skipif("not __import__('os').getenv('TEST_DATABASE_URL')")
def test_email_alone_matches_when_phone_changed(pg_session, wired, upload, monkeypatch):
    from sqlalchemy import text
    rp, resume = wired
    jd = _jd(pg_session)
    a = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@one.com +91 98200 12345")
    b = _ingest(rp, pg_session, upload, monkeypatch, resume.model_copy(update={"name": "Ada King"}), jd,
                "ADA@one.com 98200 99999")
    assert a == b and _count(pg_session) == 1
    row = pg_session.execute(text("SELECT name, email, phone FROM candidates")).one()
    assert tuple(row) == ("Ada King", "ada@one.com", "9820099999")


@pytest.mark.pg
@pytest.mark.skipif("not __import__('os').getenv('TEST_DATABASE_URL')")
def test_email_and_phone_match_preferred_over_email_only(pg_session, wired, upload, monkeypatch):
    rp, resume = wired
    jd = _jd(pg_session)
    first = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@one.com 9820012345")
    # A second row sharing the email can exist only from legacy data; create it directly
    from sqlalchemy import text
    pg_session.execute(text("UPDATE candidates SET email = 'ada@one.com', phone = '1111111111'"))
    second = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@two.com 9820012345")
    pg_session.execute(text("UPDATE candidates SET email = 'ada@one.com' WHERE id = :i"), {"i": second})
    pg_session.commit()
    again = _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "ada@one.com 9820012345")
    assert again == second != first


@pytest.mark.pg
@pytest.mark.skipif("not __import__('os').getenv('TEST_DATABASE_URL')")
def test_no_email_never_matches(pg_session, wired, upload, monkeypatch):
    rp, resume = wired
    jd = _jd(pg_session)
    _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "no contacts here")
    _ingest(rp, pg_session, upload, monkeypatch, resume, jd, "no contacts here")
    assert _count(pg_session) == 2


@pytest.mark.pg
@pytest.mark.skipif("not __import__('os').getenv('TEST_DATABASE_URL')")
def test_schema_upgrade_adds_columns_to_old_table(pg_session):
    from sqlalchemy import text
    from app.database.schema_upgrade import upgrade_schema
    pg_session.execute(text("ALTER TABLE candidates DROP COLUMN email, DROP COLUMN phone"))
    pg_session.commit()
    eng = pg_session.get_bind()
    upgrade_schema(eng)
    upgrade_schema(eng)  # idempotent
    cols = pg_session.execute(text("SELECT column_name FROM information_schema.columns "
                                   "WHERE table_name = 'candidates' AND table_schema = current_schema()")).scalars().all()
    assert {"email", "phone"} <= set(cols)
