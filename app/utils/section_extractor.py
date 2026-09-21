import re


# ============================================================
# SECTION HEADERS
# ============================================================

SUMMARY_HEADERS = [
    "SUMMARY",
    "PROFILE",
    "PROFESSIONAL SUMMARY",
    "CAREER SUMMARY",
    "EXECUTIVE SUMMARY",
    "PROFESSIONAL PROFILE",
    "CAREER PROFILE",
]


EXPERIENCE_HEADERS = [
    "WORK EXPERIENCE",
    "PROFESSIONAL EXPERIENCE",
    "EMPLOYMENT HISTORY",
    "CAREER HISTORY",
    "EXPERIENCE",
    "CORPORATE EXPERIENCE",
    "WORK HISTORY",
    "PROFESSIONAL HISTORY",
    "CAREER EXPERIENCE",
    "EMPLOYMENT EXPERIENCE",
]


EDUCATION_HEADERS = [
    "EDUCATION",
    "ACADEMIC BACKGROUND",
    "ACADEMIC QUALIFICATIONS",
    "EDUCATIONAL BACKGROUND",
    "EDUCATIONAL QUALIFICATIONS",
    "ACADEMIC HISTORY",
    "EDUCATIONAL HISTORY",
    "QUALIFICATIONS",
    "ACADEMIC RECORD",
    "ACADEMIC ACHIEVEMENTS",
    "EDUCATION & CERTIFICATION",
    "EDUCATION & CERTIFICATIONS",
    "EDUCATION AND CERTIFICATION",
    "EDUCATION AND CERTIFICATIONS",
    "ACADEMIC ACHIVEMENTS "
]


SKILLS_HEADERS = [
    "SKILLS",
    "PROFESSIONAL SKILLS",
    "TECHNICAL SKILLS",
    "CORE SKILLS",
    "KEY SKILLS",
    "TECHNOLOGIES",
    "TECHNICAL PROFICIENCIES",
    "CORE COMPETENCIES",
    "COMPETENCIES",
    "AREAS OF EXPERTISE",
    "KEY COMPETENCIES",
]


OTHER_HEADERS = [
    
    "CERTIFICATIONS",
    "CERTIFICATION",
    "ACHIEVEMENTS",
    "INTERESTS",
    "LANGUAGES",
    "PUBLICATIONS",
    "AWARDS",
    "HONORS",
    "REFERENCES",
    "PERSONAL DETAILS",
    "PERSONAL INFORMATION",
    "CONTACT",
    "CONTACT DETAILS",
    "ADDITIONAL INFORMATION",
]


ALL_HEADERS = (
    SUMMARY_HEADERS
    + EXPERIENCE_HEADERS
    + EDUCATION_HEADERS
    + SKILLS_HEADERS
    + OTHER_HEADERS
)


# ============================================================
# NORMALIZE HEADER
# ============================================================

def normalize_header(text: str) -> str:
    """
    Normalize a possible resume section header.

    Examples:

        "  Work Experience:  "
            -> "WORK EXPERIENCE"

        "Professional   Experience"
            -> "PROFESSIONAL EXPERIENCE"

        "Education & Certification"
            -> "EDUCATION CERTIFICATION"
    """

    if not text:
        return ""

    text = text.strip().upper()

    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# CREATE HEADER SET
# ============================================================

def create_header_set(headers):
    """
    Convert header names into their normalized forms.
    """

    return {
        normalize_header(header)
        for header in headers
        if normalize_header(header)
    }


# ============================================================
# GENERATE NORMALIZED HEADER SETS
# ============================================================

ALL_HEADER_SET = create_header_set(ALL_HEADERS)


# ============================================================
# CHECK WHETHER LINE IS A HEADER
# ============================================================

def is_header(line: str, headers) -> bool:
    """
    Return True when the line matches one of the known headers.
    """

    normalized = normalize_header(line)

    if not normalized:
        return False

    return normalized in create_header_set(headers)


