

# """Gemini with 2 models  """

# # app/services/resume_extractor.py

# import logging
# import time
# from pathlib import Path

# import pdfplumber
# from pydantic import ValidationError

# from app.models.resume import Resume

# from app.utils.section_extractor import (
#     extract_experience_section,
#     extract_education_section,
#     extract_name_section,
# )

# from app.services.gemini_service import (
#     generate_structured_response,
# )


# # ============================================================
# # LOGGING
# # ============================================================

# logger = logging.getLogger(__name__)


# # ============================================================
# # PDF EXTRACTION
# # ============================================================

# def extract_text(
#     pdf_path: Path,
# ) -> str:

#     logger.info(
#         "Starting PDF text extraction: %s",
#         pdf_path.name,
#     )

#     start = time.perf_counter()

#     if not pdf_path.exists():

#         logger.error(
#             "PDF does not exist: %s",
#             pdf_path,
#         )

#         raise FileNotFoundError(
#             f"PDF not found: {pdf_path}"
#         )


#     extracted_text = []


#     try:

#         with pdfplumber.open(
#             pdf_path
#         ) as pdf:

#             logger.info(
#                 "PDF contains %d pages.",
#                 len(pdf.pages),
#             )

#             for page_number, page in enumerate(
#                 pdf.pages,
#                 start=1,
#             ):

#                 page_start = (
#                     time.perf_counter()
#                 )

#                 page_text = (
#                     page.extract_text()
#                 )

#                 page_elapsed = (
#                     time.perf_counter()
#                     - page_start
#                 )

#                 if page_text:

#                     extracted_text.append(
#                         page_text
#                     )

#                     logger.debug(
#                         "Page %d extracted "
#                         "in %.4fs. Characters: %d",
#                         page_number,
#                         page_elapsed,
#                         len(page_text),
#                     )

#                 else:

#                     logger.warning(
#                         "No text extracted "
#                         "from page %d.",
#                         page_number,
#                     )


#     except Exception:

#         logger.exception(
#             "PDF extraction FAILED."
#         )

#         raise


#     full_text = "\n\n".join(
#         extracted_text
#     )


#     elapsed = (
#         time.perf_counter()
#         - start
#     )


#     logger.info(
#         "PDF extraction completed "
#         "in %.2f seconds.",
#         elapsed,
#     )

#     logger.info(
#         "Full resume text size: "
#         "%d characters.",
#         len(full_text),
#     )


#     return full_text


# # ============================================================
# # GEMINI STRUCTURED EXTRACTION
# # ============================================================

# def parse_resume_to_pydantic(
#     candidate_name: str,
#     experience_text: str,
#     education_text: str,
# ) -> Resume:

#     total_start = (
#         time.perf_counter()
#     )


#     logger.info(
#         "Starting Gemini "
#         "structured resume extraction."
#     )


#     # ========================================================
#     # BUILD PROMPT
#     # ========================================================

#     prompt_start = (
#         time.perf_counter()
#     )


#     prompt = f"""
# You are extracting structured information from a resume.

# CURRENT DATE:
# August 2026

# CANDIDATE NAME:
# {candidate_name}

# EXPERIENCE:
# {experience_text}

# EDUCATION:
# {education_text}


# RULES:

# - Use only information supported by the supplied resume text.

# - Use the supplied candidate name exactly.

# - Extract every professional employment record.

# - - For each employment record extract:
#   company,
#   title,
#   start_date,
#   end_date,
#   responsibilities.

# - For responsibilities:
#   - Extract the candidate's responsibilities, achievements, and work performed
#     under that employment record.
#   - Preserve important business, technical, financial, operational,
#     leadership, and domain-specific details.
#   - Preserve measurable evidence such as percentages, revenue, cost savings,
#     team size, budgets, transaction values, or other quantified results.
#   - Associate each responsibility with the correct employment record.
#   - Do not invent responsibilities that are not supported by the resume.

# - Normalize dates where possible.

# - Treat:
#   Current,
#   Present,
#   Till Date,
#   To Date

#   as August 2026.

# - Calculate total professional experience
#   from employment periods.

# - Do not double-count overlapping employment.

# - Do not estimate experience using title,
#   seniority or age.


# SKILLS:

# - Extract professional skills demonstrated
#   in EXPERIENCE.

# Skills can include:

