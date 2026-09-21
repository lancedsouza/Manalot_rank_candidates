from pathlib import Path
import time
import json
from sqlalchemy import text
from google.genai.errors import ClientError

from app.database.jd_models import JD  # Assuming your JD model is defined here or imported correctly
from app.database.jd_skill_table import Jd_Skill
from app.database.db import SessionLocal, engine, Base
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
                wait_time = 35
                print(f"     [Rate Limit Hit] Quota exhausted (429). Backing off for {wait_time}s (Attempt {retry_count}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded for Gemini API due to rate limits.")

session = SessionLocal()

try:
    # Query all job descriptions from the database
    jd_rows = session.query(JD.id, JD.title, JD.required_skills, JD.preferred_skills).all()
    print(f"Found {len(jd_rows)} Job Descriptions in database to check for skill enrichment.\n")

    # Load all unique skills already stored globally in the database upfront (Global Skill Cache)
    existing_skills_db = {
        row.skill: row.skill_embedding 
        for row in session.query(Jd_Skill.skill, Jd_Skill.skill_embedding).distinct(Jd_Skill.skill).all()
    }
    print(f"Loaded {len(existing_skills_db)} unique pre-cached skills from global JD skill DB table.")

    for jd_id, jd_title, req_skills_json, pref_skills_json in jd_rows:
        print(f"\nEvaluating JD ID {jd_id}: {jd_title}")

        # Combine required and preferred skills safely (handling strings or JSON payloads)
        skills_list = []
        
        for raw_skills in [req_skills_json, pref_skills_json]:
            if not raw_skills:
                continue
            if isinstance(raw_skills, str):
                try:
                    parsed = json.loads(raw_skills)
                    if isinstance(parsed, list):
                        skills_list.extend(parsed)
                    elif isinstance(parsed, set):
                        skills_list.extend(list(parsed))
                except json.JSONDecodeError:
                    # Fallback if it's stored as a comma-separated string or raw text snippet
                    skills_list.append(raw_skills)
            elif isinstance(raw_skills, (list, set)):
                skills_list.extend(list(raw_skills))

        if not skills_list:
            print(f"  -> No skills found for JD ID {jd_id}")
            continue

        # 1. Normalize and deduplicate skills while preserving order
        valid_skills = [s.strip() for s in skills_list if s and s.strip()]
        unique_jd_skills = list(dict.fromkeys(valid_skills))

        # 2. Check which skills are already stored for THIS specific JD
        already_stored_rows = session.query(Jd_Skill.skill).filter_by(jd_id=jd_id).all()
        already_stored_skills = {row[0] for row in already_stored_rows}

        if len(already_stored_skills) == len(unique_jd_skills):
            print(f"  -> All {len(unique_jd_skills)} skills already fully enriched for JD ID {jd_id}. Skipping.")
            continue

        # 3. Compute exact difference: skills still needed for this JD
        skills_to_process = [s for s in unique_jd_skills if s not in already_stored_skills]

        skill_rows_data = []
        skills_to_embed = []

        # 4. Check global cache or queue for API embedding
        for skill_name in skills_to_process:
            if skill_name in existing_skills_db:
                # REUSE FROM GLOBAL DB CACHE (0 API Calls!)
                skill_rows_data.append({
                    "jd_id": jd_id,
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
                    # Cache globally for future JDs
                    existing_skills_db[skill_name] = vector
                    skill_rows_data.append({
                        "jd_id": jd_id,
                        "skill": skill_name,
                        "skill_embedding": vector
                    })
                print("     [Throttle] Sleeping for 3 seconds between chunks...")
                time.sleep(3)

        # 6. Bulk insert the remaining skill rows for this JD
        if skill_rows_data:
            session.execute(Jd_Skill.__table__.insert(), skill_rows_data)
            session.commit()
            print(f"  -> Successfully stored skill mappings for JD ID {jd_id}")

        print("  -> Cooldown for 3 seconds before next JD...")
        time.sleep(3)

    print("\n========================================")
    print("Job Description skill enrichment completed successfully!")
    print("========================================")

except Exception as e:
    session.rollback()
    print(f"Error: {e}")
    raise

finally:
    session.close()