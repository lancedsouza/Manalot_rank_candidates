from pathlib import Path

from sqlalchemy import text

from app.database.jd_models import JD
from app.database.db import SessionLocal, engine, Base

from app.utils.extract_jd_section import extract_structured_jd
from app.utils.extract_jd import extract_pdf_text

from app.embedding.embedding_service import create_embedding


# ============================================================
# ENABLE PGVECTOR
# ============================================================

with engine.begin() as connection:
    connection.execute(
        text("CREATE EXTENSION IF NOT EXISTS vector")
    )


# ============================================================
# CREATE TABLES
# ============================================================

Base.metadata.create_all(engine)


# ============================================================
# JD DIRECTORY
# ============================================================

jd_path = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "jd_data"
)


# ============================================================
# PROCESS EACH JD PDF
# ============================================================

for file in jd_path.glob("*.pdf"):

    print(f"\nProcessing JD: {file.name}")

    # ========================================================
    # EXTRACT JD
    # ========================================================

    raw_text = extract_pdf_text(file)

    structured_jd = extract_structured_jd(
        raw_text
    )

    print(
        "JD Title:",
        structured_jd.title
    )


    # ========================================================
    # FULL JD EMBEDDING
    # ========================================================

    full_embedding = (
        create_embedding(raw_text)
        if raw_text.strip()
        else None
    )


    # ========================================================
    # COMBINED REQUIRED SKILLS EMBEDDING
    # ========================================================

    required_skills_text = " ".join(
        structured_jd.required_skills
    )

    required_skills_embeddings = (
        create_embedding(required_skills_text)
        if required_skills_text.strip()
        else None
    )


    # ========================================================
    # INDIVIDUAL REQUIRED SKILL EMBEDDINGS
    # ========================================================

    ind_required_skill_embeddings = []

    for skill in structured_jd.required_skills:

        skill = skill.strip()

        if not skill:
            continue

        print(
            f"Embedding required skill: {skill}"
        )

        skill_embedding = create_embedding(
            skill
        )

        ind_required_skill_embeddings.append(
            {
                "skill": skill,
                "embedding": skill_embedding,
            }
        )


    # ========================================================
    # COMBINED PREFERRED SKILLS EMBEDDING
    # ========================================================

    preferred_skills_text = " ".join(
        structured_jd.preferred_skills
    )

    preferred_skills_embeddings = (
        create_embedding(preferred_skills_text)
        if preferred_skills_text.strip()
        else None
    )


    # ========================================================
    # INDIVIDUAL PREFERRED SKILL EMBEDDINGS
    # ========================================================

    ind_preferred_skill_embeddings = []

    for skill in structured_jd.preferred_skills:

        skill = skill.strip()

        if not skill:
            continue

        print(
            f"Embedding preferred skill: {skill}"
        )

        skill_embedding = create_embedding(
            skill
        )

        ind_preferred_skill_embeddings.append(
            {
                "skill": skill,
                "embedding": skill_embedding,
            }
        )


    # ========================================================
    # RESPONSIBILITIES
    # ========================================================

    responsibilities_text = " ".join(
        structured_jd.responsibilities
    )

    responsibilities_embedding = (
        create_embedding(responsibilities_text)
        if responsibilities_text.strip()
        else None
    )


    # ========================================================
    # EDUCATION
    # ========================================================

    education_text = " ".join(
        structured_jd.preferred_education
    )

    education_embedding = (
        create_embedding(education_text)
        if education_text.strip()
        else None
    )


    # ========================================================
    # DOMAIN
    # ========================================================

    domain_text = " ".join(
        structured_jd.domain
    )

    domain_embedding = (
        create_embedding(domain_text)
        if domain_text.strip()
        else None
    )


    # ========================================================
    # INDUSTRIES
    # ========================================================

    industries_text = " ".join(
        structured_jd.industries
    )

    industries_embedding = (
        create_embedding(industries_text)
        if industries_text.strip()
        else None
    )


    # ========================================================
    # DEBUG
    # ========================================================

    print("\n--- JD EMBEDDING DEBUG ---")

    print(
        "Full JD:",
        len(full_embedding)
        if full_embedding
        else None
    )

    print(
        "Required Skills Combined:",
        len(required_skills_embeddings)
        if required_skills_embeddings
        else None
    )

    print(
        "Individual Required Skills:",
        len(ind_required_skill_embeddings)
    )

    print(
        "Preferred Skills Combined:",
        len(preferred_skills_embeddings)
        if preferred_skills_embeddings
        else None
    )

    print(
        "Individual Preferred Skills:",
        len(ind_preferred_skill_embeddings)
    )

    print(
        "Responsibilities:",
        len(responsibilities_embedding)
        if responsibilities_embedding
        else None
    )

    print(
        "Education:",
        len(education_embedding)
        if education_embedding
        else None
    )

    print(
        "Domain:",
        len(domain_embedding)
        if domain_embedding
        else None
    )

    print(
        "Industries:",
        len(industries_embedding)
        if industries_embedding
        else None
    )


    # ========================================================
    # DATABASE INSERT
    # ========================================================

    session = SessionLocal()

    try:

        jd = JD(

            title=structured_jd.title,

            description=raw_text,

            # -----------------------------------------------
            # STRUCTURED DATA
            # -----------------------------------------------

            required_skills=(
                structured_jd.required_skills
            ),

            preferred_skills=(
                structured_jd.preferred_skills
            ),

            minimum_experience=(
                structured_jd.minimum_experience
            ),

            maximum_experience=(
                structured_jd.maximum_experience
            ),

            preferred_education=(
                structured_jd.preferred_education
            ),

            responsibilities=(
                structured_jd.responsibilities
            ),

            domain=structured_jd.domain,

            industries=structured_jd.industries,


            # -----------------------------------------------
            # COMBINED EMBEDDINGS
            # -----------------------------------------------

            embedding=full_embedding,

            required_skills_embeddings=(
                required_skills_embeddings
            ),

            preferred_skills_embeddings=(
                preferred_skills_embeddings
            ),

            responsibilities_embedding=(
                responsibilities_embedding
            ),

            education_embedding=(
                education_embedding
            ),

            domain_embedding=(
                domain_embedding
            ),

            industries_embedding=(
                industries_embedding
            ),


            # -----------------------------------------------
            # INDIVIDUAL SKILL EMBEDDINGS
            # -----------------------------------------------

            ind_required_skill_embeddings=(
                ind_required_skill_embeddings
            ),

            ind_preferred_skill_embeddings=(
                ind_preferred_skill_embeddings
            ),
        )


        session.add(jd)

        session.commit()

        session.refresh(jd)

        print(
            f"\nJD inserted successfully."
            f" ID: {jd.id}"
        )


    except Exception as e:

        session.rollback()

        print(
            f"\nFailed to insert "
            f"{file.name}: {e}"
        )

        raise


    finally:

        session.close()

"""Code"""
