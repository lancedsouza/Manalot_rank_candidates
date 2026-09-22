"""
Resume ingestion:
  - Parses resume PDF via cache (LLM extraction)
  - Embeds structural texts + all skills in ONE logical call
    (auto-chunked by embedding_service if >100 items)
  - Upserts Candidate + Candidate_Skill rows via raw SQL
  - Links to a JD (Application row) with hybrid score
"""
"""
Resume ingestion:
  - Parses resume PDF via cache (LLM extraction)
  - Embeds structural texts + all skills in ONE logical call
  - Upserts Candidate + Candidate_Skill rows via raw SQL
  - Links to a JD (Application row) with hybrid score
"""
import os
from pathlib import Path

import redis
from sqlalchemy import text

from app.services.extract_resume import extract_text
from app.utils.resume_cache import process_resume, generate_cache_key
from app.embedding.embedding_service import create_embeddings

# ✅ Must match Vector(1024) columns
EMBED_DIM = 1024


# ============================================================
# HELPERS
# ============================================================
def _build_structural_texts(structured_resume, raw_text: str):
    """Return (skills_text, experience_text, education_text)."""
    skills_text = " ".join(structured_resume.skills) if structured_resume.skills else ""

    exp_parts = []
    for exp in structured_resume.experience:
        parts = []
        if exp.title:
            parts.append(f"Title: {exp.title}")
        if exp.company:
            parts.append(f"Company: {exp.company}")
        if exp.responsibilities:
            parts.append(f"Responsibilities: {' '.join(exp.responsibilities)}")
        if parts:
            exp_parts.append("\n".join(parts))
    experience_text = "\n\n".join(exp_parts)

    edu_parts = []
    for edu in structured_resume.education:
        parts = []
        if edu.degree:
            parts.append(f"Degree: {edu.degree}")
        if edu.institution:
            parts.append(f"Institution: {edu.institution}")
        if parts:
            edu_parts.append("\n".join(parts))
    education_text = "\n\n".join(edu_parts)

    return skills_text, experience_text, education_text


def _flush_cache_for_resume(pdf_path: Path) -> None:
    try:
        url = os.getenv("REDIS_URL", "redis://localhost:6380")
        r = redis.Redis.from_url(url, decode_responses=True)
        r.delete(generate_cache_key(pdf_path))
    except Exception:
        pass


