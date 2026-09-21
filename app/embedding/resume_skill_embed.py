# from pathlib import Path
# import time
# from sqlalchemy import text

# from app.database.candidate_skill_table import Candidate_Skill
# from app.database.db import SessionLocal, engine, Base
# from app.database.resume_models import Candidate
# from app.embedding.embedding_service import create_embeddings
# from app.utils.resume_cache import process_resume

# # Create missing tables only. DO NOT drop existing tables.
# Base.metadata.create_all(bind=engine)

# pdf_path = (
#     Path(__file__).resolve().parents[2]
#     / "app"
#     / "pdf"
# )

# def chunk_list(lst, chunk_size=50):
#     """Yield successive chunks to stay safely under batch limits."""
#     for i in range(0, len(lst), chunk_size):
#         yield lst[i:i + chunk_size]

# session = SessionLocal()

# try:
#     for file in pdf_path.glob("*.pdf"):
#         print(f"\nProcessing skills for: {file.name}")

#         # --------------------------------------------
#         # Get structured resume data
#         # --------------------------------------------
#         resume_data = process_resume(file)

#         if not resume_data.skills:
#             print("No skills found")
#             continue

#         # --------------------------------------------
#         # Find candidate already stored in DB
#         # --------------------------------------------
#         candidate = (
#             session.query(Candidate)
#             .filter(Candidate.name == resume_data.name)
#             .first()
#         )

#         if not candidate:
#             print(f"Candidate not found in DB: {resume_data.name}")
#             continue

#         # Check if skills are already enriched for this candidate to prevent duplicates
#         existing_count = session.query(Candidate_Skill).filter_by(cand_id=candidate.id).count()
#         if existing_count > 0:
#             print(f"Skills already enriched for {candidate.name}. Skipping.")
#             continue

#         # --------------------------------------------
#         # Deduplicate skills while preserving order
#         # --------------------------------------------
#         valid_skills = [s.strip() for s in resume_data.skills if s and s.strip()]
#         unique_skills = list(dict.fromkeys(valid_skills))

#         skill_rows_data = []
#         skills_to_embed = []

#         # --------------------------------------------
#         # Check Database Cache first (Save API Quota!)
#         # --------------------------------------------
#         for skill_name in unique_skills:
#             cached_skill = session.query(Candidate_Skill.skill_embedding).filter_by(skill=skill_name).first()
#             if cached_skill:
#                 skill_rows_data.append({
#                     "cand_id": candidate.id,
#                     "skill": skill_name,
#                     "skill_embedding": cached_skill.skill_embedding
#                 })
#             else:
#                 skills_to_embed.append(skill_name)

#         # --------------------------------------------
#         # Batch embed uncached skills safely
#         # --------------------------------------------
#         if skills_to_embed:
#             print(f"Embedding {len(skills_to_embed)} new skills (Reused {len(unique_skills) - len(skills_to_embed)} from DB cache)...")
#             for chunk in chunk_list(skills_to_embed, chunk_size=50):
#                 vectors = create_embeddings(chunk)
#                 for skill_name, vector in zip(chunk, vectors):
#                     skill_rows_data.append({
#                         "cand_id": candidate.id,
#                         "skill": skill_name,
#                         "skill_embedding": vector
#                     })
#                 time.sleep(1)  # Throttle between chunks

#         # --------------------------------------------
#         # Store skill rows via bulk insert
#         # --------------------------------------------
#         if skill_rows_data:
#             session.execute(Candidate_Skill.__table__.insert(), skill_rows_data)
#             session.commit()
#             print(f"Stored {len(skill_rows_data)} unique skills for {candidate.name}")

#         time.sleep(2)  # Cooldown between resume files

# except Exception as e:
#     session.rollback()
#     print(f"Error: {e}")
#     raise

# finally:
#     session.close()

# 
from pathlib import Path
import time
from sqlalchemy import text
from google.genai.errors import ClientError

from app.database.candidate_skill_table import Candidate_Skill
from app.database.db import SessionLocal, engine, Base
from app.database.resume_models import Candidate
from app.embedding.embedding_service import create_embeddings

# Create missing tables only. DO NOT drop existing tables.
Base.metadata.create_all(bind=engine)