# ============================================================
# GENERIC SECTION EXTRACTION
# ============================================================

def extract_section(
    text: str,
    target_headers: list,
    all_headers: list = ALL_HEADERS,
) -> str:
    """
    Extract one section from resume text.

    Starts collecting text immediately after a target header
    and stops when another known section header is reached.
    """

    if not text:
        return ""

    lines = text.splitlines()

    target_set = create_header_set(target_headers)
    all_set = create_header_set(all_headers)

    start = None

    for i, line in enumerate(lines):

        clean = normalize_header(line)

        if not clean:
            continue

        # ----------------------------------------------------
        # Find beginning of target section
        # ----------------------------------------------------

        if start is None:

            if clean in target_set:

                start = i + 1

                print(
                    f"Found section header: "
                    f"{repr(line.strip())} "
                    f"at line {i}"
                )

                continue

        # ----------------------------------------------------
        # Find next section header
        # ----------------------------------------------------

        else:

            if clean in all_set:

                end = i

                print(
                    f"Section ended at header: "
                    f"{repr(line.strip())} "
                    f"at line {i}"
                )

                return "\n".join(
                    lines[start:end]
                ).strip()

    # Target section continued until EOF
    if start is not None:

        return "\n".join(
            lines[start:]
        ).strip()

    return ""


# ============================================================
# DATE DETECTION
# ============================================================

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)


