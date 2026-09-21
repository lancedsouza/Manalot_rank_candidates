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

                page_start = (
                    time.perf_counter()
                )

                page_text = (
                    page.extract_text()
                )

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


if __name__ == "__main__":
    pdf_path = Path(
        "/mnt/c/Users/User/Manlot/Annil Raikundlia - Lance/Medline/Sr.Mgr FP&A/Sent/Manalot_Anup_Dubey.pdf"
    )
    
    try:
        # Extract full text once
        text = extract_text(pdf_path)
        
        # Pass the full text once to each section extractor
        name_section = extract_name_section(text)
        experience_section = extract_experience_section(text)
        education_section = extract_education_section(text)  # Fixed function call
        
        print(f"Name: {name_section}")
        print(f"Experience Section: {experience_section}")
        print(f"Len Education: {len(education_section)}")
        print(f"Education Section: {education_section}")
        
    except ValidationError as e:
        logger.error("Pydantic validation failed: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred during processing.")