# - technologies
# - tools
# - software
# - platforms
# - finance skills
# - accounting skills
# - business domains
# - methodologies
# - analytical skills
# - professional processes

# Do NOT include:

# - candidate names
# - company names
# - job titles
# - degrees
# - unsupported capabilities


# EDUCATION:

# - Extract education only from
#   the EDUCATION section.

# - Extract every clearly identifiable
#   education record.

# - Include:
#   degree,
#   institution,
#   start_date,
#   end_date

#   when available.

# - Do not invent missing information.


# Return data matching the Resume schema.
# """


#     prompt_elapsed = (
#         time.perf_counter()
#         - prompt_start
#     )


#     logger.info(
#         "Resume prompt built "
#         "in %.4f seconds.",
#         prompt_elapsed,
#     )

#     logger.info(
#         "Resume prompt size: "
#         "%d characters.",
#         len(prompt),
#     )

#     logger.info(
#         "Experience section size: "
#         "%d characters.",
#         len(experience_text),
#     )

#     logger.info(
#         "Education section size: "
#         "%d characters.",
#         len(education_text),
#     )


#     # ========================================================
#     # GEMINI
#     # ========================================================

#     logger.info(
#         "Sending resume extraction "
#         "request to Gemini..."
#     )


#     gemini_start = (
#         time.perf_counter()
#     )


#     try:

#         response = (
#             generate_structured_response(
#                 prompt=prompt,
#                 schema=Resume,
#             )
#         )


#     except Exception:

#         gemini_elapsed = (
#             time.perf_counter()
#             - gemini_start
#         )

#         logger.exception(
#             "Gemini resume extraction FAILED "
#             "after %.2f seconds.",
#             gemini_elapsed,
#         )

#         raise


#     gemini_elapsed = (
#         time.perf_counter()
#         - gemini_start
#     )


#     logger.info(
#         "Gemini resume extraction "
#         "returned in %.2f seconds.",
#         gemini_elapsed,
#     )


#     # ========================================================
#     # RESPONSE
#     # ========================================================

#     response_text = (
#         response.text
#     )


#     if not response_text:

#         logger.error(
#             "Gemini returned "
#             "an empty response."
#         )

#         raise ValueError(
#             "Gemini returned "
#             "no resume data."
#         )


#     logger.info(
#         "Gemini resume response size: "
#         "%d characters.",
#         len(response_text),
#     )


#     logger.debug(
#         "Gemini resume response preview: %r",
#         response_text[:300],
#     )


#     # ========================================================
#     # PYDANTIC
#     # ========================================================

#     logger.info(
#         "Starting Resume "
#         "Pydantic validation..."
#     )


#     validation_start = (
#         time.perf_counter()
#     )


#     try:

#         resume = (
#             Resume.model_validate_json(
#                 response_text
#             )
#         )


#     except ValidationError:

#         validation_elapsed = (
#             time.perf_counter()
#             - validation_start
#         )

#         logger.exception(
#             "Resume validation FAILED "
#             "after %.4f seconds.",
#             validation_elapsed,
#         )

#         logger.error(
#             "Invalid Gemini response "
#             "starts with: %r",
#             response_text[:500],
#         )

#         raise


#     validation_elapsed = (
#         time.perf_counter()
#         - validation_start
#     )


#     logger.info(
#         "Resume Pydantic validation "
#         "completed in %.4f seconds.",
#         validation_elapsed,
#     )


#     total_elapsed = (
#         time.perf_counter()
#         - total_start
#     )


#     logger.info(
#         "Structured resume extraction "
#         "COMPLETE in %.2f seconds.",
#         total_elapsed,
#     )


#     return resume


# # ============================================================
# # COMPLETE RESUME PIPELINE
# # ============================================================

# def extract_resume_data(
#     pdf_path: Path,
# ) -> Resume:

#     total_start = (
#         time.perf_counter()
#     )


#     logger.info(
#         "=" * 60
#     )

#     logger.info(
#         "Resume pipeline started for: %s",
#         pdf_path.name,
#     )

#     logger.info(
#         "=" * 60
#     )


#     try:

#         # ====================================================
#         # STEP 1 — PDF -> TEXT
#         # ====================================================

#         full_text = extract_text(
#             pdf_path
#         )


#         if not full_text.strip():

#             raise ValueError(
#                 "No text could be "
#                 "extracted from the PDF."
#             )


#         # ====================================================
#         # STEP 2 — NAME
#         # ====================================================