# ============================================================
# HYBRID SCORING
# ============================================================
def calculate_candidate_scores_for_jd(session, jd_id: int, cand_id: int) -> dict:
    parent_sql = text("""
        SELECT (1 - (c.embedding <=> j.embedding)) AS parent_similarity
        FROM candidates c CROSS JOIN jds j
        WHERE c.id = :cand_id AND j.id = :jd_id
    """)
    parent_res = session.execute(
        parent_sql, {"cand_id": cand_id, "jd_id": jd_id}
    ).scalar()
    parent_sim = float(parent_res) if parent_res is not None else 0.0

    skill_sql = text("""
        SELECT AVG(sub.similarity) AS avg_top_skill_similarity
        FROM (
            SELECT MAX(1 - (cs.skill_embedding <=> js.skill_embedding)) AS similarity
            FROM jd_skill js CROSS JOIN cand_skill cs
            WHERE js.jd_id = :jd_id AND cs.cand_id = :cand_id
            GROUP BY js.id
        ) sub
    """)
    skill_res = session.execute(
        skill_sql, {"cand_id": cand_id, "jd_id": jd_id}
    ).scalar()
    skill_sim = float(skill_res) if skill_res is not None else 0.0

    hybrid = 0.6 * parent_sim + 0.4 * skill_sim
    return {"hybrid": hybrid, "parent": parent_sim, "skill": skill_sim}


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def process_and_link_resume(
    session,
    uploaded_file,
    jd_id: int,
    force_refresh: bool = False,
) -> tuple:
    """
    Full pipeline: PDF -> extract -> embed -> upsert candidate
                   -> upsert skills -> link to JD.
    Returns (cand_id, name).
    """
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_pdf_path = temp_dir / uploaded_file.name

    try:
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        raw_text = extract_text(temp_pdf_path)
        if not raw_text or not raw_text.strip():
            raise ValueError(f"Could not extract text from {uploaded_file.name}.")

        if force_refresh:
            _flush_cache_for_resume(temp_pdf_path)

        structured_resume = process_resume(temp_pdf_path)
        name = (
            structured_resume.name
            or os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()
        )

        skills_text, experience_text, education_text = _build_structural_texts(
            structured_resume, raw_text
        )

        unique_skills = list({
            s.strip()
            for s in (structured_resume.skills or [])
            if s and s.strip()
        })

        # ========================================================
        # ONE logical call (auto-chunked inside create_embeddings)
        # ========================================================
        payload = [
            raw_text,
            skills_text or " ",
            experience_text or " ",
            education_text or " ",
            *unique_skills,
        ]
        vectors = create_embeddings(payload)

        full_emb       = vectors[0]
        skills_emb     = vectors[1] if skills_text.strip()     else None
        experience_emb = vectors[2] if experience_text.strip() else None
        education_emb  = vectors[3] if education_text.strip()  else None
        skill_vectors  = vectors[4:]

        # ========================================================
        # UPSERT candidate via raw SQL (avoids vector ORM issues)
        # ========================================================
        existing = session.execute(
            text("SELECT id FROM candidates WHERE name = :name"),
            {"name": name},
        ).first()

        if existing:
            cand_id = existing[0]
            session.execute(
                text("""
                    UPDATE candidates
                    SET experience_years = :exp_years,
                        resume_text      = :resume_text,
                        skills_text      = :skills_text,
                        experience_text  = :exp_text,
                        education_text   = :edu_text,
                        embedding        = CAST(:emb AS vector),
                        skills_embedding = CAST(:skill_emb AS vector)
                    WHERE id = :cand_id
                """),
                {
                    "exp_years": structured_resume.experience_years,
                    "resume_text": raw_text,
                    "skills_text": skills_text,
                    "exp_text": experience_text,
                    "edu_text": education_text,
                    "emb": str(full_emb),
                    "skill_emb": str(skills_emb) if skills_emb is not None else None,
                    "cand_id": cand_id,
                },
            )
            session.execute(
                text("DELETE FROM cand_skill WHERE cand_id = :cand_id"),
                {"cand_id": cand_id},
            )
        else:
            res = session.execute(
                text("""
                    INSERT INTO candidates
                        (name, experience_years, resume_text, skills_text,
                         experience_text, education_text,
                         embedding, skills_embedding)
                    VALUES
                        (:name, :exp_years, :resume_text, :skills_text,
                         :exp_text, :edu_text,
                         CAST(:emb AS vector), CAST(:skill_emb AS vector))
                    RETURNING id
                """),
                {
                    "name": name,
                    "exp_years": structured_resume.experience_years,
                    "resume_text": raw_text,
                    "skills_text": skills_text,
                    "exp_text": experience_text,
                    "edu_text": education_text,
                    "emb": str(full_emb),
                    "skill_emb": str(skills_emb) if skills_emb is not None else None,
                },
            )
            cand_id = res.scalar()

        # ========================================================
        # Insert skill embeddings (already computed above)
        # ========================================================
        for skill, vec in zip(unique_skills, skill_vectors):
            session.execute(
                text("""
                    INSERT INTO cand_skill (cand_id, skill, skill_embedding)
                    VALUES (:cand_id, :skill, CAST(:vec AS vector))
                """),
                {"cand_id": cand_id, "skill": skill, "vec": str(vec)},
            )

        # ========================================================
        # Compute hybrid score for this JD
        # ========================================================
        scores = calculate_candidate_scores_for_jd(session, jd_id, cand_id)

        existing_app = session.execute(
            text("SELECT id FROM applications WHERE jd_id = :jd_id AND candidate_id = :cand_id"),
            {"jd_id": jd_id, "cand_id": cand_id},
        ).first()

        if existing_app:
            session.execute(
                text("""
                    UPDATE applications
                    SET hybrid_score = :hybrid,
                        parent_score = :parent,
                        skill_score  = :skill
                    WHERE jd_id = :jd_id AND candidate_id = :cand_id
                """),
                {
                    "hybrid": scores["hybrid"],
                    "parent": scores["parent"],
                    "skill":  scores["skill"],
                    "jd_id":  jd_id,
                    "cand_id": cand_id,
                },
            )
        else:
            session.execute(
                text("""
                    INSERT INTO applications
                        (jd_id, candidate_id, hybrid_score, parent_score, skill_score)
                    VALUES
                        (:jd_id, :cand_id, :hybrid, :parent, :skill)
                """),
                {
                    "jd_id":  jd_id,
                    "cand_id": cand_id,
                    "hybrid": scores["hybrid"],
                    "parent": scores["parent"],
                    "skill":  scores["skill"],
                },
            )

        session.commit()
        return cand_id, name

    except Exception:
        session.rollback()
        raise
    finally:
        if temp_pdf_path.exists():
            temp_pdf_path.unlink()