DATE_PATTERN = re.compile(
    rf"""
    (?:
        {MONTH_PATTERN}
        [\s\-/']*
        (?:19|20)?\d{{2}}
    )
    |
    (?:
        (?:19|20)\d{{2}}
        \s*
        (?:-|–|—|to)
        \s*
        (?:
            (?:19|20)\d{{2}}
            |
            Present
            |
            Current
            |
            Till\s+Date
        )
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def contains_date_pattern(line: str) -> bool:
    """
    Detect whether a resume line contains a likely employment date.
    """

    if not line:
        return False

    return bool(
        DATE_PATTERN.search(line)
    )


# ============================================================
# EXPERIENCE FALLBACK
# ============================================================

def extract_experience_by_date_pattern(text: str) -> str:
    """
    Fallback experience extraction.

    Used when a reliable experience header cannot be found.

    Looks for the first region containing employment-like date
    patterns and captures the surrounding resume content.

    This is intentionally heuristic. The LLM performs the final
    structured extraction.
    """

    if not text:
        return ""

    lines = text.splitlines()

    date_indexes = []

    for i, line in enumerate(lines):

        if contains_date_pattern(line):
            date_indexes.append(i)

    if not date_indexes:
        return ""

    # First likely employment date
    first_date_index = date_indexes[0]

    # Start a few lines before it so that company/title information
    # immediately preceding the date is not lost.
    start = max(
        0,
        first_date_index - 4
    )

    end = len(lines)

    # Stop at a strong non-experience section header.
    stop_headers = (
        EDUCATION_HEADERS
        + SKILLS_HEADERS
        + OTHER_HEADERS
    )

    stop_set = create_header_set(
        stop_headers
    )

    for i in range(
        first_date_index + 1,
        len(lines)
    ):

        normalized = normalize_header(
            lines[i]
        )

        if normalized in stop_set:

            end = i
            break

    return "\n".join(
        lines[start:end]
    ).strip()


# ============================================================
# EXPERIENCE SECTION
# ============================================================

def extract_experience_section(text: str) -> str:
    """
    Extract professional experience.

    First attempts normal section-header extraction.

    If the extracted section is missing or suspiciously small,
    use the date-pattern fallback.
    """

    section = extract_section(
        text,
        EXPERIENCE_HEADERS,
        ALL_HEADERS,
    )

    # A very short section is probably a bad extraction.
    if len(section.strip()) >= 200:
        return section

    print(
        "Experience section weak → "
        "trying date pattern fallback"
    )

    fallback = (
        extract_experience_by_date_pattern(
            text
        )
    )

    # Prefer fallback only when it actually found useful text.
    if len(fallback.strip()) > len(section.strip()):
        return fallback

    return section


# ============================================================
# EDUCATION SECTION
# ============================================================

def extract_education_section(text: str) -> str:
    """
    Extract the education section.
    """

    return extract_section(
        text,
        EDUCATION_HEADERS,
        ALL_HEADERS,
    )


# ============================================================
# SUMMARY SECTION
# ============================================================

def extract_summary_section(text: str) -> str:
    """
    Extract summary/profile section.
    """

    return extract_section(
        text,
        SUMMARY_HEADERS,
        ALL_HEADERS,
    )


# ============================================================
# SKILLS SECTION
# ============================================================

def extract_skills_section(text: str) -> str:
    """
    Extract explicitly labelled skills section.

    Your current pipeline does not depend on this because
    skills are inferred by the LLM from experience.
    """

    return extract_section(
        text,
        SKILLS_HEADERS,
        ALL_HEADERS,
    )


# ============================================================
# NAME CLEANING
# ============================================================

def clean_name_candidate(line: str) -> str:
    """
    Clean a possible candidate-name line.
    """

    if not line:
        return ""

    line = line.strip()

    # Remove obvious phone numbers from same line.
    line = re.sub(
        r"\+?\d[\d\s\-()]{7,}",
        "",
        line
    )

    # Remove email if present on same line.
    line = re.sub(
        r"\S+@\S+",
        "",
        line
    )

    # Collapse spaces.
    line = re.sub(
        r"\s+",
        " ",
        line
    )

    return line.strip(
        " |,-:"
    )


# ============================================================
# NAME EXTRACTION
# ============================================================

def extract_name_section(text: str) -> str:
    """
    First-pass candidate name extraction.

    Searches near the beginning of the resume.

    Ignores:
    - section headers
    - email addresses
    - phone/contact lines
    - URLs

    Supports names such as:

        ANUP DUBEY
        Iqbal Singh Sandhu
        DHAVAL KADAKIA
        RUPALI M. BODKE
    """

    if not text:
        return ""

    lines = text.splitlines()

    # Look near the top of the resume.
    for raw_line in lines[:20]:

        clean = clean_name_candidate(
            raw_line
        )

        if not clean:
            continue

        normalized = normalize_header(
            clean
        )

        # ----------------------------------------------------
        # Ignore known section headers
        # ----------------------------------------------------

        if normalized in ALL_HEADER_SET:
            continue

        # ----------------------------------------------------
        # Ignore email
        # ----------------------------------------------------

        if "@" in raw_line:
            continue

        # ----------------------------------------------------
        # Ignore URLs
        # ----------------------------------------------------

        lower = raw_line.lower()

        if (
            "http://" in lower
            or "https://" in lower
            or "www." in lower
            or "linkedin.com" in lower
        ):
            continue

        # ----------------------------------------------------
        # Ignore lines still containing long numbers
        # ----------------------------------------------------

        if re.search(
            r"\d{5,}",
            clean
        ):
            continue

        # ----------------------------------------------------
        # Ignore very long lines
        # ----------------------------------------------------

        if len(clean) > 60:
            continue

        # ----------------------------------------------------
        # Candidate-name pattern
        #
        # Supports:
        #
        # Dhaval Kadakia
        # Manish Thakur
        # RUPALI M. BODKE
        # Shrikant C. Phutane
        # ----------------------------------------------------

        name_pattern = (
            r"[A-Za-z]+"
            r"(?:"
            r"[\s\-']+"
            r"(?:[A-Za-z]+|[A-Za-z]\.)"
            r"){1,5}"
        )

        if re.fullmatch(
            name_pattern,
            clean
        ):
            return clean.strip()

    return ""