#         logger.info(
#             "Starting candidate "
#             "name extraction..."
#         )


#         start = (
#             time.perf_counter()
#         )


#         name = (
#             extract_name_section(
#                 full_text
#             )
#         )


#         elapsed = (
#             time.perf_counter()
#             - start
#         )


#         logger.info(
#             "Name extraction completed "
#             "in %.4f seconds.",
#             elapsed,
#         )


#         logger.info(
#             "Candidate name detected: %s",
#             name,
#         )


#         # ====================================================
#         # STEP 3 — EXPERIENCE
#         # ====================================================

#         logger.info(
#             "Starting experience "
#             "section extraction..."
#         )


#         start = (
#             time.perf_counter()
#         )


#         experience_section = (
#             extract_experience_section(
#                 full_text
#             )
#         )


#         elapsed = (
#             time.perf_counter()
#             - start
#         )


#         logger.info(
#             "Experience extraction "
#             "completed in %.4f seconds.",
#             elapsed,
#         )


#         logger.info(
#             "Experience section size: "
#             "%d characters.",
#             len(experience_section),
#         )


#         if not (
#             experience_section.strip()
#         ):

#             logger.warning(
#                 "Experience section is empty."
#             )


#         # ====================================================
#         # STEP 4 — EDUCATION
#         # ====================================================

#         logger.info(
#             "Starting education "
#             "section extraction..."
#         )


#         start = (
#             time.perf_counter()
#         )


#         education_section = (
#             extract_education_section(
#                 full_text
#             )
#         )


#         elapsed = (
#             time.perf_counter()
#             - start
#         )


#         logger.info(
#             "Education extraction "
#             "completed in %.4f seconds.",
#             elapsed,
#         )


#         logger.info(
#             "Education section size: "
#             "%d characters.",
#             len(education_section),
#         )


#         if not (
#             education_section.strip()
#         ):

#             logger.warning(
#                 "Education section is empty."
#             )


#         # ====================================================
#         # CONTEXT METRICS
#         # ====================================================

#         full_chars = (
#             len(full_text)
#         )

#         relevant_chars = (
#             len(experience_section)
#             + len(education_section)
#         )


#         removed_chars = max(
#             0,
#             full_chars
#             - relevant_chars,
#         )


#         if full_chars > 0:

#             reduction_percentage = (
#                 removed_chars
#                 / full_chars
#             ) * 100

#         else:

#             reduction_percentage = 0


#         logger.info(
#             "Full resume characters: %d",
#             full_chars,
#         )

#         logger.info(
#             "Relevant context characters: %d",
#             relevant_chars,
#         )

#         logger.info(
#             "Characters removed "
#             "before LLM: %d",
#             removed_chars,
#         )

#         logger.info(
#             "Context reduction: %.1f%%",
#             reduction_percentage,
#         )


#         # ====================================================
#         # STEP 5 — GEMINI
#         # ====================================================

#         logger.info(
#             "Starting Gemini resume parsing..."
#         )


#         resume = (
#             parse_resume_to_pydantic(
#                 candidate_name=name,
#                 experience_text=(
#                     experience_section
#                 ),
#                 education_text=(
#                     education_section
#                 ),
#             )
#         )


#         # ====================================================
#         # NAME EXTRACTOR WINS
#         # ====================================================

#         resume.name = name


#         # ====================================================
#         # COMPLETE
#         # ====================================================

#         total_elapsed = (
#             time.perf_counter()
#             - total_start
#         )


#         logger.info(
#             "=" * 60
#         )

#         logger.info(
#             "RESUME PIPELINE COMPLETE "
#             "in %.2f seconds.",
#             total_elapsed,
#         )

#         logger.info(
#             "=" * 60
#         )


#         return resume


#     except Exception:

#         total_elapsed = (
#             time.perf_counter()
#             - total_start
#         )


#         logger.exception(
#             "RESUME PIPELINE FAILED "
#             "after %.2f seconds.",
#             total_elapsed,
#         )


#         raise

# if __name__ == "__main__":
#         from pathlib import Path
#         pdf_path = Path(
#             "/mnt/c/Users/User/Manlot/Annil Raikundlia - Lance/Medline/Sr.Mgr FP&A/Sent/Manalot_Anup_Dubey.pdf"
#         )
#         print("Starting resume extraction...")
#         resume = extract_resume_data(pdf_path)
#         print("Finished.")
#         print(resume.model_dump())


