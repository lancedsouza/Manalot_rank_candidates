"""FLOW-02 Ingest resumes — rule-based section helpers (app/utils/section_extractor.py)."""
import pytest

from app.utils import section_extractor as se


@pytest.mark.parametrize("raw,expected", [
    ("  Work Experience:  ", "WORK EXPERIENCE"),
    ("Professional   Experience", "PROFESSIONAL EXPERIENCE"),
    ("Education & Certification", "EDUCATION CERTIFICATION"),
    ("", ""),
])
def test_normalize_header(raw, expected):
    assert se.normalize_header(raw) == expected


def test_clean_name_candidate_strips_contact_details():
    assert se.clean_name_candidate("ANUP DUBEY | +91 98200 12345 | a@b.com") == "ANUP DUBEY"
