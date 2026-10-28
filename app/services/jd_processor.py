# """
# Job Description ingestion: parses a JD PDF, embeds everything in ONE Gemini
# call, and stores JD + Jd_Skill rows.
# """
# """
# Job Description ingestion: parses a JD PDF, embeds everything in ONE Gemini
# call (auto-chunked if needed), and stores JD + Jd_Skill rows.
# """
# """
# Job Description ingestion: parses a JD PDF, embeds everything in ONE
# fastembed-cloud call, and stores JD + Jd_Skill rows.
# """
# import os
# from pathlib import Path

# from app.database.jd_models import JD
# from app.database.jd_skill_table import Jd_Skill
# from app.services.extract_resume import extract_text
# from app.embedding.embedding_service import create_embeddings

# # ✅ Must match Vector(1024) columns in the DB
# EMBED_DIM = 1024


# def extract_jd_skills(description: str, title: str) -> list:
#     """Rough heuristic: pull short lines out as 'skills'."""
#     skills = [
#         line.strip()
#         for line in description.split("\n")
#         if 15 < len(line.strip()) < 80
#     ][:12]
#     return skills or [title]


# def process_pdf_jd(session, uploaded_file):
#     """
#     Parse + embed a JD PDF. Returns (jd_id, title).
#     """
#     temp_dir = Path("temp_uploads")
#     temp_dir.mkdir(exist_ok=True)
#     temp_pdf_path = temp_dir / uploaded_file.name

#     try:
#         with open(temp_pdf_path, "wb") as f:
#             f.write(uploaded_file.getbuffer())

#         description = extract_text(temp_pdf_path)
#         if not description or not description.strip():
#             raise ValueError("Could not extract text from the JD PDF.")

#         title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
#         skills_list = extract_jd_skills(description, title)

#         # ONE batched embedding call (auto-chunked by fastembed-cloud if needed)
#         payload = [description] + skills_list
#         vectors = create_embeddings(payload)
#         jd_embedding = vectors[0]
#         skill_vectors = vectors[1:]

#         # ✅ 1024-dim zeros
#         dummy_vec = [0.0] * EMBED_DIM

#         new_jd = JD(
#             title=title,
#             description=description,
#             required_skills=skills_list,
#             preferred_skills=[],
#             preferred_education=[],
#             responsibilities=["General responsibilities per job description"],
#             domain=["General"],
#             industries=["Technology"],
#             embedding=jd_embedding,
#             responsibilities_embedding=jd_embedding,
#             education_embedding=dummy_vec,
#             domain_embedding=dummy_vec,
#             industries_embedding=dummy_vec,
#             required_skills_embeddings=dummy_vec,
#             preferred_skills_embeddings=dummy_vec,
#         )
#         session.add(new_jd)
#         session.flush()
#         jd_id = new_jd.id

#         for skill, vec in zip(skills_list, skill_vectors):
#             session.add(
#                 Jd_Skill(
#                     jd_id=jd_id,
#                     skill=skill,
#                     skill_embedding=vec,
#                 )
#             )

#         session.commit()
#         return jd_id, title

#     except Exception:
#         session.rollback()
#         raise
#     finally:
#         if temp_pdf_path.exists():
#             temp_pdf_path.unlink()


"""
Job Description ingestion:
  - Extracts JD text from an uploaded PDF
  - Uses the LLM-based extractor (extract_structured_jd) with Redis caching
    — same pattern as resume extraction
  - Embeds the JD description + all required skills in ONE batched call
  - Stores JD + Jd_Skill rows
"""
import logging
import os

from app.database.jd_models import JD
from app.database.jd_skill_table import Jd_Skill
from app.services.extract_resume import extract_text       # PDF → text
from app.utils.extract_jd import extract_structured_jd     # ← the LLM extractor
from app.embedding.embedding_service import create_embeddings
from app.utils.uploads import safe_upload_path

EMBED_DIM = 384

logger = logging.getLogger(__name__)


