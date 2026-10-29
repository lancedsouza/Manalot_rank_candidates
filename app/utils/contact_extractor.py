"""Email and phone from raw resume text, used as candidate identity (ISS-22)."""
import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# A run of digits with optional +, spaces, dots, dashes or brackets between them
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")


def normalise_email(email):
    return email.strip().lower() if email and email.strip() else None


def normalise_phone(phone):
    """Last 10 digits, so +91 98200 12345 and 09820012345 compare equal."""
    digits = re.sub(r"\D", "", phone or "")
    return digits[-10:] if len(digits) >= 10 else None


def extract_contacts(text: str) -> tuple:
    """Return (email, phone) normalised, either may be None. First match wins."""
    text = text or ""
    m = EMAIL_RE.search(text)
    email = normalise_email(m.group(0)) if m else None
    for m in PHONE_RE.finditer(text):
        groups = re.findall(r"\d+", m.group(0))
        if all(re.fullmatch(r"(19|20)\d\d", g) for g in groups):
            continue  # date ranges such as "2019 - 2021 2022"
        # 10-15 digits is a phone; longer runs are IDs or account numbers
        if 10 <= len("".join(groups)) <= 15:
            return email, normalise_phone(m.group(0))
    return email, None