# # """Extract resume and cache it """

"Code with responsibilities"
# app/services/resume_extractor.py

import logging
import time
from pathlib import Path

import pdfplumber
from pydantic import ValidationError

from app.models.resume import Resume

from app.utils.section_extractor import (
    extract_experience_section,
    extract_education_section,
    extract_name_section,
)

from app.services.gemini_service import (
    generate_structured_response,
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_text(
    pdf_path: Path,
) -> str:

    logger.info(
        "Starting PDF text extraction: %s",
        pdf_path.name,
    )

    start = time.perf_counter()

    if not pdf_path.exists():

        logger.error(
            "PDF does not exist: %s",
            pdf_path,
        )

        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    extracted_text = []

    try:

        with pdfplumber.open(
            pdf_path
        ) as pdf:

            logger.info(
                "PDF contains %d pages.",
                len(pdf.pages),
            )

            for page_number, page in enumerate(
                pdf.pages,
                start=1,
            ):

                page_start = time.perf_counter()

                page_text = page.extract_text()

                page_elapsed = (
                    time.perf_counter()
                    - page_start
                )

                if page_text:

                    extracted_text.append(
                        page_text
                    )

                    logger.debug(
                        "Page %d extracted "
                        "in %.4fs. Characters: %d",
                        page_number,
                        page_elapsed,
                        len(page_text),
                    )

                else:

                    logger.warning(
                        "No text extracted "
                        "from page %d.",
                        page_number,
                    )

    except Exception:

        logger.exception(
            "PDF extraction FAILED."
        )

        raise

    full_text = "\n\n".join(
        extracted_text
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    logger.info(
        "PDF extraction completed "
        "in %.2f seconds.",
        elapsed,
    )

    logger.info(
        "Full resume text size: "
        "%d characters.",
        len(full_text),
    )

    return full_text


# ============================================================
# GEMINI STRUCTURED EXTRACTION
# ============================================================

def parse_resume_to_pydantic(
    candidate_name: str,
    experience_text: str,
    education_text: str,
) -> Resume:

    total_start = time.perf_counter()

    logger.info(
        "Starting Gemini "
        "structured resume extraction."
    )

    # ========================================================
    # BUILD PROMPT
    # ========================================================

    prompt_start = time.perf_counter()

    prompt = f"""
You are extracting structured information from a resume.

CURRENT DATE:
August 2026

CANDIDATE NAME:
{candidate_name}

EXPERIENCE:
{experience_text}

EDUCATION:
{education_text}


RULES:

- Use only information supported by the supplied resume text.

- Use the supplied candidate name exactly.

- Extract every professional employment record.

- For each employment record extract:
  company,
  title,
  start_date,
  end_date,
  responsibilities.

- For responsibilities:
  - Extract the candidate's responsibilities, achievements, and work performed
    under that employment record.
  - Preserve important business, technical, financial, operational,
    leadership, and domain-specific details.
  - Preserve measurable evidence such as percentages, revenue, cost savings,
    team size, budgets, transaction values, or other quantified results.
  - Associate each responsibility with the correct employment record.
  - Do not invent responsibilities that are not supported by the resume.

- Normalize dates where possible.

- Treat:
  Current,
  Present,
  Till Date,
  To Date

  as August 2026.

- Calculate total professional experience
  from employment periods.

- Do not double-count overlapping employment.

- Do not estimate experience using title,
  seniority or age.


SKILLS:

- Extract professional skills demonstrated
  in EXPERIENCE.

Skills can include:

- technologies
- tools
- software
- platforms
- finance skills
- accounting skills
- business domains
- methodologies
- analytical skills
- professional processes

Do NOT include:

- candidate names
- company names
- job titles
- degrees
- unsupported capabilities
SKILLS:

- Extract only skills explicitly stated or clearly demonstrated in the resume.
- Every extracted skill must be supported by text in the EXPERIENCE or PROJECTS section.
- Do not infer skills from job title, company, industry, seniority, or education.
- Do not add common skills that someone in this role would normally have.
- If a skill is not supported by resume evidence, do not include it.

EDUCATION:

- Extract education only from
  the EDUCATION section.

- Extract every clearly identifiable
  education record.

- Include:
  degree,
  institution,
  start_date,
  end_date

  when available.

- Do not invent missing information.


Return data matching the Resume schema.
"""

    prompt_elapsed = (
        time.perf_counter()
        - prompt_start
    )

    logger.info(
        "Resume prompt built "
        "in %.4f seconds.",
        prompt_elapsed,
    )

    logger.info(
        "Resume prompt size: "
        "%d characters.",
        len(prompt),
    )

    logger.info(
        "Experience section size: "
        "%d characters.",
        len(experience_text),
    )

    logger.info(
        "Education section size: "
        "%d characters.",
        len(education_text),
    )

    # ========================================================
    # CHECK SCHEMA
    # ========================================================

    print("\n" + "=" * 70)
    print("EXPERIENCE PYDANTIC SCHEMA")
    print("=" * 70)

    schema = Resume.model_json_schema()

    print(
        schema.get(
            "$defs",
            {},
        ).get(
            "Experience",
            {},
        )
    )

    print("=" * 70)

    # ========================================================
    # GEMINI
    # ========================================================

    logger.info(
        "Sending resume extraction "
        "request to Gemini..."
    )

    gemini_start = time.perf_counter()

    try:

        response = generate_structured_response(
            prompt=prompt,
            schema=Resume,
        )

    except Exception:

        gemini_elapsed = (
            time.perf_counter()
            - gemini_start
        )

        logger.exception(
            "Gemini resume extraction FAILED "
            "after %.2f seconds.",
            gemini_elapsed,
        )

        raise

    gemini_elapsed = (
        time.perf_counter()
        - gemini_start
    )

    logger.info(
        "Gemini resume extraction "
        "returned in %.2f seconds.",
        gemini_elapsed,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    response_text = response.text

    if not response_text:

        logger.error(
            "Gemini returned "
            "an empty response."
        )

        raise ValueError(
            "Gemini returned "
            "no resume data."
        )

    logger.info(
        "Gemini resume response size: "
        "%d characters.",
        len(response_text),
    )

    logger.debug(
        "Gemini resume response preview: %r",
        response_text[:300],
    )

    # ========================================================
    # DEBUG 1 — RAW GEMINI RESPONSE
    # ========================================================

    print("\n" + "=" * 70)
    print("RAW GEMINI RESPONSE")
    print("=" * 70)

    print(response_text)

    print("=" * 70)

    # ========================================================
    # PYDANTIC
    # ========================================================

    logger.info(
        "Starting Resume "
        "Pydantic validation..."
    )

    validation_start = time.perf_counter()

    try:

        resume = Resume.model_validate_json(
            response_text
        )

    except ValidationError:

        validation_elapsed = (
            time.perf_counter()
            - validation_start
        )

        logger.exception(
            "Resume validation FAILED "
            "after %.4f seconds.",
            validation_elapsed,
        )

        logger.error(
            "Invalid Gemini response "
            "starts with: %r",
            response_text[:500],
        )

        raise

    validation_elapsed = (
        time.perf_counter()
        - validation_start
    )

    logger.info(
        "Resume Pydantic validation "
        "completed in %.4f seconds.",
        validation_elapsed,
    )

    # ========================================================
    # DEBUG 2 — VALIDATED PYDANTIC OBJECT
    # ========================================================

    print("\n" + "=" * 70)
    print("VALIDATED RESUME")
    print("=" * 70)

    print(
        resume.model_dump()
    )

    print("=" * 70)

    # ========================================================
    # DEBUG 3 — EXPERIENCE RESPONSIBILITIES ONLY
    # ========================================================

    print("\n" + "=" * 70)
    print("EXPERIENCE RESPONSIBILITIES")
    print("=" * 70)

    for index, experience in enumerate(
        resume.experience,
        start=1,
    ):

        print(
            f"\nExperience {index}"
        )

        print(
            "Company:",
            experience.company,
        )

        print(
            "Title:",
            experience.title,
        )

        print(
            "Start:",
            experience.start_date,
        )

        print(
            "End:",
            experience.end_date,
        )

        print(
            "Responsibilities:"
        )

        if experience.responsibilities:

            for responsibility in (
                experience.responsibilities
            ):

                print(
                    "-",
                    responsibility,
                )

        else:

            print(
                "- NO RESPONSIBILITIES EXTRACTED"
            )

    print("\n" + "=" * 70)

    total_elapsed = (
        time.perf_counter()
        - total_start
    )

    logger.info(
        "Structured resume extraction "
        "COMPLETE in %.2f seconds.",
        total_elapsed,
    )

    return resume


# ============================================================
# COMPLETE RESUME PIPELINE
# ============================================================

def extract_resume_data(
    pdf_path: Path,
) -> Resume:

    total_start = time.perf_counter()

    logger.info(
        "=" * 60
    )

    logger.info(
        "Resume pipeline started for: %s",
        pdf_path.name,
    )

    logger.info(
        "=" * 60
    )

    try:

        # ====================================================
        # STEP 1 — PDF -> TEXT
        # ====================================================

        full_text = extract_text(
            pdf_path
        )

        if not full_text.strip():

            raise ValueError(
                "No text could be "
                "extracted from the PDF."
            )

        # ====================================================
        # STEP 2 — NAME
        # ====================================================

        logger.info(
            "Starting candidate "
            "name extraction..."
        )

        start = time.perf_counter()

        name = extract_name_section(
            full_text
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        logger.info(
            "Name extraction completed "
            "in %.4f seconds.",
            elapsed,
        )

        logger.info(
            "Candidate name detected: %s",
            name,
        )

        # ====================================================
        # STEP 3 — EXPERIENCE
        # ====================================================

        logger.info(
            "Starting experience "
            "section extraction..."
        )

        start = time.perf_counter()

        experience_section = (
            extract_experience_section(
                full_text
            )
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        logger.info(
            "Experience extraction "
            "completed in %.4f seconds.",
            elapsed,
        )

        logger.info(
            "Experience section size: "
            "%d characters.",
            len(experience_section),
        )

        if not experience_section.strip():

            logger.warning(
                "Experience section is empty."
            )

        # ====================================================
        # STEP 4 — EDUCATION
        # ====================================================

        logger.info(
            "Starting education "
            "section extraction..."
        )

        start = time.perf_counter()

        education_section = (
            extract_education_section(
                full_text
            )
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        logger.info(
            "Education extraction "
            "completed in %.4f seconds.",
            elapsed,
        )

        logger.info(
            "Education section size: "
            "%d characters.",
            len(education_section),
        )

        if not education_section.strip():

            logger.warning(
                "Education section is empty."
            )

        # ====================================================
        # CONTEXT METRICS
        # ====================================================

        full_chars = len(
            full_text
        )

        relevant_chars = (
            len(experience_section)
            + len(education_section)
        )

        removed_chars = max(
            0,
            full_chars
            - relevant_chars,
        )

        if full_chars > 0:

            reduction_percentage = (
                removed_chars
                / full_chars
            ) * 100

        else:

            reduction_percentage = 0

        logger.info(
            "Full resume characters: %d",
            full_chars,
        )

        logger.info(
            "Relevant context characters: %d",
            relevant_chars,
        )

        logger.info(
            "Characters removed "
            "before LLM: %d",
            removed_chars,
        )

        logger.info(
            "Context reduction: %.1f%%",
            reduction_percentage,
        )

        # ====================================================
        # STEP 5 — GEMINI
        # ====================================================

        logger.info(
            "Starting Gemini resume parsing..."
        )

        resume = parse_resume_to_pydantic(
            candidate_name=name,
            experience_text=(
                experience_section
            ),
            education_text=(
                education_section
            ),
        )

        # ====================================================
        # NAME EXTRACTOR WINS
        # ====================================================

        resume.name = name

        # ====================================================
        # COMPLETE
        # ====================================================

        total_elapsed = (
            time.perf_counter()
            - total_start
        )

        logger.info(
            "=" * 60
        )

        logger.info(
            "RESUME PIPELINE COMPLETE "
            "in %.2f seconds.",
            total_elapsed,
        )

        logger.info(
            "=" * 60
        )

        return resume

    except Exception:

        total_elapsed = (
            time.perf_counter()
            - total_start
        )

        logger.exception(
            "RESUME PIPELINE FAILED "
            "after %.2f seconds.",
            total_elapsed,
        )

        raise


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    pdf_path = Path(
        "/mnt/c/Users/User/Manlot/"
        "Annil Raikundlia - Lance/"
        "Medline/Sr.Mgr FP&A/Sent/"
        "Manalot_Anup_Dubey.pdf"
    )

    print(
        "Starting resume extraction..."
    )

    resume = extract_resume_data(
        pdf_path
    )

    print(
        "\nFinished."
    )

    print(
        resume.model_dump()
    )