def process_pdf_jd(session, uploaded_file):
    """
    Parse + embed a JD PDF. Returns (jd_id, title).

    Uses the LLM extractor for skills/responsibilities/education/industries,
    then embeds everything in ONE batched call.
    """
    temp_pdf_path = safe_upload_path(uploaded_file.name)

    try:
        # Write the uploaded PDF to a temp file so extract_text can read it
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 1. PDF → raw text
        raw_text = extract_text(temp_pdf_path)
        if not raw_text or not raw_text.strip():
            raise ValueError("Could not extract text from the JD PDF.")

        # Same JD text already stored -> reuse it instead of a duplicate row (ISS-10)
        existing = (
            session.query(JD.id, JD.title)
            .filter(JD.description == raw_text)
            .first()
        )
        if existing:
            logger.info("JD already embedded as id=%s", existing.id)
            return existing.id, existing.title

        # 2. LLM extraction (Redis-cached inside extract_structured_jd)
        structured_jd = extract_structured_jd(raw_text)

        # 3. Title — prefer the LLM's guess, fall back to the filename
        title = (structured_jd.title or "").strip() or os.path.splitext(
            uploaded_file.name
        )[0].replace("_", " ").title()

        # 4. Read the fields your JDRequirements schema actually defines
        required_skills     = list(structured_jd.required_skills or [])
        preferred_skills    = list(structured_jd.preferred_skills or [])
        responsibilities    = list(structured_jd.responsibilities or [])
        preferred_education = list(structured_jd.preferred_education or [])
        domain              = list(structured_jd.domain or [])
        industries          = list(structured_jd.industries or [])

        # Never store an empty skills list — the matcher needs something to work with
        if not required_skills:
            required_skills = [title]

        logger.debug(
            "JD extracted: title=%r required=%d preferred=%d responsibilities=%d",
            title, len(required_skills), len(preferred_skills), len(responsibilities),
        )

        responsibilities = responsibilities or ["General responsibilities per job description"]

        # 5. Embed description, each structured field and all required skills
        #    in ONE batched call. Empty fields get no embedding (ISS-11).
        field_texts = {
            "responsibilities": " ".join(responsibilities),
            "education": " ".join(preferred_education),
            "domain": " ".join(domain),
            "industries": " ".join(industries),
            "required_skills": " ".join(required_skills),
            "preferred_skills": " ".join(preferred_skills),
        }
        present = [k for k, v in field_texts.items() if v.strip()]
        payload = [raw_text] + required_skills + [field_texts[k] for k in present]
        vectors = create_embeddings(payload)
        jd_embedding = vectors[0]
        n_skills = len(required_skills)
        skill_vectors = vectors[1:1 + n_skills]
        field_vecs = dict(zip(present, vectors[1 + n_skills:], strict=True))

        # education_embedding is NOT NULL in the schema; keep a zero vector when empty
        zero_vec = [0.0] * EMBED_DIM

        new_jd = JD(
            title=title,
            description=raw_text,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            preferred_education=preferred_education,
            responsibilities=responsibilities,
            domain=domain,
            industries=industries,
            embedding=jd_embedding,
            responsibilities_embedding=field_vecs["responsibilities"],
            education_embedding=field_vecs.get("education", zero_vec),
            domain_embedding=field_vecs.get("domain"),
            industries_embedding=field_vecs.get("industries"),
            required_skills_embeddings=field_vecs.get("required_skills"),
            preferred_skills_embeddings=field_vecs.get("preferred_skills"),
        )
        session.add(new_jd)
        session.flush()          # assigns new_jd.id
        jd_id = new_jd.id

        # 6. Persist individual skill embeddings
        for skill, vec in zip(required_skills, skill_vectors, strict=True):
            session.add(
                Jd_Skill(
                    jd_id=jd_id,
                    skill=skill,
                    skill_embedding=vec,
                )
            )

        session.commit()
        return jd_id, title

    except Exception:
        session.rollback()
        raise
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()