"""
Job Description ingestion: parses a JD PDF, embeds everything in ONE Gemini
call, and stores JD + Jd_Skill rows.
"""
"""
Job Description ingestion: parses a JD PDF, embeds everything in ONE Gemini
call (auto-chunked if needed), and stores JD + Jd_Skill rows.
"""
import os
from pathlib import Path

from app.database.jd_models import JD
from app.database.jd_skill_table import Jd_Skill
from app.services.extract_resume import extract_text
from app.embedding.embedding_service import create_embeddings

EMBED_DIM = 768


def extract_jd_skills(description: str, title: str) -> list:
    """Rough heuristic: pull short lines out as 'skills'."""
    skills = [
        line.strip()
        for line in description.split("\n")
        if 15 < len(line.strip()) < 80
    ][:12]
    return skills or [title]


def process_pdf_jd(session, uploaded_file):
    """
    Parse + embed a JD PDF. Returns (jd_id, title).
    Uses ONE embedding call (auto-chunked by embedding_service).
    """
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_pdf_path = temp_dir / uploaded_file.name

    try:
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        description = extract_text(temp_pdf_path)
        if not description or not description.strip():
            raise ValueError("Could not extract text from the JD PDF.")

        title = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        skills_list = extract_jd_skills(description, title)

        # ONE logical call; auto-chunked inside create_embeddings
        payload = [description] + skills_list
        vectors = create_embeddings(payload)
        jd_embedding = vectors[0]
        skill_vectors = vectors[1:]

        dummy_vec = [0.0] * EMBED_DIM

        new_jd = JD(
            title=title,
            description=description,
            required_skills=skills_list,
            preferred_skills=[],
            preferred_education=[],
            responsibilities=["General responsibilities per job description"],
            domain=["General"],
            industries=["Technology"],
            embedding=jd_embedding,
            responsibilities_embedding=jd_embedding,
            education_embedding=dummy_vec,
            domain_embedding=dummy_vec,
            industries_embedding=dummy_vec,
            required_skills_embeddings=dummy_vec,
            preferred_skills_embeddings=dummy_vec,
        )
        session.add(new_jd)
        session.flush()  # get new_jd.id
        jd_id = new_jd.id

        for skill, vec in zip(skills_list, skill_vectors):
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