def chunk_list(lst, chunk_size=10):
    """Yield smaller chunks to stay well within free-tier rate limits."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def embed_with_rate_limit_retry(chunk):
    """Safely calls create_embeddings, automatically handling 429 Quota Exhaustion."""
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            return create_embeddings(chunk)
        except ClientError as e:
            if e.code == 429:
                retry_count += 1
                wait_time = 35  # Default fallback wait time in seconds
                print(f"     [Rate Limit Hit] Quota exhausted (429). Backing off for {wait_time}s (Attempt {retry_count}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded for Gemini API due to rate limits.")

session = SessionLocal()

try:
    # Query only the scalar/JSON columns needed
    candidate_rows = session.query(Candidate.id, Candidate.name, Candidate.skills).all()
    print(f"Found {len(candidate_rows)} candidates in database to check for skill enrichment.\n")

    # Load all unique skills already stored globally in the database upfront (Global Skill Cache)
    existing_skills_db = {
        row.skill: row.skill_embedding 
        for row in session.query(Candidate_Skill.skill, Candidate_Skill.skill_embedding).distinct(Candidate_Skill.skill).all()
    }
    print(f"Loaded {len(existing_skills_db)} unique pre-cached skills from global DB table.")

    for cand_id, cand_name, cand_skills in candidate_rows:
        print(f"\nEvaluating candidate ID {cand_id}: {cand_name}")

        if not cand_skills:
            print(f"  -> No skills found in database record for {cand_name}")
            continue

        # 1. Normalize and deduplicate total candidate skills from the array
        valid_skills = [s.strip() for s in cand_skills if s and s.strip()]
        unique_candidate_skills = list(dict.fromkeys(valid_skills))

        # 2. Fetch the exact set of skill strings ALREADY stored in DB for THIS specific candidate
        already_stored_rows = session.query(Candidate_Skill.skill).filter_by(cand_id=cand_id).all()
        already_stored_skills = {row[0] for row in already_stored_rows}

        if len(already_stored_skills) == len(unique_candidate_skills):
            print(f"  -> All {len(unique_candidate_skills)} skills already fully enriched for {cand_name}. Skipping.")
            continue

        if already_stored_skills:
            print(f"  -> Partial resume detected! Found {len(already_stored_skills)}/{len(unique_candidate_skills)} skills already in DB. Resuming remaining...")

        # 3. Compute the exact difference: skills that still need processing for this candidate
        skills_to_process = [s for s in unique_candidate_skills if s not in already_stored_skills]

        skill_rows_data = []
        skills_to_embed = []

        # 4. Check global cache or queue for API embedding
        for skill_name in skills_to_process:
            if skill_name in existing_skills_db:
                # REUSE FROM GLOBAL DB CACHE (0 API Calls!)
                skill_rows_data.append({
                    "cand_id": cand_id,
                    "skill": skill_name,
                    "skill_embedding": existing_skills_db[skill_name]
                })
            else:
                skills_to_embed.append(skill_name)

        # 5. Batch embed ONLY missing unique skills with automatic retry handling
        if skills_to_embed:
            print(f"  -> Embedding {len(skills_to_embed)} new unique skills (Reused {len(skills_to_process) - len(skills_to_embed)} from cache)...")
            for chunk in chunk_list(skills_to_embed, chunk_size=10):
                vectors = embed_with_rate_limit_retry(chunk)
                for skill_name, vector in zip(chunk, vectors):
                    # Cache globally for future candidates
                    existing_skills_db[skill_name] = vector
                    skill_rows_data.append({
                        "cand_id": cand_id,
                        "skill": skill_name,
                        "skill_embedding": vector
                    })
                print("     [Throttle] Sleeping for 3 seconds between chunks...")
                time.sleep(3)  # Gentle pause between chunks

        # 6. Bulk insert the remaining skill rows for this candidate
        if skill_rows_data:
            session.execute(Candidate_Skill.__table__.insert(), skill_rows_data)
            session.commit()
            print(f"  -> Successfully stored skill mappings for {cand_name}")

        print("  -> Cooldown for 5 seconds before next candidate...")
        time.sleep(5)

    print("\n========================================")
    print("Candidate skill enrichment completed successfully!")
    print("========================================")

except Exception as e:
    session.rollback()
    print(f"Error: {e}")
    raise

finally:
    session.close()